"""Shared SNMP helper functions for WD MyCloud EX2 Ultra."""
from __future__ import annotations

import re
import logging

from homeassistant.exceptions import HomeAssistantError

_LOGGER = logging.getLogger(__name__)


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect to the device."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate invalid SNMP credentials."""


class SnmpLibraryMissing(HomeAssistantError):
    """Error to indicate pysnmp is not installed."""


def sanitize_host(host: str) -> str:
    """Strip http://, https://, trailing slashes and whitespace from a host string."""
    host = host.strip()
    host = re.sub(r'^https?://', '', host)
    host = host.rstrip('/')
    return host


def parse_wd_temperature(raw_value: str) -> float | None:
    """Parse WD-specific temperature format 'Centigrade:48 \tFahrenheit:118' into float."""
    if not raw_value or not isinstance(raw_value, str):
        return None
    
    # Try to match 'Centigrade:XX' or 'Fahrenheit:XX' format
    match_c = re.search(r'Centigrade:\s*(\d+)', raw_value)
    if match_c:
        try:
            return float(match_c.group(1))
        except (ValueError, AttributeError):
            pass
    
    # Fallback: try to parse as plain number
    try:
        return float(raw_value)
    except (ValueError, TypeError):
        _LOGGER.warning("Could not parse temperature value: %s", raw_value)
        return None


def build_auth_data(data: dict):
    """Build the correct pysnmp auth data object based on SNMP version."""
    try:
        from pysnmp.hlapi import (
            CommunityData,
            UsmUserData,
            usmHMACMD5AuthProtocol,
            usmHMACSHAAuthProtocol,
            usmDESPrivProtocol,
            usmAesCfb128Protocol,
        )
    except ImportError as err:
        raise SnmpLibraryMissing(
            "pysnmp-lextudio is not installed. Please restart Home Assistant."
        ) from err
    
    from .const import (
        CONF_SNMP_VERSION,
        CONF_COMMUNITY,
        CONF_USERNAME,
        CONF_AUTH_PROTOCOL,
        CONF_AUTH_PASSWORD,
        CONF_PRIV_PROTOCOL,
        CONF_PRIV_PASSWORD,
        SNMP_VERSION_V2C,
    )

    snmp_version = data.get(CONF_SNMP_VERSION, SNMP_VERSION_V2C)

    if snmp_version == SNMP_VERSION_V2C:
        return CommunityData(data.get(CONF_COMMUNITY, "public"), mpModel=1)

    auth_protocol_map = {
        "MD5": usmHMACMD5AuthProtocol,
        "SHA": usmHMACSHAAuthProtocol,
    }
    priv_protocol_map = {
        "DES": usmDESPrivProtocol,
        "AES": usmAesCfb128Protocol,
    }
    return UsmUserData(
        data[CONF_USERNAME],
        authKey=data[CONF_AUTH_PASSWORD],
        privKey=data[CONF_PRIV_PASSWORD],
        authProtocol=auth_protocol_map.get(data[CONF_AUTH_PROTOCOL], usmHMACMD5AuthProtocol),
        privProtocol=priv_protocol_map.get(data[CONF_PRIV_PROTOCOL], usmDESPrivProtocol),
    )


def test_snmp_connection(data: dict) -> None:
    """Perform a synchronous SNMP connectivity test (queries sysUpTime)."""
    try:
        from pysnmp.hlapi import (
            getCmd,
            SnmpEngine,
            UdpTransportTarget,
            ContextData,
            ObjectType,
            ObjectIdentity,
        )
    except ImportError as err:
        raise SnmpLibraryMissing(
            "pysnmp-lextudio is not installed. Please restart Home Assistant after installation."
        ) from err

    try:
        host = sanitize_host(data["host"])
        auth_data = build_auth_data(data)
        transport = UdpTransportTarget((host, 161), timeout=5, retries=1)

        error_indication, error_status, error_index, _ = next(
            getCmd(
                SnmpEngine(),
                auth_data,
                transport,
                ContextData(),
                ObjectType(ObjectIdentity("1.3.6.1.2.1.1.3.0")),
            )
        )
    except SnmpLibraryMissing:
        raise
    except Exception as err:
        _LOGGER.exception("Unexpected error during SNMP test connection: %s", err)
        raise CannotConnect(str(err)) from err

    if error_indication:
        _LOGGER.error("SNMP error_indication: %s", error_indication)
        raise CannotConnect(str(error_indication))
    if error_status:
        _LOGGER.error("SNMP error_status: %s", error_status)
        raise InvalidAuth(str(error_status))


def fetch_snmp_data(data: dict, sensors: list) -> dict:
    """Fetch all configured sensor OIDs via SNMP. Returns a dict keyed by sensor key."""
    try:
        from pysnmp.hlapi import (
            getCmd,
            SnmpEngine,
            UdpTransportTarget,
            ContextData,
            ObjectType,
            ObjectIdentity,
        )
    except ImportError as err:
        raise SnmpLibraryMissing("pysnmp-lextudio is not installed.") from err

    host = sanitize_host(data["host"])
    auth_data = build_auth_data(data)
    transport = UdpTransportTarget((host, 161), timeout=5, retries=1)
    engine = SnmpEngine()
    result = {}

    for sensor in sensors:
        oid = sensor["oid"]
        key = sensor["key"]
        try:
            error_indication, error_status, error_index, var_binds = next(
                getCmd(
                    engine,
                    auth_data,
                    transport,
                    ContextData(),
                    ObjectType(ObjectIdentity(oid)),
                )
            )
        except Exception as err:
            _LOGGER.warning("Exception fetching OID %s: %s", oid, err)
            result[key] = None
            continue

        if error_indication or error_status:
            _LOGGER.warning("SNMP error for OID %s: %s %s", oid, error_indication, error_status)
            result[key] = None
        else:
            raw_value = str(var_binds[0][1])
            
            # Special handling for system uptime (timeticks)
            if key == "system_uptime":
                try:
                    result[key] = round(int(raw_value) / 100, 1)
                except (ValueError, TypeError):
                    result[key] = raw_value
            
            # Special handling for WD disk temperatures
            elif "temperature" in key:
                result[key] = parse_wd_temperature(raw_value)
            
            # All other sensors: try to convert to float
            else:
                try:
                    result[key] = float(raw_value)
                except (ValueError, TypeError):
                    result[key] = raw_value

    return result
