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

    async_add_entities(entities)

    # -------------------------------------------------------------------
    # Dynamic disk and volume sensors.
    # The coordinator may not yet have data at setup time (e.g. on the
    # very first poll), so we register a one-shot listener that adds the
    # dynamic entities as soon as the first successful update arrives.
    # Subsequent updates are handled by CoordinatorEntity automatically.
    # -------------------------------------------------------------------
    added_disk_indices: set[str] = set()
    added_volume_indices: set[str] = set()

    def _add_dynamic_entities() -> None:
        """Add disk and volume entities for newly discovered indices."""
        if coordinator.data is None:
            return

        new_entities: list[SensorEntity] = []

        # --- Disk sensors ---
        disks = coordinator.data.get("_disks", [])
        for disk in disks:
            idx = disk["index"]
            if idx in added_disk_indices:
                continue
            added_disk_indices.add(idx)

            model = disk.get("model", "").strip()
            label = f"Disk {idx}" + (f" ({model})" if model else "")

            new_entities.append(
                WDEx2UltraDiskSensor(
                    coordinator, entry, idx, "temperature",
                    name=f"{label} Temperature",
                    unit="°C",
                    icon="mdi:thermometer",
                    device_class=SensorDeviceClass.TEMPERATURE,
                    state_class=SensorStateClass.MEASUREMENT,
                )
            )
            new_entities.append(
                WDEx2UltraDiskSensor(
                    coordinator, entry, idx, "capacity",
                    name=f"{label} Capacity",
                    unit="GB",
                    icon="mdi:harddisk",
                    device_class=None,
                    state_class=SensorStateClass.MEASUREMENT,
                )
            )
            new_entities.append(
                WDEx2UltraDiskSensor(
                    coordinator, entry, idx, "status",
                    name=f"{label} Health",
                    unit=None,
                    icon="mdi:harddisk",
                    device_class=None,
                    state_class=None,
                )
            )
            new_entities.append(
                WDEx2UltraDiskSensor(
                    coordinator, entry, idx, "model",
                    name=f"Disk {idx} Model",
                    unit=None,
                    icon="mdi:information-outline",
                    device_class=None,
                    state_class=None,
                )
            )
            new_entities.append(
                WDEx2UltraDiskSensor(
                    coordinator, entry, idx, "vendor",
                    name=f"Disk {idx} Vendor",
                    unit=None,
                    icon="mdi:information-outline",
                    device_class=None,
                    state_class=None,
                )
            )

        # --- Volume / RAID sensors ---
        volumes = coordinator.data.get("_volumes", [])
        for vol in volumes:
            vidx = vol["index"]
            if vidx in added_volume_indices:
                continue
            added_volume_indices.add(vidx)

            vol_name = vol.get("name", "").strip() or f"Volume {vidx}"

            new_entities.append(
                WDEx2UltraVolumeSensor(
                    coordinator, entry, vidx, "size_mb",
                    name=f"{vol_name} Total Size",
                    unit="MB",
                    icon="mdi:nas",
                    device_class=None,
                    state_class=SensorStateClass.MEASUREMENT,
                )
            )
            new_entities.append(
                WDEx2UltraVolumeSensor(
                    coordinator, entry, vidx, "free_mb",
                    name=f"{vol_name} Free Space",
                    unit="MB",
                    icon="mdi:nas",
                    device_class=None,
                    state_class=SensorStateClass.MEASUREMENT,
                )
            )
            new_entities.append(
                WDEx2UltraVolumeSensor(
                    coordinator, entry, vidx, "used_mb",
                    name=f"{vol_name} Used Space",
                    unit="MB",
                    icon="mdi:nas",
                    device_class=None,
                    state_class=SensorStateClass.MEASUREMENT,
                )
            )
            new_entities.append(
                WDEx2UltraVolumeSensor(
                    coordinator, entry, vidx, "used_pct",
                    name=f"{vol_name} Used Percent",
                    unit="%",
                    icon="mdi:chart-pie",
                    device_class=None,
                    state_class=SensorStateClass.MEASUREMENT,
                )
            )
            new_entities.append(
                WDEx2UltraVolumeSensor(
                    coordinator, entry, vidx, "raid_level",
                    name=f"{vol_name} RAID Level",
                    unit=None,
                    icon="mdi:shield-half-full",
                    device_class=None,
                    state_class=None,
                )
            )

        if new_entities:
            async_add_entities(new_entities)

    # Try to add entities immediately if data is already available
    _add_dynamic_entities()

    # Also register as a coordinator listener so entities are added after
    # the first update if coordinator.data was None during setup.
    entry.async_on_unload(
        coordinator.async_add_listener(_add_dynamic_entities)
    )


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
        elif device_class == "data_size":
            self._attr_device_class = SensorDeviceClass.DATA_SIZE
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


class WDEx2UltraVolumeSensor(CoordinatorEntity, SensorEntity):
    """Representation of a dynamic WD volume/RAID table sensor."""

    def __init__(
        self,
        coordinator: WDEx2UltraCoordinator,
        entry: ConfigEntry,
        volume_index: str,
        metric: str,
        name: str,
        unit: str | None,
        icon: str,
        device_class: SensorDeviceClass | None,
        state_class: SensorStateClass | None,
    ) -> None:
        """Initialize the volume sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._volume_index = volume_index
        self._metric = metric
        self._attr_unique_id = f"{entry.entry_id}_volume_{volume_index}_{metric}"
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
        """Return the current value from the volume table."""
        if self.coordinator.data is None:
            return None
        volumes: list[dict] = self.coordinator.data.get("_volumes", [])
        for vol in volumes:
            if vol["index"] == self._volume_index:
                return vol.get(self._metric)
        return None
