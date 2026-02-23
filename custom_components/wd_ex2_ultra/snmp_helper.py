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


def parse_snmp_number(raw_value: str) -> float | None:
    """Safely parse a numeric string from SNMP, ignoring locale separators."""
    if raw_value is None:
        return None
    s = str(raw_value).strip()
    # Remove thousands separators (dot or space) and normalise decimal comma
    s = re.sub(r'[\s]', '', s)          # remove spaces
    # If both '.' and ',' exist, treat '.' as thousands sep
    if '.' in s and ',' in s:
        s = s.replace('.', '').replace(',', '.')
    elif ',' in s:
        s = s.replace(',', '.')
    # Remove any remaining non-numeric chars except leading minus and dot
    s = re.sub(r'[^0-9.\-]', '', s)
    try:
        return float(s)
    except (ValueError, TypeError):
        return None


def parse_wd_temperature(raw_value: str) -> float | None:
    """Parse WD temperature string 'Centigrade:48 Fahrenheit:118' to float.

    Also handles plain numeric strings returned by the WD MIB disk table.
    """
    if not raw_value or not isinstance(raw_value, str):
        return None
    match_c = re.search(r'Centigrade:\s*(\d+)', raw_value)
    if match_c:
        try:
            return float(match_c.group(1))
        except (ValueError, AttributeError):
            pass
    return parse_snmp_number(raw_value)


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


async def walk_snmp_column(data: dict, column_oid: str) -> dict[str, str]:
    """Walk a single SNMP table column and return {row_index: value} dict.

    The row index is extracted as the last OID component after column_oid.
    """
    try:
        from pysnmp.hlapi.v3arch.asyncio import (
            SnmpEngine,
            ContextData,
            UdpTransportTarget,
            ObjectType,
            ObjectIdentity,
            next_cmd,
        )
    except ImportError as err:
        raise SnmpLibraryMissing(
            "pysnmp 7.1.22 is not installed. Restart Home Assistant."
        ) from err

    host = sanitize_host(data["host"])
    auth_data = _build_auth_data(data)
    target = await UdpTransportTarget.create((host, 161), timeout=5, retries=1)
    engine = SnmpEngine()
    result: dict[str, str] = {}

    # Walk the column using next_cmd
    async for (error_indication, error_status, error_index, var_binds) in next_cmd(
        engine,
        auth_data,
        target,
        ContextData(),
        ObjectType(ObjectIdentity(column_oid)),
        lexicographicMode=False,
    ):
        if error_indication or error_status:
            _LOGGER.debug("Walk ended for OID %s: %s %s", column_oid, error_indication, error_status)
            break
        for var_bind in var_binds:
            oid_str = str(var_bind[0])
            value_str = str(var_bind[1])
            # Extract row index = last part of OID after column_oid
            if oid_str.startswith(column_oid + "."):
                row_idx = oid_str[len(column_oid) + 1:]
                result[row_idx] = value_str
            else:
                # Walked beyond this column – stop
                break
        else:
            continue
        break

    return result


async def fetch_disk_table(data: dict) -> list[dict]:
    """Fetch WD disk table dynamically. Returns list of disk dicts.

    Each dict has keys: index, vendor, model, serial, temperature, capacity.
    """
    from .const import (
        WD_DISK_COL_NUM,
        WD_DISK_COL_VENDOR,
        WD_DISK_COL_MODEL,
        WD_DISK_COL_SERIAL,
        WD_DISK_COL_TEMPERATURE,
        WD_DISK_COL_CAPACITY,
    )

    # First walk the DiskNum column to find which indices exist
    indices = await walk_snmp_column(data, WD_DISK_COL_NUM)
    if not indices:
        _LOGGER.debug("WD disk table: no disks found via SNMP walk")
        return []

    _LOGGER.debug("WD disk table indices found: %s", list(indices.keys()))

    # Fetch remaining columns for each index
    vendors    = await walk_snmp_column(data, WD_DISK_COL_VENDOR)
    models     = await walk_snmp_column(data, WD_DISK_COL_MODEL)
    serials    = await walk_snmp_column(data, WD_DISK_COL_SERIAL)
    temps      = await walk_snmp_column(data, WD_DISK_COL_TEMPERATURE)
    capacities = await walk_snmp_column(data, WD_DISK_COL_CAPACITY)

    disks = []
    for idx in sorted(indices.keys(), key=lambda x: int(x) if x.isdigit() else x):
        disks.append({
            "index": idx,
            "vendor":      vendors.get(idx, ""),
            "model":       models.get(idx, ""),
            "serial":      serials.get(idx, ""),
            "temperature": parse_wd_temperature(temps.get(idx, "")),
            "capacity":    parse_snmp_number(capacities.get(idx, "")),
        })
    return disks


async def fetch_snmp_data(data: dict, sensors: list) -> dict:
    """Fetch all scalar sensor OIDs via SNMP. Returns dict keyed by sensor key.

    Also fetches the WD disk table and adds disk_<idx>_* keys to the result.
    """
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
        transform = sensor.get("transform")
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
                parsed = parse_snmp_number(raw_value)
                result[key] = round(parsed / 100, 1) if parsed is not None else None
            elif "temperature" in key:
                result[key] = parse_wd_temperature(raw_value)
            elif transform == "kb_to_mib":
                parsed = parse_snmp_number(raw_value)
                result[key] = round(parsed / 1024, 1) if parsed is not None else None
            else:
                parsed = parse_snmp_number(raw_value)
                result[key] = parsed if parsed is not None else raw_value

    # Fetch dynamic WD disk table
    try:
        disks = await fetch_disk_table(data)
        result["_disks"] = disks
    except Exception as err:
        _LOGGER.warning("Could not fetch WD disk table: %s", err)
        result["_disks"] = []

    return result
