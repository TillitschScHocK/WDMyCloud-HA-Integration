"""Shared async SNMP helper functions for WD MyCloud EX2 Ultra.

Uses pysnmp.hlapi.v3arch.asyncio – the same API as HA core's built-in
SNMP integration (pysnmp==7.1.22).
"""
from __future__ import annotations

import logging
import re

from homeassistant.exceptions import HomeAssistantError

_LOGGER = logging.getLogger(__name__)


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect to the device."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate invalid SNMP credentials."""


class SnmpLibraryMissing(HomeAssistantError):
    """Error to indicate pysnmp is not installed or incompatible."""


def sanitize_host(host: str) -> str:
    """Strip http://, https://, trailing slashes and whitespace."""
    host = host.strip()
    host = re.sub(r'^https?://', '', host)
    host = host.rstrip('/')
    return host


def parse_wd_temperature(raw_value: str) -> float | None:
    """Parse WD temperature string 'Centigrade:48 Fahrenheit:118' to float."""
    if not raw_value or not isinstance(raw_value, str):
        return None
    match_c = re.search(r'Centigrade:\s*(\d+)', raw_value)
    if match_c:
        try:
            return float(match_c.group(1))
        except (ValueError, AttributeError):
            pass
    try:
        return float(raw_value)
    except (ValueError, TypeError):
        _LOGGER.warning("Could not parse temperature value: %s", raw_value)
        return None


def _build_auth_data(data: dict):
    """Build pysnmp auth data based on SNMP version (sync helper)."""
    try:
        from pysnmp.hlapi.v3arch.asyncio import (
            CommunityData,
            UsmUserData,
            usmHMACMD5AuthProtocol,
            usmHMACSHAAuthProtocol,
            usmDESPrivProtocol,
            usmAesCfb128Protocol,
        )
    except ImportError as err:
        raise SnmpLibraryMissing(
            "pysnmp 7.1.22 is not installed. Restart Home Assistant after HACS installation."
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


async def test_snmp_connection(data: dict) -> None:
    """Async SNMP connectivity test – queries sysUpTime (1.3.6.1.2.1.1.3.0)."""
    try:
        from pysnmp.hlapi.v3arch.asyncio import (
            SnmpEngine,
            ContextData,
            UdpTransportTarget,
            ObjectType,
            ObjectIdentity,
            get_cmd,
        )
    except ImportError as err:
        raise SnmpLibraryMissing(
            "pysnmp 7.1.22 is not installed. Restart Home Assistant."
        ) from err

    try:
        host = sanitize_host(data["host"])
        auth_data = _build_auth_data(data)
        target = await UdpTransportTarget.create((host, 161), timeout=5, retries=1)

        error_indication, error_status, error_index, _ = await get_cmd(
            SnmpEngine(),
            auth_data,
            target,
            ContextData(),
            ObjectType(ObjectIdentity("1.3.6.1.2.1.1.3.0")),
        )
    except SnmpLibraryMissing:
        raise
    except Exception as err:
        _LOGGER.exception("Unexpected error during SNMP test: %s", err)
        raise CannotConnect(str(err)) from err

    if error_indication:
        _LOGGER.error("SNMP test error_indication: %s", error_indication)
        raise CannotConnect(str(error_indication))
    if error_status:
        _LOGGER.error("SNMP test error_status: %s", error_status)
        raise InvalidAuth(str(error_status))


async def fetch_snmp_data(data: dict, sensors: list) -> dict:
    """Fetch all sensor OIDs via SNMP. Returns dict keyed by sensor key."""
    try:
        from pysnmp.hlapi.v3arch.asyncio import (
            SnmpEngine,
            ContextData,
            UdpTransportTarget,
            ObjectType,
            ObjectIdentity,
            get_cmd,
        )
    except ImportError as err:
        raise SnmpLibraryMissing(
            "pysnmp 7.1.22 is not installed. Restart Home Assistant."
        ) from err

    host = sanitize_host(data["host"])
    auth_data = _build_auth_data(data)
    target = await UdpTransportTarget.create((host, 161), timeout=5, retries=1)
    engine = SnmpEngine()
    result: dict = {}

    for sensor in sensors:
        oid = sensor["oid"]
        key = sensor["key"]
        try:
            error_indication, error_status, error_index, var_binds = await get_cmd(
                engine,
                auth_data,
                target,
                ContextData(),
                ObjectType(ObjectIdentity(oid)),
            )
        except Exception as err:
            _LOGGER.warning("Exception fetching OID %s: %s", oid, err)
            result[key] = None
            continue

        if error_indication or error_status:
            _LOGGER.warning(
                "SNMP error for OID %s: %s %s", oid, error_indication, error_status
            )
            result[key] = None
        else:
            raw_value = str(var_binds[0][1])
            if key == "system_uptime":
                try:
                    result[key] = round(int(raw_value) / 100, 1)
                except (ValueError, TypeError):
                    result[key] = raw_value
            elif "temperature" in key:
                result[key] = parse_wd_temperature(raw_value)
            else:
                try:
                    result[key] = float(raw_value)
                except (ValueError, TypeError):
                    result[key] = raw_value

    return result
