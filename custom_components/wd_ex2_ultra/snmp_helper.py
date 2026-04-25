<<<<<<< HEAD
"""SNMP helper for WD MyCloud EX2 Ultra integration."""
=======
"""Async SNMP helper for WD MyCloud EX2 Ultra.

Uses pysnmp.hlapi.v3arch.asyncio (pysnmp==7.1.22),
the same API as the HA core SNMP integration.
"""
>>>>>>> ec0ae21 (change config...)
from __future__ import annotations

import asyncio
import logging
import re
from typing import Any

_LOGGER = logging.getLogger(__name__)

<<<<<<< HEAD
SNMP_TIMEOUT = 5
SNMP_RETRIES = 1
SNMP_PORT = 161

# ---------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------

class SnmpLibraryMissing(Exception):
    """Raised when pysnmp is not installed."""

class CannotConnect(Exception):
    """Raised when the SNMP agent is unreachable."""

class InvalidAuth(Exception):
    """Raised when SNMP authentication fails."""


# ---------------------------------------------------------------
# Transform helpers
# ---------------------------------------------------------------

def timeticks_to_seconds(value: Any) -> float | None:
    """Convert SNMP TimeTicks (1/100 s) to seconds."""
    try:
        return round(int(value) / 100, 1)
    except (TypeError, ValueError):
        return None


def hrStorage_kb_to_mib(value: Any) -> float | None:
    """Convert hrStorage raw blocks (alloc_unit=1024 bytes) to MiB."""
=======
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


def _safe_float(raw) -> float | None:
    if raw is None:
        return None
    s = re.sub(r"[^\d.\-]", "", str(raw).strip())
>>>>>>> ec0ae21 (change config...)
    try:
        return round(int(value) * 1024 / 1024 / 1024, 1)
    except (TypeError, ValueError):
        return None


<<<<<<< HEAD
def hrStorage_blocks_to_gib(value: Any) -> float | None:
    """Convert hrStorage raw blocks (alloc_unit=512 bytes) to GiB."""
    try:
        return round(int(value) * 512 / (1024 ** 3), 2)
    except (TypeError, ValueError):
        return None


def bps_to_mbit(value: Any) -> str | None:
    """Convert bits/s to a human-readable Mbit/s string."""
    try:
        return f"{int(value) / 1_000_000:.0f} Mbit/s"
    except (TypeError, ValueError):
        return None


def if_oper_status_map(value: Any) -> str | None:
    """Map ifOperStatus integer to a human-readable string."""
    _MAP = {
        1: "up",
        2: "down",
        3: "testing",
        4: "unknown",
        5: "dormant",
        6: "notPresent",
        7: "lowerLayerDown",
    }
    try:
        return _MAP.get(int(value), str(value))
    except (TypeError, ValueError):
        return None


def parse_wd_temperature(value: Any) -> float | None:
    """Parse WD temperature string 'Centigrade:48 Fahrenheit:118' -> 48.0."""
    try:
        match = re.search(r"Centigrade:(\d+)", str(value))
        if match:
            return float(match.group(1))
        return float(value)
    except (TypeError, ValueError):
        return None


def fan_status_map(value: Any) -> str | None:
    """Map WD fan status integer to a human-readable string."""
    _MAP = {"0": "Normal", "1": "Error"}
    try:
        return _MAP.get(str(int(value)), str(value))
    except (TypeError, ValueError):
        return None


TRANSFORMS = {
    "timeticks_to_seconds": timeticks_to_seconds,
    "hrStorage_kb_to_mib": hrStorage_kb_to_mib,
    "hrStorage_blocks_to_gib": hrStorage_blocks_to_gib,
    "bps_to_mbit": bps_to_mbit,
    "if_oper_status_map": if_oper_status_map,
    "parse_wd_temperature": parse_wd_temperature,
    "fan_status_map": fan_status_map,
}


# ---------------------------------------------------------------
# SNMP transport / credential helpers
# ---------------------------------------------------------------

