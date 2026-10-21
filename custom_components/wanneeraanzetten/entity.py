"""Common account device information."""

from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, NAME, SETTINGS_URL
from .coordinator import WanneerAanzettenCoordinator


class WanneerAanzettenEntity(CoordinatorEntity[WanneerAanzettenCoordinator]):
    """An entity associated with the linked account."""

    _attr_has_entity_name = True

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.account_id)},
            name=NAME,
            manufacturer=NAME,
            entry_type=DeviceEntryType.SERVICE,
            configuration_url=SETTINGS_URL,
        )
