"""SNMP helper for WD MyCloud EX2 Ultra integration."""
from __future__ import annotations

import asyncio
import logging
import re
from typing import Any

_LOGGER = logging.getLogger(__name__)

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
    try:
        return round(int(value) * 1024 / 1024 / 1024, 1)
    except (TypeError, ValueError):
        return None


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
        usmHMACMD5AuthProtocol, usmHMACSHAAuthProtocol,
        usmDESPrivProtocol, usmAesCfb128Protocol,
    )

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
