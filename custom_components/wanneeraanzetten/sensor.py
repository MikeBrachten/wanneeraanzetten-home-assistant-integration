"""Current wholesale electricity price, excluding taxes and supplier markup."""

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import WanneerAanzettenEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities(
        [
            SpotPriceSensor(entry.runtime_data),
            HouseholdPriceEstimateSensor(entry.runtime_data),
        ]
    )


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
        tariff = self.coordinator.data.get("tariffPreferences") or {}
        prices = self.coordinator.data.get("prices", [])
        return {
            "country": self.coordinator.country,
            "source": price["source"],
            "includes_tax": False,
            "includes_supplier_markup": False,
            "period_start": price["start"],
            "period_end": price["end"],
            "prices": [
                {
                    "start": item["start"],
                    "end": item["end"],
                    "spot": item["value"],
                    "estimated_all_in": _all_in(item["value"], tariff, self.coordinator.country),
                }
                for item in prices
            ],
            "tariff_configured": _tariff_complete(tariff, self.coordinator.country),
            "tariff_settings_url": SETTINGS_URL,
            "unavailable_days": self.coordinator.data.get("unavailableDays", []),
        }


SETTINGS_URL = "https://wanneeraanzetten.nl/?view=settings"


def _tariff_complete(tariff: dict, country: str) -> bool:
    return country == "NL" and all(
        isinstance(tariff.get(key), (int, float)) and not isinstance(tariff.get(key), bool)
        for key in ("inkoop", "eb", "btw")
    )


def _all_in(spot: float, tariff: dict, country: str) -> float | None:
    if not _tariff_complete(tariff, country):
        return None
    return round((spot + tariff["inkoop"] + tariff["eb"]) * (1 + tariff["btw"] / 100), 6)


class HouseholdPriceEstimateSensor(WanneerAanzettenEntity, SensorEntity):
    """Estimated marginal household price using the linked account tariff."""

    _attr_translation_key = "household_price_estimate"
    _attr_native_unit_of_measurement = "EUR/kWh"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 5
    _attr_icon = "mdi:receipt-text-outline"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.account_id}_household_price_estimate"

    @property
    def available(self) -> bool:
        return super().available and self.native_value is not None

    @property
    def native_value(self) -> float | None:
        price = self.coordinator.data["price"]
        if not price["available"]:
            return None
        return _all_in(
            price["value"],
            self.coordinator.data.get("tariffPreferences") or {},
            self.coordinator.country,
        )

    @property
    def extra_state_attributes(self) -> dict:
        tariff = self.coordinator.data.get("tariffPreferences") or {}
        return {
            "country": self.coordinator.country,
            "supplier": tariff.get("supplier"),
            "calculation": "(spot price + supplier markup + energy tax) × (1 + VAT)",
            "fixed_fees_included": False,
            "estimated": True,
            "tariff_configured": _tariff_complete(tariff, self.coordinator.country),
            "tariff_settings_url": SETTINGS_URL,
        }
