"""Shared async SNMP helper functions for WD MyCloud EX2 Ultra.

Uses pysnmp.hlapi.v3arch.asyncio - the same API as HA core's built-in
SNMP integration (pysnmp==7.1.22).
"""
from __future__ import annotations

import asyncio
import logging
import re

from homeassistant.exceptions import HomeAssistantError

_LOGGER = logging.getLogger(__name__)

SNMP_TIMEOUT = 5
SNMP_RETRIES = 1
SNMP_PORT = 161
MAX_WALK_ITERATIONS = 100


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect to the device."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate invalid SNMP credentials."""


class SnmpLibraryMissing(HomeAssistantError):
    """Error to indicate pysnmp is not installed or incompatible."""


def _get_snmp_imports():
    """Import pysnmp async API; raise SnmpLibraryMissing on failure."""
    try:
        from pysnmp.hlapi.v3arch.asyncio import (
            SnmpEngine,
            ContextData,
            UdpTransportTarget,
            ObjectType,
            ObjectIdentity,
            get_cmd,
            next_cmd,
            CommunityData,
            UsmUserData,
            usmHMACMD5AuthProtocol,
            usmHMACSHAAuthProtocol,
            usmDESPrivProtocol,
            usmAesCfb128Protocol,
        )
        return (
            SnmpEngine, ContextData, UdpTransportTarget, ObjectType,
            ObjectIdentity, get_cmd, next_cmd, CommunityData, UsmUserData,
            usmHMACMD5AuthProtocol, usmHMACSHAAuthProtocol,
            usmDESPrivProtocol, usmAesCfb128Protocol,
        )
    except ImportError as err:
        raise SnmpLibraryMissing(
            "pysnmp 7.1.22 is not installed. Restart Home Assistant after HACS installation."
        ) from err


def sanitize_host(host: str) -> str:
    """Strip http://, https://, trailing slashes and whitespace."""
    host = host.strip()
    host = re.sub(r'^https?://', '', host)
    return host.rstrip('/')


def parse_snmp_number(raw_value: str) -> float | None:
    """Safely parse a numeric string from SNMP, ignoring locale separators."""
    if raw_value is None:
        return None
    s = str(raw_value).strip()
    s = re.sub(r'[\s]', '', s)
    if '.' in s and ',' in s:
        s = s.replace('.', '').replace(',', '.')
    elif ',' in s:
        s = s.replace(',', '.')
    s = re.sub(r'[^0-9.\-]', '', s)
    try:
        return float(s)
    except (ValueError, TypeError):
        return None


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
    return parse_snmp_number(raw_value)


async def _make_engine_and_target(imports, host: str):
    """Create SnmpEngine and UdpTransportTarget (shared across all queries)."""
    (
        SnmpEngine, ContextData, UdpTransportTarget, *_rest
    ) = imports
    target = await UdpTransportTarget.create(
        (host, SNMP_PORT), timeout=SNMP_TIMEOUT, retries=SNMP_RETRIES
    )
    engine = await asyncio.get_running_loop().run_in_executor(None, SnmpEngine)
    return engine, target


