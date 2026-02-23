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

    entities: list[SensorEntity] = []

    # Static scalar sensors
    for sensor in SENSORS:
        entities.append(WDEx2UltraSensor(coordinator, entry, sensor))

    # Dynamic disk sensors from WD disk table
    disks = (coordinator.data or {}).get("_disks", [])
    for disk in disks:
        idx = disk["index"]
        model = disk.get("model", "").strip()
        label = f"Disk {idx}" + (f" ({model})" if model else "")
        entities.append(
            WDEx2UltraDiskSensor(
                coordinator, entry, idx, "temperature",
                name=f"{label} Temperature",
                unit="°C",
                icon="mdi:thermometer",
                device_class=SensorDeviceClass.TEMPERATURE,
                state_class=SensorStateClass.MEASUREMENT,
            )
        )
        entities.append(
            WDEx2UltraDiskSensor(
                coordinator, entry, idx, "capacity",
                name=f"{label} Capacity",
                unit="GB",
                icon="mdi:harddisk",
                device_class=None,
                state_class=SensorStateClass.MEASUREMENT,
            )
        )
        entities.append(
            WDEx2UltraDiskSensor(
                coordinator, entry, idx, "model",
                name=f"Disk {idx} Model",
                unit=None,
                icon="mdi:harddisk",
                device_class=None,
                state_class=None,
            )
        )
        entities.append(
            WDEx2UltraDiskSensor(
                coordinator, entry, idx, "vendor",
                name=f"Disk {idx} Vendor",
                unit=None,
                icon="mdi:information-outline",
                device_class=None,
                state_class=None,
            )
        )

    async_add_entities(entities)


class WDEx2UltraSensor(CoordinatorEntity, SensorEntity):
    """Representation of a static WD EX2 Ultra sensor (scalar OID)."""

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


class WDEx2UltraDiskSensor(CoordinatorEntity, SensorEntity):
    """Representation of a dynamic WD disk table sensor."""

    def __init__(
        self,
        coordinator: WDEx2UltraCoordinator,
        entry: ConfigEntry,
        disk_index: str,
        metric: str,
        name: str,
        unit: str | None,
        icon: str,
        device_class: SensorDeviceClass | None,
        state_class: SensorStateClass | None,
    ) -> None:
        """Initialize the disk sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._disk_index = disk_index
        self._metric = metric
        self._attr_unique_id = f"{entry.entry_id}_disk_{disk_index}_{metric}"
        self._attr_name = name
        self._attr_native_unit_of_measurement = unit
        self._attr_icon = icon
        self._attr_device_class = device_class
        self._attr_state_class = state_class

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
        """Return the current value from the disk table."""
        if self.coordinator.data is None:
            return None
        disks: list[dict] = self.coordinator.data.get("_disks", [])
        for disk in disks:
            if disk["index"] == self._disk_index:
                return disk.get(self._metric)
        return None
