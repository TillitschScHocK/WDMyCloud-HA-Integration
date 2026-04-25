"""Async SNMP helper for WD MyCloud EX2 Ultra.

Uses pysnmp.hlapi.v3arch.asyncio (pysnmp>=7.1.22),
the same API as the HA core SNMP integration.
"""
from __future__ import annotations

import asyncio
import logging
import re
from typing import Any

from homeassistant.exceptions import HomeAssistantError

from .const import (
    CONF_SNMP_VERSION, CONF_COMMUNITY, CONF_USERNAME,
    CONF_AUTH_PROTOCOL, CONF_AUTH_PASSWORD,
    CONF_PRIV_PROTOCOL, CONF_PRIV_PASSWORD,
    SNMP_VERSION_V2C, RAID_LEVEL_MAP,
)

_LOGGER = logging.getLogger(__name__)

SNMP_TIMEOUT      = 5
SNMP_RETRIES      = 1
SNMP_PORT         = 161
MAX_WALK_ITERS    = 100


# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------

class CannotConnect(HomeAssistantError):
    """Cannot reach the device via SNMP."""

class InvalidAuth(HomeAssistantError):
    """SNMP credentials are invalid."""

class SnmpLibraryMissing(HomeAssistantError):
    """pysnmp is not installed or incompatible."""


# ---------------------------------------------------------------------------
# pysnmp lazy import
# ---------------------------------------------------------------------------

def _get_snmp_imports():
    try:
        from pysnmp.hlapi.v3arch.asyncio import (
            SnmpEngine, ContextData, UdpTransportTarget,
            ObjectType, ObjectIdentity,
            get_cmd, next_cmd,
            CommunityData, UsmUserData,
            usmHMACMD5AuthProtocol, usmHMACSHAAuthProtocol,
            usmDESPrivProtocol, usmAesCfb128Protocol,
        )
        return (
            SnmpEngine, ContextData, UdpTransportTarget,
            ObjectType, ObjectIdentity,
            get_cmd, next_cmd,
            CommunityData, UsmUserData,
            usmHMACMD5AuthProtocol, usmHMACSHAAuthProtocol,
            usmDESPrivProtocol, usmAesCfb128Protocol,
        )
    except ImportError as err:
        raise SnmpLibraryMissing(
            "pysnmp 7.1.22 is not installed. Restart Home Assistant after HACS installation."
        ) from err


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def sanitize_host(host: str) -> str:
    """Strip http(s):// and trailing slashes."""
    host = host.strip()
    host = re.sub(r"^https?://", "", host)
    return host.rstrip("/")


def _safe_float(raw: Any) -> float | None:
    if raw is None:
        return None
    s = re.sub(r"[^\d.\-]", "", str(raw).strip())
    try:
        return float(s)
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Transform functions
# ---------------------------------------------------------------------------

def _tf_timeticks_to_seconds(raw: str) -> float | None:
    v = _safe_float(raw)
    return round(v / 100, 1) if v is not None else None


def _tf_hr_1k_blocks_to_mib(raw: str) -> float | None:
    """hrStorageSize/Used with alloc_unit=1024 B -> MiB."""
    v = _safe_float(raw)
    return round(v / 1024, 1) if v is not None else None


def _tf_hr_512b_blocks_to_gib(raw: str) -> float | None:
    """hrStorageSize/Used with alloc_unit=512 B -> GiB."""
    v = _safe_float(raw)
    return round(v * 512 / 1024 ** 3, 2) if v is not None else None


def _tf_bps_to_mbit(raw: str) -> float | None:
    v = _safe_float(raw)
    return round(v / 1_000_000, 1) if v is not None else None


def _tf_if_oper_status(raw: str) -> str:
    from .const import IF_OPER_STATUS_MAP
    return IF_OPER_STATUS_MAP.get(str(raw).strip(), raw)


