"""Shared async SNMP helper functions for WD MyCloud EX2 Ultra."""
from __future__ import annotations

import asyncio
import re
import logging

from homeassistant.exceptions import HomeAssistantError

_LOGGER = logging.getLogger(__name__)


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect to the device."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate invalid SNMP credentials."""


class SnmpLibraryMissing(HomeAssistantError):
    """Error to indicate pysnmp is not installed or incompatible."""


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


def _get_snmp_modules():
    """Import pysnmp v1arch asyncio modules; raise SnmpLibraryMissing on failure."""
    try:
        from pysnmp.hlapi.v1arch.asyncio import (
            get_cmd,
            CommunityData,
            UsmUserData,
            SnmpDispatcher,
            UdpTransportTarget,
            ObjectType,
            ObjectIdentity,
            usmHMACMD5AuthProtocol,
            usmHMACSHAAuthProtocol,
            usmDESPrivProtocol,
            usmAesCfb128Protocol,
        )
        return (
            get_cmd,
            CommunityData,
            UsmUserData,
            SnmpDispatcher,
            UdpTransportTarget,
            ObjectType,
            ObjectIdentity,
            usmHMACMD5AuthProtocol,
            usmHMACSHAAuthProtocol,
            usmDESPrivProtocol,
            usmAesCfb128Protocol,
        )
    except ImportError as err:
        raise SnmpLibraryMissing(
            "pysnmp is not installed or incompatible. "
            "Please install pysnmp>=6.2 and restart Home Assistant."
        ) from err


async def _build_auth_data(data: dict):
    """Build the correct pysnmp auth data object based on SNMP version."""
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

    (
        _,
        CommunityData,
        UsmUserData,
        _,
        _,
        _,
        _,
        usmHMACMD5AuthProtocol,
        usmHMACSHAAuthProtocol,
        usmDESPrivProtocol,
        usmAesCfb128Protocol,
    ) = _get_snmp_modules()

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
        authProtocol=auth_protocol_map.get(
            data[CONF_AUTH_PROTOCOL], usmHMACMD5AuthProtocol
        ),
        privProtocol=priv_protocol_map.get(
            data[CONF_PRIV_PROTOCOL], usmDESPrivProtocol
        ),
    )


async def test_snmp_connection(data: dict) -> None:
    """Perform an async SNMP connectivity test (queries sysUpTime OID)."""
    (
        get_cmd,
        _,
        _,
        SnmpDispatcher,
        UdpTransportTarget,
        ObjectType,
        ObjectIdentity,
        *_rest,
    ) = _get_snmp_modules()

    try:
        host = sanitize_host(data["host"])
        auth_data = await _build_auth_data(data)
        transport = await UdpTransportTarget.create((host, 161), timeout=5, retries=1)

        error_indication, error_status, error_index, _ = await get_cmd(
            SnmpDispatcher(),
            auth_data,
            transport,
            ObjectType(ObjectIdentity("1.3.6.1.2.1.1.3.0")),
        )
    except SnmpLibraryMissing:
        raise
    except Exception as err:
        _LOGGER.exception("Unexpected error during SNMP test connection: %s", err)
        raise CannotConnect(str(err)) from err

    if error_indication:
        _LOGGER.error("SNMP error_indication during test: %s", error_indication)
        raise CannotConnect(str(error_indication))
    if error_status:
        _LOGGER.error("SNMP error_status during test: %s", error_status)
        raise InvalidAuth(str(error_status))


async def fetch_snmp_data(data: dict, sensors: list) -> dict:
    """Fetch all configured sensor OIDs via SNMP. Returns a dict keyed by sensor key."""
    (
        get_cmd,
        _,
        _,
        SnmpDispatcher,
        UdpTransportTarget,
        ObjectType,
        ObjectIdentity,
        *_rest,
    ) = _get_snmp_modules()

    host = sanitize_host(data["host"])
    auth_data = await _build_auth_data(data)
    transport = await UdpTransportTarget.create((host, 161), timeout=5, retries=1)
    dispatcher = SnmpDispatcher()
    result = {}

    for sensor in sensors:
        oid = sensor["oid"]
        key = sensor["key"]
        try:
            error_indication, error_status, error_index, var_binds = await get_cmd(
                dispatcher,
                auth_data,
                transport,
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
