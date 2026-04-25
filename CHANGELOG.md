# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] – 2026-03-24 🎉 First Full Release

### Fixed

- **Home Assistant no longer restarts when adding the integration.** If the NAS is unreachable at startup, the integration now gracefully retries in the background instead of crashing the HA core.
- **HA can no longer freeze due to a hanging SNMP request.** Every SNMP call now has a hard timeout. If the NAS stops responding mid-poll, the sensors go to *unavailable* and HA keeps running normally.
- Fixed a rare error on integration unload that could leave stale data behind.

### Improved

- **Sensor updates are noticeably faster.** All SNMP queries (CPU, RAM, network, disk table, volume table) are now sent in parallel instead of one after another. On a typical setup this cuts each update cycle from several seconds down to roughly the time of a single request.
- **Scan interval can now be changed after setup** without removing and re-adding the integration. Go to *Settings → Integrations → WD MyCloud EX2 Ultra → Configure*.

### Changed (units)

- **RAM sensors** (Total, Free, Used) now correctly report in **MiB** with full Home Assistant unit-conversion support. HA can display the value in GiB, MB, or any other unit via the sensor settings.
- **Network In / Network Out** now use the `DATA_SIZE` device class with **Bytes** as the base unit. Home Assistant automatically converts the display to KB, MB, or GB depending on the value size.
- **System Uptime** now uses the `DURATION` device class so HA can display it as hours, days, etc.
- **Disk Capacity** sensors now report in **GB** with `DATA_SIZE` device class, enabling HA unit conversion.
- **Volume sensors** (Total Size, Free Space, Used Space) now report in **MB** with `DATA_SIZE` device class.

---

## [0.9.0] – 2026-02-23

### Added

- **WD System Temperature sensor** using the official `MYCLOUDEX2ULTRA-MIB` OID (`nasAgent.7`).
- **WD Fan Status sensor** using the official MIB OID (`nasAgent.8`).
- **Dynamic disk sensors** based on the WD disk table (`nasAgent.10`). The number of disks is detected automatically via SNMP walk, so 1-disk and 2-disk setups both work without any configuration change. Each disk gets four sensors: Temperature, Capacity, Model, Vendor.
- New `walk_snmp_column()` async helper for iterating SNMP table columns via `next_cmd`.
- New `fetch_disk_table()` async helper that walks all disk table columns and returns structured data.
- New `parse_snmp_number()` helper that safely parses numeric SNMP strings regardless of locale-specific separators (fixes the `1.354.752,0` display bug).

### Changed

- **RAM sensors** (Total, Free, Used) are now returned in **MiB** instead of kB. This prevents Home Assistant from displaying values like `1.354.752,0 kB` due to locale-based number formatting.
- Removed static `disk1_temperature`, `disk2_temperature`, `disk1_status`, `disk2_status` sensors. These used incorrect OID paths and are now fully replaced by the dynamic disk table sensors.
- `fetch_snmp_data()` now always populates a `_disks` key in the coordinator data with the result of `fetch_disk_table()`.
- `sensor.py` generates dynamic `WDEx2UltraDiskSensor` entities from `coordinator.data["_disks"]` at setup time.

---

## [0.5.0] – 2026-02-23

### Fixed

- **CRITICAL:** Switched from deprecated `pysnmp-lextudio` to the official `pysnmp` package maintained by LeXtudio Inc. Updated `manifest.json` to use `pysnmp>=6.2.0,<7.0.0`.
- Added fallback imports in `snmp_helper.py` to support both new (`pysnmp.hlapi.v1arch.asyncio`) and legacy (`pysnmp.hlapi`) import paths for maximum compatibility.
- Added `parse_wd_temperature()` function to handle WD's proprietary temperature format `'Centigrade:48 \tFahrenheit:118'`.
- Improved `build_auth_data()` to catch `ImportError` immediately and raise `SnmpLibraryMissing`.
- Updated `fetch_snmp_data()` to apply special parsing for any sensor key containing `"temperature"`.
- Added `sanitize_host()` helper that automatically strips `http://`, `https://`, trailing slashes and whitespace from the host field.
- Extracted all SNMP logic into a dedicated `snmp_helper.py` module for better separation of concerns.
- Added a dedicated `SnmpLibraryMissing` error class with a clear user-facing message.
- Improved error categorisation in the config flow: `ImportError` and transport errors are now caught individually.
- Updated `strings.json` to include the new `snmp_library_missing` error message and improved host field descriptions.

---

## [0.1.0] – 2026-02-23

### Added

- Initial release of the WD MyCloud EX2 Ultra Home Assistant integration.
- Full Config Flow setup via Settings → Integrations (no YAML required).
- Support for **SNMPv2c** (community string) and **SNMPv3** (username, auth protocol, privacy protocol).
- 13 pre-configured SNMP sensors:
  - CPU Load (1min, 5min, 15min)
  - RAM Total, RAM Free, RAM Used
  - Disk 1 & Disk 2 Temperature (°C)
  - Disk 1 & Disk 2 Status
  - Network In / Network Out (eth0, bytes)
  - System Uptime (seconds)
- Configurable polling interval: 30, 60, or 120 seconds (default: 60 s).
- Connection validation during setup with user-friendly error messages.
- HACS compatibility via `hacs.json`.
- `manifest.json` with `config_flow: true` and `iot_class: local_polling`.
- `strings.json` for UI label localisation.
- MIT license.