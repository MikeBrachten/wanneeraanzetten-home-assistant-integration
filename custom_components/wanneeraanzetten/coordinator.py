"""One shared update per account, regardless of the number of devices."""

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ACCESS_TOKEN
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import CannotConnect, InvalidAuth, WanneerAanzettenApi
from .const import CONF_COUNTRY, CONF_RESOLUTION, NAME, RESOLUTION_ACCOUNT

LOGGER = logging.getLogger(__name__)


class WanneerAanzettenCoordinator(DataUpdateCoordinator[dict]):
    """Refresh once a minute and request reauthentication for revoked tokens."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            LOGGER,
            name=NAME,
            config_entry=entry,
            update_interval=timedelta(minutes=1),
        )
        self.api = WanneerAanzettenApi(async_get_clientsession(hass), entry.data[CONF_ACCESS_TOKEN])
        self.country = entry.options.get(CONF_COUNTRY, entry.data[CONF_COUNTRY])
        self.price_resolution = entry.options.get(CONF_RESOLUTION, RESOLUTION_ACCOUNT)
        self.account_id = entry.unique_id

    async def _async_update_data(self) -> dict:
        try:
            resolution = (
                None if self.price_resolution == RESOLUTION_ACCOUNT else self.price_resolution
            )
            result = await self.api.async_state(self.country, resolution)
            if result["user"]["id"] != self.account_id:
                raise ConfigEntryAuthFailed("The linked account has changed")
            return result
        except InvalidAuth as err:
            raise ConfigEntryAuthFailed("Link your account again") from err
        except CannotConnect as err:
            raise UpdateFailed(str(err)) from err