def _tf_fan_status_string(raw: str) -> str:
    """Parse WD fan status string.

    Raw value example: 'fan0: stop '
    -> 'stop' in string means fan is stopped -> return 'Stopped'
    -> anything else (running, spin up, ...) -> return 'Running'
    """
    s = str(raw).lower().strip()
    if "stop" in s:
        return "Stopped"
    return "Running"


def _tf_wd_temperature(raw: str) -> float | None:
    """Parse 'Centigrade:48 Fahrenheit:118' or 'Centigrade:34' -> 48.0."""
    if not raw:
        return None
    raw_s = str(raw)
    m = re.search(r"[Cc]entigrade:\s*(\d+(?:\.\d+)?)", raw_s)
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            pass
    return _safe_float(raw_s)


def _tf_wd_size_string_to_gib(raw: str) -> float | None:
    """Convert WD size strings to GiB.

    Examples:
      '3.6T'    -> 3.6 * 1024        = 3686.4  GiB
      '974.4G'  -> 974.4             GiB
      '500M'    -> 500 / 1024        GiB
      '1.5TB'   -> 1.5 * 1024        GiB
      '4000 GB.'-> 4000.0            GB  (used for display, not this fn)
    """
    if not raw:
        return None
    s = str(raw).strip()
    # Match optional decimal number followed by optional space and unit
    m = re.match(r"([\d.]+)\s*([TGMK]i?B?)", s, re.IGNORECASE)
    if not m:
        return _safe_float(s)
    value = float(m.group(1))
    unit  = m.group(2).upper().rstrip("B").rstrip("I")
    if unit in ("T", "TB"):
        return round(value * 1024, 2)
    if unit in ("G", "GB"):
        return round(value, 2)
    if unit in ("M", "MB"):
        return round(value / 1024, 2)
    if unit in ("K", "KB"):
        return round(value / 1024 / 1024, 2)
    return round(value, 2)


def _tf_wd_disk_capacity_gb(raw: str) -> float | None:
    """Parse WD disk capacity string like '4000 GB.' -> 4000.0 (GB)."""
    if not raw:
        return None
    # Strip everything except digits and decimal point
    s = re.sub(r"[^\d.]", "", str(raw).strip())
    try:
        return float(s)
    except ValueError:
        return None


def _tf_wd_raid_level_map(raw: str) -> str:
    """Map RAID level integer string to human-readable label."""
    return RAID_LEVEL_MAP.get(str(raw).strip(), str(raw).strip())


_TRANSFORMS = {
    "timeticks_to_seconds":  _tf_timeticks_to_seconds,
    "hr_1k_blocks_to_mib":   _tf_hr_1k_blocks_to_mib,
    "hr_512b_blocks_to_gib": _tf_hr_512b_blocks_to_gib,
    "bps_to_mbit":           _tf_bps_to_mbit,
    "if_oper_status_map":    _tf_if_oper_status,
    "fan_status_string":     _tf_fan_status_string,
    "wd_temperature":        _tf_wd_temperature,
    "wd_size_string_to_gib": _tf_wd_size_string_to_gib,
    "wd_disk_capacity_gb":   _tf_wd_disk_capacity_gb,
    "wd_raid_level_map":     _tf_wd_raid_level_map,
}


def _apply_transform(key: str | None, raw: str) -> Any:
    if key and key in _TRANSFORMS:
        return _TRANSFORMS[key](raw)
    v = _safe_float(raw)
    return v if v is not None else raw


# ---------------------------------------------------------------------------
# SNMP engine / target / auth builders
# ---------------------------------------------------------------------------

