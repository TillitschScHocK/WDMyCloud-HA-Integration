"""Sensor platform for WD MyCloud EX2 Ultra integration."""
from __future__ import annotations

import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, SENSORS, CONF_HOST
from . import WDEx2UltraCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors from config entry."""
    coordinator: WDEx2UltraCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        WDEx2UltraSensor(coordinator, entry, sensor)
        for sensor in SENSORS
    )


class WDEx2UltraSensor(CoordinatorEntity, SensorEntity):
    """Representation of a WD EX2 Ultra sensor."""

    def __init__(
        self,
        coordinator: WDEx2UltraCoordinator,
        entry: ConfigEntry,
        sensor_def: dict,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._sensor_def = sensor_def
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_{sensor_def['key']}"
        self._attr_name = sensor_def["name"]
        self._attr_native_unit_of_measurement = sensor_def["unit"] or None
        self._attr_icon = sensor_def.get("icon")

        device_class = sensor_def.get("device_class")
        if device_class == "temperature":
            self._attr_device_class = SensorDeviceClass.TEMPERATURE
        else:
            self._attr_device_class = None

        state_class = sensor_def.get("state_class")
        if state_class == "measurement":
            self._attr_state_class = SensorStateClass.MEASUREMENT
        elif state_class == "total_increasing":
            self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        else:
            self._attr_state_class = None

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name=f"WD MyCloud EX2 Ultra ({self._entry.data[CONF_HOST]})",
            manufacturer="Western Digital",
            model="MyCloud EX2 Ultra",
        )

    @property
    def native_value(self):
        """Return the current sensor value."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get(self._sensor_def["key"])
