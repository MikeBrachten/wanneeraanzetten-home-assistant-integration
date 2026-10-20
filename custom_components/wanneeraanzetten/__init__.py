"""Wanneer Aanzetten electricity prices and appliance recommendations."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ACCESS_TOKEN, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import CannotConnect, InvalidAuth, WanneerAanzettenApi
from .coordinator import LOGGER, WanneerAanzettenCoordinator

PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR]


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
