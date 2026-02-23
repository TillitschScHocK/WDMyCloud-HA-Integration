"""WD MyCloud EX2 Ultra SNMP Integration for Home Assistant."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    CONF_SNMP_VERSION,
    CONF_HOST,
    CONF_COMMUNITY,
    CONF_USERNAME,
    CONF_AUTH_PROTOCOL,
    CONF_AUTH_PASSWORD,
    CONF_PRIV_PROTOCOL,
    CONF_PRIV_PASSWORD,
    CONF_SCAN_INTERVAL,
    SNMP_VERSION_V2C,
    SENSORS,
)

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
        """Fetch data from WD EX2 Ultra via SNMP."""
        try:
            return await self.hass.async_add_executor_job(self._fetch_snmp_data)
        except Exception as err:
            raise UpdateFailed(f"SNMP update failed: {err}") from err

    def _fetch_snmp_data(self) -> dict:
        """Synchronously fetch all SNMP OIDs."""
        from pysnmp.hlapi import (
            getCmd,
            SnmpEngine,
            CommunityData,
            UsmUserData,
            UdpTransportTarget,
            ContextData,
            ObjectType,
            ObjectIdentity,
            usmHMACMD5AuthProtocol,
            usmHMACSHAAuthProtocol,
            usmDESPrivProtocol,
            usmAesCfb128Protocol,
        )

        data = self.entry.data
        snmp_version = data.get(CONF_SNMP_VERSION, SNMP_VERSION_V2C)
        host = data[CONF_HOST]

        if snmp_version == SNMP_VERSION_V2C:
            auth_data = CommunityData(data.get(CONF_COMMUNITY, "public"), mpModel=1)
        else:
            auth_protocol_map = {
                "MD5": usmHMACMD5AuthProtocol,
                "SHA": usmHMACSHAAuthProtocol,
            }
            priv_protocol_map = {
                "DES": usmDESPrivProtocol,
                "AES": usmAesCfb128Protocol,
            }
            auth_data = UsmUserData(
                data[CONF_USERNAME],
                authKey=data[CONF_AUTH_PASSWORD],
                privKey=data[CONF_PRIV_PASSWORD],
                authProtocol=auth_protocol_map.get(data[CONF_AUTH_PROTOCOL], usmHMACMD5AuthProtocol),
                privProtocol=priv_protocol_map.get(data[CONF_PRIV_PROTOCOL], usmDESPrivProtocol),
            )

        transport = UdpTransportTarget((host, 161), timeout=5, retries=1)
        engine = SnmpEngine()

        result = {}
        for sensor in SENSORS:
            oid = sensor["oid"]
            key = sensor["key"]
            error_indication, error_status, error_index, var_binds = next(
                getCmd(
                    engine,
                    auth_data,
                    transport,
                    ContextData(),
                    ObjectType(ObjectIdentity(oid)),
                )
            )
            if error_indication or error_status:
                _LOGGER.warning("SNMP error for OID %s: %s %s", oid, error_indication, error_status)
                result[key] = None
            else:
                for var_bind in var_binds:
                    raw_value = str(var_bind[1])
                    # System uptime arrives as timeticks (hundredths of seconds), convert to seconds
                    if key == "system_uptime":
                        try:
                            result[key] = round(int(raw_value) / 100, 1)
                        except (ValueError, TypeError):
                            result[key] = raw_value
                    else:
                        try:
                            result[key] = float(raw_value)
                        except (ValueError, TypeError):
                            result[key] = raw_value
        return result
