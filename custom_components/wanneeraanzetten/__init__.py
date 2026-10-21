"""Wanneer Aanzetten electricity prices and appliance recommendations."""

import logging
from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ACCESS_TOKEN, Platform
from homeassistant.core import CoreState, EVENT_HOMEASSISTANT_STARTED, HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import CannotConnect, InvalidAuth, WanneerAanzettenApi
from .const import DOMAIN
from .coordinator import LOGGER, NAME, WanneerAanzettenCoordinator

PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR]
_LOGGER = logging.getLogger(__name__)
_CARD_URL = f"/{DOMAIN}/wanneeraanzetten-price-card.js"
_CARD_VERSION = "0.2.0"
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def _async_register_card_resource(hass: HomeAssistant) -> None:
    """Make the bundled branded Lovelace card available after frontend startup."""
    url = f"{_CARD_URL}?v={_CARD_VERSION}"
    lovelace = hass.data.get("lovelace")
    resources = getattr(lovelace, "resources", None) if lovelace else None
    if resources is None and isinstance(lovelace, dict):
        resources = lovelace.get("resources")
    if resources is None or not hasattr(resources, "async_create_item"):
        add_extra_js_url(hass, url)
        return

    # Load the existing collection before writing; this prevents replacing the
    # user's resource list when Home Assistant has deferred its storage load.
    await resources.async_get_info()
    matches = [item for item in resources.async_items() if item.get("url", "").split("?", 1)[0] == _CARD_URL]
    if matches:
        item = matches[0]
        if item.get("url") != url:
            await resources.async_update_item(item["id"], {"res_type": "module", "url": url})
        return
    await resources.async_create_item({"res_type": "module", "url": url})


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Serve and register the Lovelace price graph bundled with the HACS integration."""
    frontend_path = Path(__file__).parent / "frontend"
    await hass.http.async_register_static_paths([
        StaticPathConfig(f"/{DOMAIN}", str(frontend_path), True)
    ])

    async def register(_event=None) -> None:
        try:
            await _async_register_card_resource(hass)
        except Exception:
            # A custom dashboard card is an optional enhancement; sensor setup
            # must stay available even if a user's dashboard is YAML-managed.
            _LOGGER.exception("Unable to register the %s dashboard card", NAME)

    if hass.state is CoreState.running:
        await register()
    else:
        hass.bus.async_listen_once(
            EVENT_HOMEASSISTANT_STARTED,
            lambda event: hass.async_create_task(register(event)),
        )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Validate the connection before adding entities."""
    coordinator = WanneerAanzettenCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Apply updated country settings."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload without revoking credentials during restarts or reloads."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Revoke this installation's token when the user removes the integration."""
    try:
        await WanneerAanzettenApi(
            async_get_clientsession(hass), entry.data[CONF_ACCESS_TOKEN]
        ).async_revoke()
    except InvalidAuth:
        pass
    except CannotConnect:
        LOGGER.warning("Could not revoke the account link; revoke it through the account API")
