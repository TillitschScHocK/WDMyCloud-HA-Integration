"""Sensor platform for WD MyCloud EX2 Ultra integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfInformation
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator

from .const import DOMAIN, SENSORS, CONF_HOST

_LOGGER = logging.getLogger(__name__)

_DC_MAP = {
    "temperature": SensorDeviceClass.TEMPERATURE,
    "data_size":   SensorDeviceClass.DATA_SIZE,
    "duration":    SensorDeviceClass.DURATION,
}
_SC_MAP = {
    "measurement":      SensorStateClass.MEASUREMENT,
    "total_increasing": SensorStateClass.TOTAL_INCREASING,
}


def _device_info(entry: ConfigEntry) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=f"WD MyCloud EX2 Ultra ({entry.data[CONF_HOST]})",
        manufacturer="Western Digital",
        model="MyCloud EX2 Ultra",
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up WD EX2 Ultra sensors from config entry."""
    coordinator: DataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Static scalar sensors
    async_add_entities(
        [WDEx2UltraSensor(coordinator, entry, s) for s in SENSORS]
    )

    added_disks:   set[str] = set()
    added_volumes: set[str] = set()

    def _add_dynamic() -> None:
        if coordinator.data is None:
            return
        new: list[SensorEntity] = []

        for disk in coordinator.data.get("_disks", []):
            idx = disk["index"]
            if idx in added_disks:
                continue
            added_disks.add(idx)
            model = disk.get("model", "").strip()
            label = f"Disk {idx}" + (f" ({model})" if model else "")
            new += [
                WDEx2UltraDiskSensor(coordinator, entry, idx, "temperature",
                    name=f"{label} Temperature", unit="°C",
                    icon="mdi:thermometer",
                    device_class=SensorDeviceClass.TEMPERATURE,
                    state_class=SensorStateClass.MEASUREMENT),
                WDEx2UltraDiskSensor(coordinator, entry, idx, "capacity",
                    name=f"{label} Capacity", unit=UnitOfInformation.GIGABYTES,
                    icon="mdi:harddisk",
                    device_class=SensorDeviceClass.DATA_SIZE,
                    state_class=SensorStateClass.MEASUREMENT),
                WDEx2UltraDiskSensor(coordinator, entry, idx, "status",
                    name=f"{label} Health", unit=None,
                    icon="mdi:harddisk", device_class=None, state_class=None),
                WDEx2UltraDiskSensor(coordinator, entry, idx, "model",
                    name=f"Disk {idx} Model", unit=None,
                    icon="mdi:information-outline", device_class=None, state_class=None),
                WDEx2UltraDiskSensor(coordinator, entry, idx, "vendor",
                    name=f"Disk {idx} Vendor", unit=None,
                    icon="mdi:information-outline", device_class=None, state_class=None),
            ]

        for vol in coordinator.data.get("_volumes", []):
            vidx = vol["index"]
            if vidx in added_volumes:
                continue
            added_volumes.add(vidx)
            vol_name = vol.get("name", "").strip() or f"Volume {vidx}"
            new += [
                WDEx2UltraVolumeSensor(coordinator, entry, vidx, "size_gib",
                    name=f"{vol_name} Total Size", unit=UnitOfInformation.GIBIBYTES,
                    icon="mdi:nas", device_class=SensorDeviceClass.DATA_SIZE,
                    state_class=SensorStateClass.MEASUREMENT),
                WDEx2UltraVolumeSensor(coordinator, entry, vidx, "free_gib",
                    name=f"{vol_name} Free Space", unit=UnitOfInformation.GIBIBYTES,
                    icon="mdi:nas", device_class=SensorDeviceClass.DATA_SIZE,
                    state_class=SensorStateClass.MEASUREMENT),
                WDEx2UltraVolumeSensor(coordinator, entry, vidx, "used_gib",
                    name=f"{vol_name} Used Space", unit=UnitOfInformation.GIBIBYTES,
                    icon="mdi:nas", device_class=SensorDeviceClass.DATA_SIZE,
                    state_class=SensorStateClass.MEASUREMENT),
                WDEx2UltraVolumeSensor(coordinator, entry, vidx, "used_pct",
                    name=f"{vol_name} Used Percent", unit="%",
                    icon="mdi:chart-pie", device_class=None,
                    state_class=SensorStateClass.MEASUREMENT),
                WDEx2UltraVolumeSensor(coordinator, entry, vidx, "raid_level",
                    name=f"{vol_name} RAID Level", unit=None,
                    icon="mdi:shield-half-full", device_class=None, state_class=None),
            ]

        if new:
            async_add_entities(new)

    _add_dynamic()
    entry.async_on_unload(coordinator.async_add_listener(_add_dynamic))


# ---------------------------------------------------------------------------
# Sensor classes
# ---------------------------------------------------------------------------

class WDEx2UltraSensor(CoordinatorEntity, SensorEntity):
    """Static scalar sensor backed by a single OID."""

    def __init__(self, coordinator, entry: ConfigEntry, sensor_def: dict) -> None:
        super().__init__(coordinator)
        self._def   = sensor_def
        self._entry = entry
        self._attr_unique_id                    = f"{entry.entry_id}_{sensor_def['key']}"
        self._attr_name                         = sensor_def["name"]
        self._attr_native_unit_of_measurement   = sensor_def.get("unit")
        self._attr_icon                         = sensor_def.get("icon")
        self._attr_device_class                 = _DC_MAP.get(sensor_def.get("device_class"))
        self._attr_state_class                  = _SC_MAP.get(sensor_def.get("state_class"))

    @property
    def device_info(self) -> DeviceInfo:
        return _device_info(self._entry)

    @property
    def native_value(self) -> Any:
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get(self._def["key"])


class WDEx2UltraDiskSensor(CoordinatorEntity, SensorEntity):
    """Dynamic sensor for one metric of one physical disk."""

    def __init__(self, coordinator, entry, disk_index, metric,
                 name, unit, icon, device_class, state_class) -> None:
        super().__init__(coordinator)
        self._entry      = entry
        self._idx        = disk_index
        self._metric     = metric
        self._attr_unique_id                  = f"{entry.entry_id}_disk_{disk_index}_{metric}"
        self._attr_name                       = name
        self._attr_native_unit_of_measurement = unit
        self._attr_icon                       = icon
        self._attr_device_class               = device_class
        self._attr_state_class                = state_class

    @property
    def device_info(self) -> DeviceInfo:
        return _device_info(self._entry)

    @property
    def native_value(self) -> Any:
        if self.coordinator.data is None:
            return None
        for d in self.coordinator.data.get("_disks", []):
            if d["index"] == self._idx:
                return d.get(self._metric)
        return None


class WDEx2UltraVolumeSensor(CoordinatorEntity, SensorEntity):
    """Dynamic sensor for one metric of one RAID volume."""

    def __init__(self, coordinator, entry, volume_index, metric,
                 name, unit, icon, device_class, state_class) -> None:
        super().__init__(coordinator)
        self._entry      = entry
        self._vidx       = volume_index
        self._metric     = metric
        self._attr_unique_id                  = f"{entry.entry_id}_volume_{volume_index}_{metric}"
        self._attr_name                       = name
        self._attr_native_unit_of_measurement = unit
        self._attr_icon                       = icon
        self._attr_device_class               = device_class
        self._attr_state_class                = state_class

    @property
    def device_info(self) -> DeviceInfo:
        return _device_info(self._entry)

    @property
    def native_value(self) -> Any:
        if self.coordinator.data is None:
            return None
        for v in self.coordinator.data.get("_volumes", []):
            if v["index"] == self._vidx:
                return v.get(self._metric)
        return None
