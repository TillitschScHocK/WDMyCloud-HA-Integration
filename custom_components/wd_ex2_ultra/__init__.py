"""The WD MyCloud EX2 Ultra integration."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

<<<<<<< HEAD
from .const import (
    DOMAIN,
    DEFAULT_SCAN_INTERVAL,
    CONF_HOST,
    CONF_SNMP_VERSION,
    CONF_COMMUNITY,
    CONF_USERNAME,
    CONF_AUTH_PROTOCOL,
    CONF_AUTH_PASSWORD,
    CONF_PRIV_PROTOCOL,
    CONF_PRIV_PASSWORD,
    CONF_SCAN_INTERVAL,
    SENSORS,
)
from .snmp_helper import (
    snmp_get_all,
    fetch_disk_table,
    fetch_volume_table,
    SnmpLibraryMissing,
    CannotConnect,
    InvalidAuth,
    TRANSFORMS,
)
=======
from .const import DOMAIN, CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL, SENSORS
from .snmp_helper import fetch_snmp_data, CannotConnect, SnmpLibraryMissing
>>>>>>> ec0ae21 (change config...)

_LOGGER = logging.getLogger(__name__)
PLATFORMS = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
<<<<<<< HEAD
    """Set up WD MyCloud EX2 Ultra from a config entry."""
    host = entry.data[CONF_HOST]
    snmp_version = entry.data[CONF_SNMP_VERSION]
    community = entry.data.get(CONF_COMMUNITY)
    username = entry.data.get(CONF_USERNAME)
    auth_protocol = entry.data.get(CONF_AUTH_PROTOCOL)
    auth_password = entry.data.get(CONF_AUTH_PASSWORD)
    priv_protocol = entry.data.get(CONF_PRIV_PROTOCOL)
    priv_password = entry.data.get(CONF_PRIV_PASSWORD)
    scan_interval = entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
=======
    """Set up WD EX2 Ultra from a config entry."""
    scan_interval = entry.options.get(
        CONF_SCAN_INTERVAL,
        entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
    )
>>>>>>> ec0ae21 (change config...)

    oid_list = [s["oid"] for s in SENSORS if s.get("oid")]

    async def _async_update_data() -> dict:
        try:
            scalar_data = await snmp_get_all(
                host=host,
                snmp_version=snmp_version,
                community=community,
                username=username,
                auth_protocol=auth_protocol,
                auth_password=auth_password,
                priv_protocol=priv_protocol,
                priv_password=priv_password,
                oid_list=oid_list,
            )

            # Apply transforms to scalar data
            processed: dict = {}
            for sensor in SENSORS:
                oid = sensor.get("oid")
                if not oid:
                    continue
                raw = scalar_data.get(oid)
                transform_key = sensor.get("transform")
                if transform_key and raw is not None:
                    transform_fn = TRANSFORMS.get(transform_key)
                    processed[sensor["key"]] = transform_fn(raw) if transform_fn else raw
                else:
                    try:
                        processed[sensor["key"]] = float(raw) if raw is not None else None
                    except (TypeError, ValueError):
                        processed[sensor["key"]] = str(raw) if raw is not None else None

            # Dynamic tables
            walk_kwargs = dict(
                host=host, snmp_version=snmp_version, community=community,
                username=username, auth_protocol=auth_protocol,
                auth_password=auth_password, priv_protocol=priv_protocol,
                priv_password=priv_password,
            )
            disks = await fetch_disk_table(**walk_kwargs)
            volumes = await fetch_volume_table(**walk_kwargs)

            return {
                "scalars": processed,
                "disks": disks,
                "volumes": volumes,
            }

        except (SnmpLibraryMissing, CannotConnect, InvalidAuth) as exc:
            raise UpdateFailed(str(exc)) from exc

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=DOMAIN,
        update_method=_async_update_data,
        update_interval=timedelta(seconds=scan_interval),
    )

    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception as exc:
        raise ConfigEntryNotReady(f"Unable to connect to {host}: {exc}") from exc

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
<<<<<<< HEAD
    return True


=======
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload entry when options are updated."""
    await hass.config_entries.async_reload(entry.entry_id)


>>>>>>> ec0ae21 (change config...)
async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
<<<<<<< HEAD
=======


class WDEx2UltraCoordinator(DataUpdateCoordinator):
    """Coordinator that polls the WD EX2 Ultra via SNMP."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        update_interval: timedelta,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=update_interval,
        )
        self.entry = entry

    async def _async_update_data(self) -> dict:
        try:
            return await fetch_snmp_data(dict(self.entry.data), SENSORS)
        except (CannotConnect, SnmpLibraryMissing) as err:
            raise UpdateFailed(f"SNMP update failed: {err}") from err
        except Exception as err:
            _LOGGER.exception("Unexpected error during SNMP update")
            raise UpdateFailed(f"Unexpected SNMP error: {err}") from err
>>>>>>> ec0ae21 (change config...)