def _build_auth_data(imports, data: dict):
    """Build pysnmp auth data based on SNMP version."""
    (
        SnmpEngine, ContextData, UdpTransportTarget, ObjectType,
        ObjectIdentity, get_cmd, next_cmd, CommunityData, UsmUserData,
        usmHMACMD5AuthProtocol, usmHMACSHAAuthProtocol,
        usmDESPrivProtocol, usmAesCfb128Protocol,
    ) = imports

    from .const import (
        CONF_SNMP_VERSION, CONF_COMMUNITY, CONF_USERNAME,
        CONF_AUTH_PROTOCOL, CONF_AUTH_PASSWORD,
        CONF_PRIV_PROTOCOL, CONF_PRIV_PASSWORD,
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
    """Async SNMP connectivity test - queries sysUpTime (1.3.6.1.2.1.1.3.0)."""
    imports = _get_snmp_imports()
    (
        SnmpEngine, ContextData, UdpTransportTarget, ObjectType,
        ObjectIdentity, get_cmd, *_rest
    ) = imports

    try:
        host = sanitize_host(data["host"])
        auth_data = _build_auth_data(imports, data)
        engine, target = await _make_engine_and_target(imports, host)

        error_indication, error_status, error_index, _ = await asyncio.wait_for(
            get_cmd(
                engine,
                auth_data,
                target,
                ContextData(),
                ObjectType(ObjectIdentity("1.3.6.1.2.1.1.3.0")),
            ),
            timeout=SNMP_TIMEOUT + 2,
        )
    except SnmpLibraryMissing:
        raise
    except asyncio.TimeoutError as err:
        raise CannotConnect("SNMP connection timed out") from err
    except Exception as err:
        _LOGGER.exception("Unexpected error during SNMP test: %s", err)
        raise CannotConnect(str(err)) from err

    if error_indication:
        _LOGGER.error("SNMP test error_indication: %s", error_indication)
        raise CannotConnect(str(error_indication))
    if error_status:
        _LOGGER.error("SNMP test error_status: %s", error_status)
        raise InvalidAuth(str(error_status))


async def walk_snmp_column(
    engine, auth_data, target, imports, column_oid: str
) -> dict[str, str]:
    """Walk a single SNMP table column; return {row_index: value}.

    Hard-limited to MAX_WALK_ITERATIONS to guard against misbehaving agents.
    """
    (
        SnmpEngine, ContextData, UdpTransportTarget, ObjectType,
        ObjectIdentity, get_cmd, next_cmd, *_rest
    ) = imports

    result: dict[str, str] = {}
    current_oid = column_oid
    iterations = 0

    while iterations < MAX_WALK_ITERATIONS:
        iterations += 1
        try:
            error_indication, error_status, error_index, var_binds = await asyncio.wait_for(
                next_cmd(
                    engine,
                    auth_data,
                    target,
                    ContextData(),
                    ObjectType(ObjectIdentity(current_oid)),
                ),
                timeout=SNMP_TIMEOUT + 2,
            )
        except asyncio.TimeoutError:
            _LOGGER.debug("Walk timeout for OID %s", current_oid)
            break
        except Exception as err:
            _LOGGER.debug("Walk exception for OID %s: %s", current_oid, err)
            break

        if error_indication or error_status:
            _LOGGER.debug(
                "Walk ended for OID %s: %s %s", column_oid, error_indication, error_status
            )
            break

        if not var_binds:
            break

        var_bind = var_binds[0]
        oid_str = str(var_bind[0])
        value_str = str(var_bind[1])

        if not oid_str.startswith(column_oid + "."):
            break

        row_idx = oid_str[len(column_oid) + 1:]
        result[row_idx] = value_str
        current_oid = oid_str

    return result


async def fetch_disk_table(engine, auth_data, target, imports, data: dict) -> list[dict]:
    """Fetch WD disk table dynamically using shared engine/target."""
    from .const import (
        WD_DISK_COL_NUM, WD_DISK_COL_VENDOR, WD_DISK_COL_MODEL,
        WD_DISK_COL_SERIAL, WD_DISK_COL_TEMPERATURE,
        WD_DISK_COL_CAPACITY, WD_DISK_COL_STATUS, DISK_STATUS_MAP,
    )

    indices = await walk_snmp_column(engine, auth_data, target, imports, WD_DISK_COL_NUM)
    if not indices:
        _LOGGER.debug("WD disk table: no disks found via SNMP walk")
        return []

    _LOGGER.debug("WD disk table indices found: %s", list(indices.keys()))

    vendors, models, serials, temps, capacities, statuses = await asyncio.gather(
        walk_snmp_column(engine, auth_data, target, imports, WD_DISK_COL_VENDOR),
        walk_snmp_column(engine, auth_data, target, imports, WD_DISK_COL_MODEL),
        walk_snmp_column(engine, auth_data, target, imports, WD_DISK_COL_SERIAL),
        walk_snmp_column(engine, auth_data, target, imports, WD_DISK_COL_TEMPERATURE),
        walk_snmp_column(engine, auth_data, target, imports, WD_DISK_COL_CAPACITY),
        walk_snmp_column(engine, auth_data, target, imports, WD_DISK_COL_STATUS),
    )

    disks = []
    for idx in sorted(indices.keys(), key=lambda x: int(x) if x.isdigit() else x):
        raw_status = statuses.get(idx, "0")
        disks.append({
            "index":       idx,
            "vendor":      vendors.get(idx, ""),
            "model":       models.get(idx, ""),
            "serial":      serials.get(idx, ""),
            "temperature": parse_wd_temperature(temps.get(idx, "")),
            "capacity":    parse_snmp_number(capacities.get(idx, "")),
            "status":      DISK_STATUS_MAP.get(raw_status, raw_status),
        })
    return disks


async def fetch_volume_table(engine, auth_data, target, imports, data: dict) -> list[dict]:
    """Fetch WD volume/RAID table dynamically using shared engine/target."""
    from .const import (
        WD_VOL_COL_NUM, WD_VOL_COL_NAME, WD_VOL_COL_FSTYPE,
        WD_VOL_COL_RAIDLEVEL, WD_VOL_COL_SIZE, WD_VOL_COL_FREESPACE,
        RAID_LEVEL_MAP,
    )

    indices = await walk_snmp_column(engine, auth_data, target, imports, WD_VOL_COL_NUM)
    if not indices:
        _LOGGER.debug("WD volume table: no volumes found via SNMP walk")
        return []

    _LOGGER.debug("WD volume table indices found: %s", list(indices.keys()))

    names, fstypes, raidlevels, sizes, frees = await asyncio.gather(
        walk_snmp_column(engine, auth_data, target, imports, WD_VOL_COL_NAME),
        walk_snmp_column(engine, auth_data, target, imports, WD_VOL_COL_FSTYPE),
        walk_snmp_column(engine, auth_data, target, imports, WD_VOL_COL_RAIDLEVEL),
        walk_snmp_column(engine, auth_data, target, imports, WD_VOL_COL_SIZE),
        walk_snmp_column(engine, auth_data, target, imports, WD_VOL_COL_FREESPACE),
    )

    volumes = []
    for idx in sorted(indices.keys(), key=lambda x: int(x) if x.isdigit() else x):
        size_mb = parse_snmp_number(sizes.get(idx, ""))
        free_mb = parse_snmp_number(frees.get(idx, ""))
        used_mb = None
        used_pct = None
        if size_mb is not None and free_mb is not None:
            used_mb = round(size_mb - free_mb, 1)
            if size_mb > 0:
                used_pct = round((used_mb / size_mb) * 100, 1)
        raw_raid = raidlevels.get(idx, "")
        volumes.append({
            "index":      idx,
            "name":       names.get(idx, ""),
            "fstype":     fstypes.get(idx, ""),
            "raid_level": RAID_LEVEL_MAP.get(raw_raid, raw_raid),
            "size_mb":    size_mb,
            "free_mb":    free_mb,
            "used_mb":    used_mb,
            "used_pct":   used_pct,
        })
    return volumes


async def fetch_snmp_data(data: dict, sensors: list) -> dict:
    """Fetch all SNMP data. Returns dict keyed by sensor key.

    Reuses a single SnmpEngine and UdpTransportTarget for all queries.
    All scalar OIDs are fetched in parallel via asyncio.gather.
    Disk and volume table columns are fetched in parallel as well.
    """
    imports = _get_snmp_imports()
    (
        SnmpEngine, ContextData, UdpTransportTarget, ObjectType,
        ObjectIdentity, get_cmd, *_rest
    ) = imports

    host = sanitize_host(data["host"])
    auth_data = _build_auth_data(imports, data)

    try:
        engine, target = await _make_engine_and_target(imports, host)
    except Exception as err:
        raise CannotConnect(f"Could not create SNMP transport: {err}") from err

    result: dict = {}
    scalar_sensors = [s for s in sensors if not s.get("computed")]

    async def _fetch_one(sensor: dict):
        oid = sensor["oid"]
        key = sensor["key"]
        transform = sensor.get("transform")
        try:
            error_indication, error_status, error_index, var_binds = await asyncio.wait_for(
                get_cmd(
                    engine, auth_data, target, ContextData(),
                    ObjectType(ObjectIdentity(oid)),
                ),
                timeout=SNMP_TIMEOUT + 2,
            )
        except asyncio.TimeoutError:
            _LOGGER.warning("Timeout fetching OID %s", oid)
            return key, None
        except Exception as err:
            _LOGGER.warning("Exception fetching OID %s: %s", oid, err)
            return key, None

        if error_indication or error_status:
            _LOGGER.warning(
                "SNMP error for OID %s: %s %s", oid, error_indication, error_status
            )
            return key, None

        raw_value = str(var_binds[0][1])
        if key == "system_uptime":
            parsed = parse_snmp_number(raw_value)
            return key, round(parsed / 100, 1) if parsed is not None else None
        if "temperature" in key:
            return key, parse_wd_temperature(raw_value)
        if transform == "kb_to_mib":
            parsed = parse_snmp_number(raw_value)
            return key, round(parsed / 1024, 1) if parsed is not None else None
        parsed = parse_snmp_number(raw_value)
        return key, parsed if parsed is not None else raw_value

    scalar_results = await asyncio.gather(*[_fetch_one(s) for s in scalar_sensors])
    for key, value in scalar_results:
        result[key] = value

    ram_total = result.get("ram_total")
    ram_free = result.get("ram_free")
    if ram_total is not None and ram_free is not None:
        result["ram_used"] = round(ram_total - ram_free, 1)

    disk_result, volume_result = await asyncio.gather(
        fetch_disk_table(engine, auth_data, target, imports, data),
        fetch_volume_table(engine, auth_data, target, imports, data),
        return_exceptions=True,
    )

    if isinstance(disk_result, Exception):
        _LOGGER.warning("Could not fetch WD disk table: %s", disk_result)
        result["_disks"] = []
    else:
        result["_disks"] = disk_result

    if isinstance(volume_result, Exception):
        _LOGGER.warning("Could not fetch WD volume table: %s", volume_result)
        result["_volumes"] = []
    else:
        result["_volumes"] = volume_result

    return result