def _build_auth_data(imports: tuple, data: dict) -> Any:
    (
        SnmpEngine, ContextData, UdpTransportTarget,
        ObjectType, ObjectIdentity,
        get_cmd, next_cmd,
        CommunityData, UsmUserData,
        usmHMACMD5AuthProtocol, usmHMACSHAAuthProtocol,
        usmDESPrivProtocol, usmAesCfb128Protocol,
    ) = imports

    if data.get(CONF_SNMP_VERSION, SNMP_VERSION_V2C) == SNMP_VERSION_V2C:
        return CommunityData(data.get(CONF_COMMUNITY, "public"), mpModel=1)

    return UsmUserData(
        data[CONF_USERNAME],
        authKey=data.get(CONF_AUTH_PASSWORD, ""),
        privKey=data.get(CONF_PRIV_PASSWORD, ""),
        authProtocol={
            "MD5": usmHMACMD5AuthProtocol,
            "SHA": usmHMACSHAAuthProtocol,
        }.get(data.get(CONF_AUTH_PROTOCOL, "MD5"), usmHMACMD5AuthProtocol),
        privProtocol={
            "DES": usmDESPrivProtocol,
            "AES": usmAesCfb128Protocol,
        }.get(data.get(CONF_PRIV_PROTOCOL, "DES"), usmDESPrivProtocol),
    )


async def _make_engine_and_target(imports: tuple, host: str) -> tuple:
    SnmpEngine, ContextData, UdpTransportTarget, *_ = imports
    target = await UdpTransportTarget.create(
        (host, SNMP_PORT), timeout=SNMP_TIMEOUT, retries=SNMP_RETRIES
    )
    return SnmpEngine(), target


# ---------------------------------------------------------------------------
# SNMP connectivity test
# ---------------------------------------------------------------------------

async def test_snmp_connection(data: dict) -> None:
    """Test connectivity by reading sysUpTimeInstance."""
    imports = _get_snmp_imports()
    SnmpEngine, ContextData, UdpTransportTarget, ObjectType, ObjectIdentity, get_cmd, *_ = imports

    host = sanitize_host(data["host"])
    auth_data = _build_auth_data(imports, data)

    try:
        engine, target = await _make_engine_and_target(imports, host)
        err_ind, err_status, _, _ = await asyncio.wait_for(
            get_cmd(
                engine, auth_data, target, ContextData(),
                ObjectType(ObjectIdentity("1.3.6.1.2.1.1.3.0")),
            ),
            timeout=SNMP_TIMEOUT + 2,
        )
    except SnmpLibraryMissing:
        raise
    except asyncio.TimeoutError as exc:
        raise CannotConnect("SNMP connection timed out") from exc
    except Exception as exc:
        raise CannotConnect(str(exc)) from exc

    if err_ind:
        raise CannotConnect(str(err_ind))
    if err_status:
        raise InvalidAuth(str(err_status))


# ---------------------------------------------------------------------------
# SNMP table walk helper
# ---------------------------------------------------------------------------

async def walk_snmp_column(
    engine: Any, auth_data: Any, target: Any, imports: tuple, column_oid: str
) -> dict[str, str]:
    """Walk one SNMP table column; return {row_index: value_string}."""
    _, ContextData, _, ObjectType, ObjectIdentity, _, next_cmd, *_ = imports

    result: dict[str, str] = {}
    current_oid = column_oid

    for _ in range(MAX_WALK_ITERS):
        try:
            err_ind, err_status, _, var_binds = await asyncio.wait_for(
                next_cmd(
                    engine, auth_data, target, ContextData(),
                    ObjectType(ObjectIdentity(current_oid)),
                ),
                timeout=SNMP_TIMEOUT + 2,
            )
        except Exception as exc:
            _LOGGER.debug("Walk error for %s: %s", current_oid, exc)
            break

        if err_ind or err_status or not var_binds:
            break

        oid_str = str(var_binds[0][0])
        val_str = str(var_binds[0][1])

        if not oid_str.startswith(column_oid + "."):
            break

        result[oid_str[len(column_oid) + 1:]] = val_str
        current_oid = oid_str

    return result


# ---------------------------------------------------------------------------
# Dynamic disk table
# ---------------------------------------------------------------------------

