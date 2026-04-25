"""Sensor platform for WD MyCloud EX2 Ultra integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator

from .const import DOMAIN, SENSORS, CONF_HOST

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up WD EX2 Ultra sensors from config entry."""
    coordinator: DataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    host = entry.data[CONF_HOST]

    device_info = DeviceInfo(
        identifiers={(DOMAIN, host)},
        name="WD MyCloud EX2 Ultra",
        manufacturer="Western Digital",
        model="MyCloud EX2 Ultra",
    )

    entities: list[SensorEntity] = []

    # Static scalar sensors
    for sensor_def in SENSORS:
        entities.append(
            WDEx2UltraSensor(
                coordinator=coordinator,
                sensor_def=sensor_def,
                device_info=device_info,
                entry_id=entry.entry_id,
            )
        )

    # Dynamic disk sensors
    if coordinator.data and coordinator.data.get("disks"):
        for disk in coordinator.data["disks"]:
            n = disk["index"]
            entities += [
                WDEx2UltraDiskSensor(coordinator, device_info, entry.entry_id, disk, n, "temperature",
                                     f"Disk {n} Temperature", "°C", "temperature", "measurement", "mdi:thermometer"),
                WDEx2UltraDiskSensor(coordinator, device_info, entry.entry_id, disk, n, "capacity_gb",
                                     f"Disk {n} Capacity", "GB", "data_size", "measurement", "mdi:harddisk"),
                WDEx2UltraDiskSensor(coordinator, device_info, entry.entry_id, disk, n, "health",
                                     f"Disk {n} Health", None, None, None, "mdi:shield-check"),
                WDEx2UltraDiskSensor(coordinator, device_info, entry.entry_id, disk, n, "model",
                                     f"Disk {n} Model", None, None, None, "mdi:harddisk"),
                WDEx2UltraDiskSensor(coordinator, device_info, entry.entry_id, disk, n, "vendor",
                                     f"Disk {n} Vendor", None, None, None, "mdi:factory"),
            ]

    # Dynamic volume sensors
    if coordinator.data and coordinator.data.get("volumes"):
        for vol in coordinator.data["volumes"]:
            name = vol["name"]
            idx = vol["index"]
            entities += [
                WDEx2UltraVolumeSensor(coordinator, device_info, entry.entry_id, vol, idx, "total_gib",
                                       f"{name} Total Size", "GiB", "data_size", "measurement", "mdi:harddisk"),
                WDEx2UltraVolumeSensor(coordinator, device_info, entry.entry_id, vol, idx, "free_gib",
                                       f"{name} Free Space", "GiB", "data_size", "measurement", "mdi:harddisk"),
                WDEx2UltraVolumeSensor(coordinator, device_info, entry.entry_id, vol, idx, "used_gib",
                                       f"{name} Used Space", "GiB", "data_size", "measurement", "mdi:harddisk"),
                WDEx2UltraVolumeSensor(coordinator, device_info, entry.entry_id, vol, idx, "used_pct",
                                       f"{name} Used Percent", "%", None, "measurement", "mdi:percent"),
                WDEx2UltraVolumeSensor(coordinator, device_info, entry.entry_id, vol, idx, "raid_level",
                                       f"{name} RAID Level", None, None, None, "mdi:server"),
            ]

    async_add_entities(entities)


class WDEx2UltraSensor(CoordinatorEntity, SensorEntity):
    """Static scalar sensor entity."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        sensor_def: dict,
        device_info: DeviceInfo,
        entry_id: str,
    ) -> None:
        super().__init__(coordinator)
        self._sensor_def = sensor_def
        self._attr_name = sensor_def["name"]
        self._attr_unique_id = f"{entry_id}_{sensor_def['key']}"
        self._attr_native_unit_of_measurement = sensor_def.get("unit")
        self._attr_device_class = sensor_def.get("device_class")
        sc = sensor_def.get("state_class")
        self._attr_state_class = SensorStateClass(sc) if sc else None
        self._attr_icon = sensor_def.get("icon")
        self._attr_device_info = device_info

    @property
    def native_value(self) -> Any:
        if not self.coordinator.data:
            return None
        return self.coordinator.data["scalars"].get(self._sensor_def["key"])


class WDEx2UltraDiskSensor(CoordinatorEntity, SensorEntity):
    """Dynamic disk sensor entity."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        device_info: DeviceInfo,
        entry_id: str,
        disk: dict,
        disk_index: str,
        field: str,
        name: str,
        unit: str | None,
        device_class: str | None,
        state_class: str | None,
        icon: str,
    ) -> None:
        super().__init__(coordinator)
        self._disk_index = disk_index
        self._field = field
        self._attr_name = name
        self._attr_unique_id = f"{entry_id}_disk_{disk_index}_{field}"
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_state_class = SensorStateClass(state_class) if state_class else None
        self._attr_icon = icon
        self._attr_device_info = device_info

    @property
    def native_value(self) -> Any:
        if not self.coordinator.data:
            return None
        for disk in self.coordinator.data.get("disks", []):
            if disk["index"] == self._disk_index:
                return disk.get(self._field)
        return None


class WDEx2UltraVolumeSensor(CoordinatorEntity, SensorEntity):
    """Dynamic volume sensor entity."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        device_info: DeviceInfo,
        entry_id: str,
        vol: dict,
        vol_index: str,
        field: str,
        name: str,
        unit: str | None,
        device_class: str | None,
        state_class: str | None,
        icon: str,
    ) -> None:
        super().__init__(coordinator)
        self._vol_index = vol_index
        self._field = field
        self._attr_name = name
        self._attr_unique_id = f"{entry_id}_volume_{vol_index}_{field}"
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_state_class = SensorStateClass(state_class) if state_class else None
        self._attr_icon = icon
        self._attr_device_info = device_info

    @property
    def native_value(self) -> Any:
        if not self.coordinator.data:
            return None
        for vol in self.coordinator.data.get("volumes", []):
            if vol["index"] == self._vol_index:
                return vol.get(self._field)
        return None
