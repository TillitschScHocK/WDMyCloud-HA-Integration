"""WD MyCloud EX2 Ultra SNMP Integration for Home Assistant."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    CONF_SCAN_INTERVAL,
    SENSORS,
)
from .snmp_helper import fetch_snmp_data

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up WD EX2 Ultra from a config entry."""
    scan_interval = entry.data.get(CONF_SCAN_INTERVAL, 60)

    coordinator = WDEx2UltraCoordinator(
        hass,
        entry,
        update_interval=timedelta(seconds=scan_interval),
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


class WDEx2UltraCoordinator(DataUpdateCoordinator):
    """Data update coordinator for WD EX2 Ultra."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        update_interval: timedelta,
    ) -> None:
        """Initialize coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=update_interval,
        )
        self.entry = entry

    async def _async_update_data(self) -> dict:
        """Fetch data from WD EX2 Ultra via SNMP (async)."""
        try:
            return await fetch_snmp_data(dict(self.entry.data), SENSORS)
        except Exception as err:
            raise UpdateFailed(f"SNMP update failed: {err}") from err