async def fetch_disk_table(
    engine: Any, auth_data: Any, target: Any, imports: tuple, _data: dict
) -> list[dict]:
    """Fetch WD disk table.

    Capacity raw value: '4000 GB.' -> parse to float GB, store as GB.
    Temperature raw value: 'Centigrade:34' -> extract integer.
    Status raw value: '0' -> map via DISK_STATUS_MAP.
    """
    from .const import (
        WD_DISK_COL_NUM, WD_DISK_COL_VENDOR, WD_DISK_COL_MODEL,
        WD_DISK_COL_SERIAL, WD_DISK_COL_TEMPERATURE,
        WD_DISK_COL_CAPACITY, WD_DISK_COL_STATUS, DISK_STATUS_MAP,
    )

    indices = await walk_snmp_column(engine, auth_data, target, imports, WD_DISK_COL_NUM)
    if not indices:
        return []

    vendors, models, serials, temps, caps, statuses = await asyncio.gather(
        walk_snmp_column(engine, auth_data, target, imports, WD_DISK_COL_VENDOR),
        walk_snmp_column(engine, auth_data, target, imports, WD_DISK_COL_MODEL),
        walk_snmp_column(engine, auth_data, target, imports, WD_DISK_COL_SERIAL),
        walk_snmp_column(engine, auth_data, target, imports, WD_DISK_COL_TEMPERATURE),
        walk_snmp_column(engine, auth_data, target, imports, WD_DISK_COL_CAPACITY),
        walk_snmp_column(engine, auth_data, target, imports, WD_DISK_COL_STATUS),
    )

    disks = []
    for idx in sorted(indices, key=lambda x: int(x) if x.isdigit() else x):
        # Capacity: '4000 GB.' -> 4000.0 GB (stored as GB, displayed as TB in sensor.py)
        cap_gb = _tf_wd_disk_capacity_gb(caps.get(idx, ""))
        disks.append({
            "index":       idx,
            "vendor":      vendors.get(idx, ""),
            "model":       models.get(idx, ""),
            "serial":      serials.get(idx, ""),
            "temperature": _tf_wd_temperature(temps.get(idx, "")),
            "capacity_gb": cap_gb,
            "status":      DISK_STATUS_MAP.get(statuses.get(idx, "0"), statuses.get(idx, "0")),
        })
    return disks


# ---------------------------------------------------------------------------
# Dynamic volume table (walk - kept for completeness, not used for main sensors)
# ---------------------------------------------------------------------------

async def fetch_volume_table(
    engine: Any, auth_data: Any, target: Any, imports: tuple, _data: dict
) -> list[dict]:
    """Fetch WD volume/RAID table via walk (not used for main volume sensors)."""
    from .const import (
        WD_VOL_COL_NUM, WD_VOL_COL_NAME, WD_VOL_COL_FSTYPE,
        WD_VOL_COL_RAIDLEVEL, WD_VOL_COL_SIZE, WD_VOL_COL_FREESPACE,
        RAID_LEVEL_MAP,
    )

    indices = await walk_snmp_column(engine, auth_data, target, imports, WD_VOL_COL_NUM)
    if not indices:
        return []

    names, fstypes, raids, sizes, frees = await asyncio.gather(
        walk_snmp_column(engine, auth_data, target, imports, WD_VOL_COL_NAME),
        walk_snmp_column(engine, auth_data, target, imports, WD_VOL_COL_FSTYPE),
        walk_snmp_column(engine, auth_data, target, imports, WD_VOL_COL_RAIDLEVEL),
        walk_snmp_column(engine, auth_data, target, imports, WD_VOL_COL_SIZE),
        walk_snmp_column(engine, auth_data, target, imports, WD_VOL_COL_FREESPACE),
    )

    volumes = []
    for idx in sorted(indices, key=lambda x: int(x) if x.isdigit() else x):
        raw_size = _tf_wd_size_string_to_gib(sizes.get(idx, ""))
        raw_free = _tf_wd_size_string_to_gib(frees.get(idx, ""))
        used_gib = round(raw_size - raw_free, 2) if (raw_size is not None and raw_free is not None) else None
        used_pct = round(used_gib / raw_size * 100, 1) if (used_gib is not None and raw_size) else None
        volumes.append({
            "index":      idx,
            "name":       names.get(idx, ""),
            "fstype":     fstypes.get(idx, ""),
            "raid_level": RAID_LEVEL_MAP.get(raids.get(idx, ""), raids.get(idx, "")),
            "size_gib":   raw_size,
            "free_gib":   raw_free,
            "used_gib":   used_gib,
            "used_pct":   used_pct,
        })
    return volumes


