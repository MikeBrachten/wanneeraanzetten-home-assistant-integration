"""Advisory on/off sensors for every device saved to the linked account."""

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import BASE_URL, DOMAIN, NAME
from .entity import WanneerAanzettenEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = entry.runtime_data
    known: set[str] = set()

    @callback
    def discover_devices() -> None:
        new_devices = [
            device for device in coordinator.data["devices"] if device["id"] not in known
        ]
        known.update(device["id"] for device in new_devices)
        async_add_entities([RecommendedNowSensor(coordinator, device) for device in new_devices])

    discover_devices()
    entry.async_on_unload(coordinator.async_add_listener(discover_devices))


class RecommendedNowSensor(WanneerAanzettenEntity, BinarySensorEntity):
    """On means this device's cheapest available start is now."""

    _attr_translation_key = "recommended_now"

    def __init__(self, coordinator, device: dict) -> None:
        super().__init__(coordinator)
        self.device_id = device["id"]
        self.initial_name = device["name"]
        self._attr_unique_id = f"{coordinator.account_id}_{self.device_id}_recommended_now"

    @property
    def device(self) -> dict:
        return next(
            (item for item in self.coordinator.data["devices"] if item["id"] == self.device_id), {}
        )

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, f"{self.coordinator.account_id}_{self.device_id}")},
            name=self.device.get("name", self.initial_name),
            manufacturer=NAME,
            via_device=(DOMAIN, self.coordinator.account_id),
            configuration_url=BASE_URL,
        )

    @property
    def icon(self) -> str:
        return self.device.get("icon", "mdi:power-plug")

    @property
    def available(self) -> bool:
        return super().available and self.device.get("available", False)

    @property
    def is_on(self) -> bool | None:
        return self.device.get("recommendedNow")

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "best_start": self.device.get("bestStart"),
            "best_end": self.device.get("bestEnd"),
            "duration_minutes": self.device.get("durationMinutes"),
            "average_spot_price": self.device.get("averageSpotPrice"),
        }
