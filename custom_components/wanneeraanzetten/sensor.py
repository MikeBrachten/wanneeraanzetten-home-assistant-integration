"""Current wholesale electricity price, excluding taxes and supplier markup."""

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import WanneerAanzettenEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([SpotPriceSensor(entry.runtime_data)])


class SpotPriceSensor(WanneerAanzettenEntity, SensorEntity):
    """A negative price is valid; an absent price is unavailable, never zero."""

    _attr_translation_key = "spot_price"
    _attr_native_unit_of_measurement = "EUR/kWh"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 5
    _attr_icon = "mdi:currency-eur"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.account_id}_spot_price"

    @property
    def available(self) -> bool:
        return super().available and self.coordinator.data["price"]["available"]

    @property
    def native_value(self) -> float | None:
        return self.coordinator.data["price"]["value"]

    @property
    def extra_state_attributes(self) -> dict:
        price = self.coordinator.data["price"]
        return {
            "country": self.coordinator.country,
            "source": price["source"],
            "includes_tax": False,
            "includes_supplier_markup": False,
            "period_start": price["start"],
            "period_end": price["end"],
        }
