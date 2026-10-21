"""Wanneer Aanzetten electricity prices and appliance recommendations."""

import asyncio
import logging
from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ACCESS_TOKEN, Platform
from homeassistant.core import EVENT_HOMEASSISTANT_STARTED, CoreState, HomeAssistant
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


async def _async_register_card_resource(hass: HomeAssistant) -> bool:
    """Register the card in Lovelace storage, or use the YAML-mode fallback."""
    url = f"{_CARD_URL}?v={_CARD_VERSION}"
    lovelace = hass.data.get("lovelace")
    if lovelace is None:
        return False
    resource_mode = (
        lovelace.get("resource_mode")
        if isinstance(lovelace, dict)
        else getattr(lovelace, "resource_mode", None)
    )
    if resource_mode == "yaml":
        add_extra_js_url(hass, url)
        _LOGGER.info(
            "Lovelace resources are YAML-managed; the Wanneer Aanzetten card "
            "script is loaded globally and cannot appear in the Resources list"
        )
        return True
    resources = getattr(lovelace, "resources", None) if lovelace else None
    if resources is None and isinstance(lovelace, dict):
        resources = lovelace.get("resources")
    if resources is None or not hasattr(resources, "async_create_item"):
        return False

    # Load the existing collection before writing; this prevents replacing the
    # user's resource list when Home Assistant has deferred its storage load.
    await resources.async_get_info()
    matches = [
        item
        for item in resources.async_items()
        if item.get("url", "").split("?", 1)[0] == _CARD_URL
    ]
    if matches:
        item = matches[0]
        if item.get("url") != url:
            await resources.async_update_item(item["id"], {"res_type": "module", "url": url})
        return True
    await resources.async_create_item({"res_type": "module", "url": url})
    return True


async def _async_setup_frontend(hass: HomeAssistant) -> None:
    """Serve and auto-load the dashboard card once the integration is configured."""
    setup_key = f"{DOMAIN}_frontend_setup"
    if hass.data.get(setup_key):
        return

    frontend_path = Path(__file__).parent / "frontend"
    await hass.http.async_register_static_paths(
        [StaticPathConfig(f"/{DOMAIN}", str(frontend_path), True)]
    )
    hass.data[setup_key] = True

    async def register(_event=None) -> None:
        last_error = None
        for attempt in range(5):
            try:
                if await _async_register_card_resource(hass):
                    return
            except Exception as err:  # Storage may still be initializing.
                last_error = err
            if attempt < 4:
                await asyncio.sleep(1)

        # Keep the card usable while making the missing Resources entry visible
        # in logs. This should only be reached if Lovelace storage never became
        # writable; the integration itself remains available.
        add_extra_js_url(hass, f"{_CARD_URL}?v={_CARD_VERSION}")
        if last_error:
            _LOGGER.warning(
                "Unable to add the %s dashboard card to Lovelace Resources after retries: %s",
                NAME,
                last_error,
            )
        else:
            _LOGGER.warning(
                "Lovelace storage resources did not become available; the %s card "
                "script was loaded globally but is not listed in Resources",
                NAME,
            )

    if hass.state is CoreState.running:
        hass.async_create_task(register())
    else:
        hass.bus.async_listen_once(
            EVENT_HOMEASSISTANT_STARTED,
            lambda event: hass.async_create_task(register(event)),
        )


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Support YAML setup while config-entry setup calls this too."""
    await _async_setup_frontend(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Validate the connection before adding entities."""
    await _async_setup_frontend(hass)
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
