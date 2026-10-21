"""Account setup and real Home Assistant entity lifecycle tests."""

from copy import deepcopy
from unittest.mock import patch

import pytest
from homeassistant import config_entries
from homeassistant.const import CONF_ACCESS_TOKEN, CONF_EMAIL, CONF_PASSWORD
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.wanneeraanzetten.api import CannotConnect, InvalidAuth
from custom_components.wanneeraanzetten.const import CONF_COUNTRY, DOMAIN

LINK = {"token": "wa_ha_test", "user": {"id": "usr_1", "email": "ha@example.nl"}}
DATA = {CONF_ACCESS_TOKEN: LINK["token"], CONF_EMAIL: "ha@example.nl", CONF_COUNTRY: "NL"}
DEVICE = {
    "id": "dev_1",
    "name": "Wasmachine",
    "icon": "mdi:washing-machine",
    "available": True,
    "recommendedNow": True,
    "durationMinutes": 60,
    "bestStart": "2026-10-20T10:00:00Z",
    "bestEnd": "2026-10-20T11:00:00Z",
    "averageSpotPrice": -0.02,
}
STATE = {
    "user": LINK["user"],
    "country": "NL",
    "updatedAt": "2026-10-20T10:00:00Z",
    "price": {
        "available": True,
        "value": -0.02,
        "source": "entsoe",
        "start": "2026-10-20T10:00:00Z",
        "end": "2026-10-20T11:00:00Z",
    },
    "tariffPreferences": {
        "country": "NL", "supplier": "custom", "inkoop": 0.02, "eb": 0.09161, "btw": 21
    },
    "prices": [
        {"start": "2026-10-20T10:00:00Z", "end": "2026-10-20T11:00:00Z", "value": -0.02}
    ],
    "devices": [DEVICE],
}
INPUT = {CONF_EMAIL: "ha@example.nl", CONF_PASSWORD: "a password", CONF_COUNTRY: "NL"}


@pytest.fixture
def mock_api():
    with patch(
        "custom_components.wanneeraanzetten.coordinator.WanneerAanzettenApi", autospec=True
    ) as api:
        api.return_value.async_state.return_value = deepcopy(STATE)
        yield api.return_value


async def setup_entry(hass):
    entry = MockConfigEntry(domain=DOMAIN, unique_id="usr_1", data=DATA)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_account_link(hass):
    with (
        patch("custom_components.wanneeraanzetten.config_flow.async_link", return_value=LINK),
        patch("custom_components.wanneeraanzetten.async_setup_entry", return_value=True),
    ):
        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
        assert result["type"] == FlowResultType.FORM
        result = await hass.config_entries.flow.async_configure(result["flow_id"], INPUT)
        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["data"] == DATA
        assert CONF_PASSWORD not in result["data"]
        await hass.async_block_till_done()


@pytest.mark.parametrize(
    ("exception", "error"), [(InvalidAuth, "invalid_auth"), (CannotConnect, "cannot_connect")]
)
async def test_account_link_errors(hass, exception, error):
    with patch("custom_components.wanneeraanzetten.config_flow.async_link", side_effect=exception):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}, data=INPUT
        )
        assert result["errors"] == {"base": error}


async def test_two_factor_retry_and_recovery(hass):
    with (
        patch(
            "custom_components.wanneeraanzetten.config_flow.async_link",
            return_value={"pending_token": "pending"},
        ),
        patch(
            "custom_components.wanneeraanzetten.config_flow.async_complete_two_factor",
            side_effect=[InvalidAuth, LINK],
        ) as complete,
        patch("custom_components.wanneeraanzetten.async_setup_entry", return_value=True),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}, data=INPUT
        )
        assert result["step_id"] == "two_factor"
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"code": "wrong", "recovery": False}
        )
        assert result["errors"] == {"base": "invalid_auth"}
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"code": "recovery", "recovery": True}
        )
        assert result["type"] == FlowResultType.CREATE_ENTRY
        complete.assert_awaited_with("pending", "recovery", True)
        await hass.async_block_till_done()


async def test_duplicate_account_revokes_unused_token(hass):
    MockConfigEntry(domain=DOMAIN, unique_id="usr_1", data=DATA).add_to_hass(hass)
    with (
        patch("custom_components.wanneeraanzetten.config_flow.async_link", return_value=LINK),
        patch(
            "custom_components.wanneeraanzetten.config_flow.WanneerAanzettenApi.async_revoke"
        ) as revoke,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}, data=INPUT
        )
        assert result["reason"] == "already_configured"
        revoke.assert_awaited_once()