# ---------------------------------------------------------------------------
# Main fetch entry point
# ---------------------------------------------------------------------------

async def fetch_snmp_data(data: dict, sensors: list) -> dict:
    """Fetch all SNMP data in parallel; return dict keyed by sensor key.

    One SnmpEngine + UdpTransportTarget is reused for every query in this
    update cycle to minimise overhead.
    """
    imports = _get_snmp_imports()
    SnmpEngine, ContextData, UdpTransportTarget, ObjectType, ObjectIdentity, get_cmd, *_ = imports

    host      = sanitize_host(data["host"])
    auth_data = _build_auth_data(imports, data)

    try:
        engine, target = await _make_engine_and_target(imports, host)
    except Exception as exc:
        raise CannotConnect(f"Could not create SNMP transport: {exc}") from exc

    async def _fetch_one(sensor: dict) -> tuple[str, Any]:
        oid       = sensor["oid"]
        key       = sensor["key"]
        transform = sensor.get("transform")
        try:
            err_ind, err_status, _, var_binds = await asyncio.wait_for(
                get_cmd(
                    engine, auth_data, target, ContextData(),
                    ObjectType(ObjectIdentity(oid)),
                ),
                timeout=SNMP_TIMEOUT + 2,
            )
        except asyncio.TimeoutError:
            _LOGGER.warning("Timeout fetching OID %s (%s)", oid, key)
            return key, None
        except Exception as exc:
            _LOGGER.warning("Exception fetching OID %s (%s): %s", oid, key, exc)
            return key, None

        if err_ind or err_status:
            _LOGGER.warning("SNMP error for OID %s (%s): %s %s", oid, key, err_ind, err_status)
            return key, None

        raw = str(var_binds[0][1])
        return key, _apply_transform(transform, raw)

    # Fetch all scalar sensors that have an OID (skip computed)
    scalar_sensors = [s for s in sensors if s.get("oid") and not s.get("computed")]
    results = await asyncio.gather(*[_fetch_one(s) for s in scalar_sensors])
    result: dict = {k: v for k, v in results}

    # Compute derived WD volume values from already-fetched data
    total_gib = result.get("volume_total_wd")
    free_gib  = result.get("volume_free_wd")
    if total_gib is not None and free_gib is not None:
        used_gib = round(total_gib - free_gib, 2)
        result["volume_used_wd"]         = used_gib
        result["volume_used_percent_wd"] = round(used_gib / total_gib * 100, 1) if total_gib else None
    else:
        result["volume_used_wd"]         = None
        result["volume_used_percent_wd"] = None

    # Dynamic tables in parallel
    disk_res, vol_res = await asyncio.gather(
        fetch_disk_table(engine, auth_data, target, imports, data),
        fetch_volume_table(engine, auth_data, target, imports, data),
        return_exceptions=True,
    )

    result["_disks"]   = [] if isinstance(disk_res, Exception) else disk_res
    result["_volumes"] = [] if isinstance(vol_res, Exception) else vol_res

    if isinstance(disk_res, Exception):
        _LOGGER.warning("Disk table fetch failed: %s", disk_res)
    if isinstance(vol_res, Exception):
        _LOGGER.warning("Volume table fetch failed: %s", vol_res)

    return result