def _build_v2c_params(community: str):
    from pysnmp.hlapi.v3arch.asyncio import CommunityData, UdpTransportTarget, SnmpEngine
    return CommunityData(community, mpModel=1)


def _build_v3_params(username: str, auth_protocol: str, auth_password: str,
                     priv_protocol: str, priv_password: str):
    from pysnmp.hlapi.v3arch.asyncio import UsmUserData
    from pysnmp.hlapi.v3arch.asyncio import (
=======
# ---------------------------------------------------------------------------
# Transform functions (one per transform key used in SENSORS / disk / volume)
# ---------------------------------------------------------------------------

def _tf_timeticks_to_seconds(raw: str) -> float | None:
    v = _safe_float(raw)
    return round(v / 100, 1) if v is not None else None


def _tf_hr_1k_blocks_to_mib(raw: str) -> float | None:
    """hrStorageSize/Used with alloc_unit=1024 B → MiB."""
    v = _safe_float(raw)
    # raw value is in 1-KiB blocks → divide by 1024 to get MiB
    return round(v / 1024, 1) if v is not None else None


def _tf_hr_512b_blocks_to_gib(raw: str) -> float | None:
    """hrStorageSize/Used with alloc_unit=512 B → GiB."""
    v = _safe_float(raw)
    return round(v * 512 / 1024 ** 3, 2) if v is not None else None


def _tf_bps_to_mbit(raw: str) -> float | None:
    v = _safe_float(raw)
    return round(v / 1_000_000, 0) if v is not None else None


def _tf_if_oper_status(raw: str) -> str:
    from .const import IF_OPER_STATUS_MAP
    return IF_OPER_STATUS_MAP.get(str(raw).strip(), raw)


def _tf_fan_status(raw: str) -> str:
    from .const import FAN_STATUS_MAP
    return FAN_STATUS_MAP.get(str(raw).strip(), raw)


def _tf_wd_temperature(raw: str) -> float | None:
    """Parse 'Centigrade:48 Fahrenheit:118' → 48.0."""
    if not raw or not isinstance(raw, str):
        return None
    m = re.search(r"Centigrade:\s*(\d+)", raw)
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            pass
    return _safe_float(raw)


_TRANSFORMS = {
    "timeticks_to_seconds":  _tf_timeticks_to_seconds,
    "hr_1k_blocks_to_mib":   _tf_hr_1k_blocks_to_mib,
    "hr_512b_blocks_to_gib": _tf_hr_512b_blocks_to_gib,
    "bps_to_mbit":           _tf_bps_to_mbit,
    "if_oper_status_map":    _tf_if_oper_status,
    "fan_status_map":        _tf_fan_status,
    "wd_temperature":        _tf_wd_temperature,
}


def _apply_transform(key: str | None, raw: str):
    if key and key in _TRANSFORMS:
        return _TRANSFORMS[key](raw)
    v = _safe_float(raw)
    return v if v is not None else raw


# ---------------------------------------------------------------------------
# SNMP engine / target / auth builders
# ---------------------------------------------------------------------------

def _build_auth_data(imports, data: dict):
    (
        SnmpEngine, ContextData, UdpTransportTarget,
        ObjectType, ObjectIdentity,
        get_cmd, next_cmd,
        CommunityData, UsmUserData,
>>>>>>> ec0ae21 (change config...)
        usmHMACMD5AuthProtocol, usmHMACSHAAuthProtocol,
        usmDESPrivProtocol, usmAesCfb128Protocol,
    )

<<<<<<< HEAD
    auth_proto = (
        usmHMACSHAAuthProtocol if auth_protocol.upper() == "SHA"
        else usmHMACMD5AuthProtocol
    )
    priv_proto = (
        usmAesCfb128Protocol if priv_protocol.upper() == "AES"
        else usmDESPrivProtocol
    )
    return UsmUserData(
        username,
        authKey=auth_password,
        privKey=priv_password,
        authProtocol=auth_proto,
        privProtocol=priv_proto,
    )


async def _snmp_get_one(engine, auth_data, transport, oid_str: str) -> Any:
    """Perform a single SNMP GET and return the raw value (or None on error)."""
    from pysnmp.hlapi.v3arch.asyncio import get_cmd, ObjectType, ObjectIdentity

    try:
        error_indication, error_status, error_index, var_binds = await get_cmd(
            engine,
            auth_data,
            transport,
            ObjectType(ObjectIdentity(oid_str)),
        )

        if error_indication:
            _LOGGER.debug("SNMP GET %s: %s", oid_str, error_indication)
            return None
        if error_status:
            _LOGGER.debug("SNMP GET %s error status: %s", oid_str, error_status)
            return None

        for var_bind in var_binds:
            return var_bind[1]

    except Exception as exc:  # noqa: BLE001
        _LOGGER.debug("SNMP GET %s exception: %s", oid_str, exc)
        return None


async def snmp_get_all(
    host: str,
    snmp_version: str,
    community: str | None,
    username: str | None,
    auth_protocol: str | None,
    auth_password: str | None,
    priv_protocol: str | None,
    priv_password: str | None,
    oid_list: list[str],
) -> dict[str, Any]:
    """Fetch all scalar OIDs in parallel with asyncio.gather()."""
    try:
        from pysnmp.hlapi.v3arch.asyncio import SnmpEngine, UdpTransportTarget, ContextData
    except ImportError as exc:
        raise SnmpLibraryMissing("pysnmp is not installed") from exc

    engine = SnmpEngine()
    try:
        transport = await UdpTransportTarget.create(
            (host, SNMP_PORT),
            timeout=SNMP_TIMEOUT,
            retries=SNMP_RETRIES,
        )
    except Exception as exc:
        raise CannotConnect(f"Cannot connect to {host}") from exc

    if snmp_version == "SNMPv3":
        if not username:
            raise InvalidAuth("SNMPv3 requires a username")
        auth_data = _build_v3_params(
            username, auth_protocol or "MD5", auth_password or "",
            priv_protocol or "DES", priv_password or "",
        )
    else:
        auth_data = _build_v2c_params(community or "public")

    tasks = [_snmp_get_one(engine, auth_data, transport, oid) for oid in oid_list]
    results_list = await asyncio.gather(*tasks, return_exceptions=True)

    results: dict[str, Any] = {}
    for oid, result in zip(oid_list, results_list):
        if isinstance(result, Exception):
            _LOGGER.debug("SNMP gather error for %s: %s", oid, result)
            results[oid] = None
        else:
            results[oid] = result

    return results


async def snmp_walk(
    host: str,
    snmp_version: str,
    community: str | None,
    username: str | None,
    auth_protocol: str | None,
    auth_password: str | None,
    priv_protocol: str | None,
    priv_password: str | None,
    base_oid: str,
) -> list[tuple[str, Any]]:
    """Perform an SNMP walk under base_oid and return (oid_str, value) pairs."""
    try:
        from pysnmp.hlapi.v3arch.asyncio import (
            SnmpEngine, UdpTransportTarget, ContextData,
            ObjectType, ObjectIdentity, bulk_walk_cmd,
        )
    except ImportError as exc:
        raise SnmpLibraryMissing("pysnmp is not installed") from exc

    engine = SnmpEngine()
    try:
        transport = await UdpTransportTarget.create(
            (host, SNMP_PORT),
            timeout=SNMP_TIMEOUT,
            retries=SNMP_RETRIES,
        )
    except Exception as exc:
        raise CannotConnect(f"Cannot connect to {host}") from exc

    if snmp_version == "SNMPv3":
        if not username:
            raise InvalidAuth("SNMPv3 requires a username")
        auth_data = _build_v3_params(
            username, auth_protocol or "MD5", auth_password or "",
            priv_protocol or "DES", priv_password or "",
        )
    else:
        auth_data = _build_v2c_params(community or "public")

    rows: list[tuple[str, Any]] = []
    try:
        async for error_indication, error_status, error_index, var_binds in bulk_walk_cmd(
            engine,
            auth_data,
            transport,
            ObjectType(ObjectIdentity(base_oid)),
            lexicographicMode=False,
        ):
            if error_indication:
                _LOGGER.debug("SNMP walk %s: %s", base_oid, error_indication)
                break
            if error_status:
                _LOGGER.debug("SNMP walk %s error: %s", base_oid, error_status)
                break
            for var_bind in var_binds:
                rows.append((str(var_bind[0]), var_bind[1]))
    except Exception as exc:  # noqa: BLE001
        _LOGGER.debug("SNMP walk exception for %s: %s", base_oid, exc)

    return rows


async def fetch_disk_table(
    host: str, snmp_version: str, community: str | None,
    username: str | None, auth_protocol: str | None, auth_password: str | None,
    priv_protocol: str | None, priv_password: str | None,
) -> list[dict[str, Any]]:
    """Walk the WD disk table and return a list of disk dicts."""
    from .const import (
        WD_DISK_TABLE_ROOT, WD_DISK_COL_VENDOR, WD_DISK_COL_MODEL,
        WD_DISK_COL_TEMPERATURE, WD_DISK_COL_CAPACITY, WD_DISK_COL_STATUS,
        DISK_STATUS_MAP,
    )

    kwargs = dict(
        host=host, snmp_version=snmp_version, community=community,
        username=username, auth_protocol=auth_protocol, auth_password=auth_password,
        priv_protocol=priv_protocol, priv_password=priv_password,
    )

    rows = await snmp_walk(**kwargs, base_oid=WD_DISK_TABLE_ROOT)

    # Group by row index (last OID component)
    disks: dict[str, dict] = {}
    for oid_str, value in rows:
        parts = oid_str.split(".")
        col_prefix = ".".join(parts[:-1])
        idx = parts[-1]
        disks.setdefault(idx, {})

        raw = str(value)
        if col_prefix.endswith(".10.1.2"):
            disks[idx]["vendor"] = raw
        elif col_prefix.endswith(".10.1.3"):
            disks[idx]["model"] = raw
        elif col_prefix.endswith(".10.1.5"):
            try:
                disks[idx]["temperature"] = float(raw)
            except ValueError:
                disks[idx]["temperature"] = None
        elif col_prefix.endswith(".10.1.6"):
            try:
                disks[idx]["capacity_gb"] = round(int(raw) / 1000, 1)
            except ValueError:
                disks[idx]["capacity_gb"] = None
        elif col_prefix.endswith(".10.1.7"):
            disks[idx]["health"] = DISK_STATUS_MAP.get(raw, raw)

    return [{
        "index": idx,
        "vendor": d.get("vendor", ""),
        "model": d.get("model", ""),
        "temperature": d.get("temperature"),
        "capacity_gb": d.get("capacity_gb"),
        "health": d.get("health", "Unknown"),
    } for idx, d in sorted(disks.items())]


async def fetch_volume_table(
    host: str, snmp_version: str, community: str | None,
    username: str | None, auth_protocol: str | None, auth_password: str | None,
    priv_protocol: str | None, priv_password: str | None,
) -> list[dict[str, Any]]:
    """Walk the WD volume table and return a list of volume dicts."""
    from .const import WD_VOL_TABLE_ROOT, WD_VOL_COL_NAME, RAID_LEVEL_MAP

    kwargs = dict(
        host=host, snmp_version=snmp_version, community=community,
        username=username, auth_protocol=auth_protocol, auth_password=auth_password,
        priv_protocol=priv_protocol, priv_password=priv_password,
    )

    rows = await snmp_walk(**kwargs, base_oid=WD_VOL_TABLE_ROOT)

    volumes: dict[str, dict] = {}
    for oid_str, value in rows:
        parts = oid_str.split(".")
        col_prefix = ".".join(parts[:-1])
        idx = parts[-1]
        volumes.setdefault(idx, {})

        raw = str(value)
        if col_prefix.endswith(".9.1.2"):
            volumes[idx]["name"] = raw
        elif col_prefix.endswith(".9.1.4"):
            volumes[idx]["raid_level"] = RAID_LEVEL_MAP.get(raw, raw)
        elif col_prefix.endswith(".9.1.5"):
            try:
                kb = int(raw)
                volumes[idx]["total_gib"] = round(kb / 1024 / 1024, 2)
            except ValueError:
                volumes[idx]["total_gib"] = None
        elif col_prefix.endswith(".9.1.6"):
            try:
                kb = int(raw)
                free_gib = round(kb / 1024 / 1024, 2)
                volumes[idx]["free_gib"] = free_gib
            except ValueError:
                volumes[idx]["free_gib"] = None

    # Calculate derived fields
    result = []
    for idx, v in sorted(volumes.items()):
        total = v.get("total_gib")
        free = v.get("free_gib")
        used = round(total - free, 2) if total is not None and free is not None else None
        used_pct = round((used / total) * 100, 1) if total and used is not None else None
        result.append({
            "index": idx,
            "name": v.get("name", f"Volume {idx}"),
            "raid_level": v.get("raid_level", "Unknown"),
            "total_gib": total,
            "free_gib": free,
            "used_gib": used,
            "used_pct": used_pct,
        })
    return result
=======
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


async def _make_engine_and_target(imports, host: str):
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
    engine, auth_data, target, imports, column_oid: str
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

async def fetch_disk_table(engine, auth_data, target, imports, _data: dict) -> list[dict]:
    """Fetch WD disk table. Capacity value is in MB → convert to GB."""
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
        raw_cap = _safe_float(caps.get(idx, ""))
        disks.append({
            "index":       idx,
            "vendor":      vendors.get(idx, ""),
            "model":       models.get(idx, ""),
            "serial":      serials.get(idx, ""),
            "temperature": _tf_wd_temperature(temps.get(idx, "")),
            "capacity":    round(raw_cap / 1000, 2) if raw_cap is not None else None,
            "status":      DISK_STATUS_MAP.get(statuses.get(idx, "0"), statuses.get(idx, "0")),
        })
    return disks


# ---------------------------------------------------------------------------
# Dynamic volume table
# ---------------------------------------------------------------------------

async def fetch_volume_table(engine, auth_data, target, imports, _data: dict) -> list[dict]:
    """Fetch WD volume/RAID table. Size/free in KB → convert to GiB."""
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
        raw_size = _safe_float(sizes.get(idx, ""))
        raw_free = _safe_float(frees.get(idx, ""))
        size_gib = round(raw_size / 1024 / 1024, 2) if raw_size is not None else None
        free_gib = round(raw_free / 1024 / 1024, 2) if raw_free is not None else None
        used_gib = round(size_gib - free_gib, 2) if (size_gib and free_gib is not None) else None
        used_pct = round(used_gib / size_gib * 100, 1) if (used_gib is not None and size_gib) else None
        volumes.append({
            "index":      idx,
            "name":       names.get(idx, ""),
            "fstype":     fstypes.get(idx, ""),
            "raid_level": RAID_LEVEL_MAP.get(raids.get(idx, ""), raids.get(idx, "")),
            "size_gib":   size_gib,
            "free_gib":   free_gib,
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

    async def _fetch_one(sensor: dict):
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

    # Fetch all scalar sensors in parallel
    scalar_sensors = [s for s in sensors if not s.get("computed")]
    results = await asyncio.gather(*[_fetch_one(s) for s in scalar_sensors])
    result: dict = {k: v for k, v in results}

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
>>>>>>> ec0ae21 (change config...)