async def test_entities_and_discovery(hass, mock_api):
    entry = await setup_entry(hass)
    sensors = hass.states.async_all("sensor")
    binaries = hass.states.async_all("binary_sensor")
    assert len(sensors) == 2 and len(binaries) == 1
    spot = next(sensor for sensor in sensors if sensor.attributes.get("includes_tax") is False)
    household = next(sensor for sensor in sensors if sensor.attributes.get("estimated") is True)
    assert spot.state == "-0.02"
    assert spot.attributes["unit_of_measurement"] == "EUR/kWh"
    assert spot.attributes["prices"][0]["estimated_all_in"] == pytest.approx(0.110848)
    assert spot.attributes["tariff_settings_url"].endswith("?view=settings")
    assert household.state == "0.110848"
    assert household.attributes["fixed_fees_included"] is False
    assert binaries[0].state == "on"

    updated = deepcopy(STATE)
    updated["devices"][0]["recommendedNow"] = False
    updated["devices"].append({**DEVICE, "id": "dev_2", "name": "Vaatwasser"})
    entry.runtime_data.async_set_updated_data(updated)
    await hass.async_block_till_done()
    assert hass.states.get(binaries[0].entity_id).state == "off"
    assert len(hass.states.async_all("binary_sensor")) == 2

    updated["devices"] = []
    updated["price"]["available"] = False
    updated["price"]["value"] = None
    entry.runtime_data.async_set_updated_data(updated)
    await hass.async_block_till_done()
    assert hass.states.get(binaries[0].entity_id).state == "unavailable"
    assert all(hass.states.get(sensor.entity_id).state == "unavailable" for sensor in sensors)
    assert await hass.config_entries.async_unload(entry.entry_id)


async def test_refresh_auth_error_starts_reauth(hass, mock_api):
    entry = await setup_entry(hass)
    mock_api.async_state.side_effect = InvalidAuth
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()
    assert all(state.state == "unavailable" for state in hass.states.async_all("binary_sensor"))
    flows = hass.config_entries.flow.async_progress()
    assert any(flow["context"]["source"] == config_entries.SOURCE_REAUTH for flow in flows)


async def test_transient_failure_marks_unavailable_and_recovers(hass, mock_api):
    entry = await setup_entry(hass)
    mock_api.async_state.side_effect = CannotConnect
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()
    assert all(sensor.state == "unavailable" for sensor in hass.states.async_all("sensor"))
    mock_api.async_state.side_effect = None
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()
    assert any(sensor.state == "-0.02" for sensor in hass.states.async_all("sensor"))


async def test_reauthentication_replaces_token(hass, mock_api):
    entry = await setup_entry(hass)
    with (
        patch(
            "custom_components.wanneeraanzetten.config_flow.async_link",
            return_value={**LINK, "token": "replacement"},
        ),
        patch(
            "custom_components.wanneeraanzetten.config_flow.WanneerAanzettenApi.async_revoke"
        ) as revoke,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "reauth", "entry_id": entry.entry_id}, data=entry.data
        )
        result = await hass.config_entries.flow.async_configure(result["flow_id"], INPUT)
        assert result["reason"] == "reauth_successful"
        assert entry.data[CONF_ACCESS_TOKEN] == "replacement"
        revoke.assert_awaited_once()
        await hass.async_block_till_done()


async def test_wrong_reauth_account_is_rejected(hass, mock_api):
    entry = await setup_entry(hass)
    with (
        patch(
            "custom_components.wanneeraanzetten.config_flow.async_link",
            return_value={**LINK, "user": {"id": "other", "email": "other@example.nl"}},
        ),
        patch(
            "custom_components.wanneeraanzetten.config_flow.WanneerAanzettenApi.async_revoke"
        ) as revoke,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "reauth", "entry_id": entry.entry_id}, data=entry.data
        )
        result = await hass.config_entries.flow.async_configure(result["flow_id"], INPUT)
        assert result["reason"] == "wrong_account"
        assert entry.data == DATA
        revoke.assert_awaited_once()


async def test_removal_revokes_token(hass, mock_api):
    entry = await setup_entry(hass)
    with patch("custom_components.wanneeraanzetten.WanneerAanzettenApi.async_revoke") as revoke:
        await hass.config_entries.async_remove(entry.entry_id)
        await hass.async_block_till_done()
        revoke.assert_awaited_once()


async def test_options_change_country(hass, mock_api):
    entry = await setup_entry(hass)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_COUNTRY: "BE"}
    )
    assert result["type"] == FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    assert entry.runtime_data.country == "BE"
