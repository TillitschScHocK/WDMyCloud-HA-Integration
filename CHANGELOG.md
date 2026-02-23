# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.3.0] – 2026-02-23

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
- `manifest.json` version bumped to `1.3.0`.

---

## [1.0.3] – 2026-02-23

### Fixed

- **CRITICAL:** Switched from deprecated `pysnmp-lextudio` to the official `pysnmp` package maintained by LeXtudio Inc. The `-lextudio` postfix packages are no longer maintained and version 6.2.6 does not exist under that name.
- Updated `manifest.json` to use `pysnmp>=6.2.0,<7.0.0` (6.2.x is the stable branch, 7.x introduces breaking API changes).
- Added fallback imports in `snmp_helper.py` to support both new (`pysnmp.hlapi.v1arch.asyncio`) and legacy (`pysnmp.hlapi`) import paths for maximum compatibility with different Home Assistant pysnmp installations.
- Updated all error messages to reference `pysnmp` instead of `pysnmp-lextudio`.

---

## [1.0.2] – 2026-02-23

### Fixed

- Added `parse_wd_temperature()` function to handle WD's proprietary temperature format `'Centigrade:48 \tFahrenheit:118'` which the NAS returns for disk temperature OIDs. The parser extracts the Celsius value and converts it to a float.
- Improved `build_auth_data()` to catch `ImportError` immediately and raise `SnmpLibraryMissing`, preventing the error from cascading into `test_snmp_connection()`.
- Pinned `pysnmp-lextudio` to exact version `6.2.6` in `manifest.json` to ensure consistent behavior across installations (reverted in 1.0.3).
- Updated `fetch_snmp_data()` to apply special parsing for any sensor key containing `"temperature"`.

---

## [1.0.1] – 2026-02-23

### Fixed

- Changed SNMP library dependency from `pysnmp` to `pysnmp-lextudio>=6.0.0` (the actively maintained fork with updated import paths) (reverted in 1.0.3).
- Added `sanitize_host()` helper that automatically strips `http://`, `https://`, trailing slashes and whitespace from the host field — entering `http://192.168.1.100` no longer causes an error.
- Extracted all SNMP logic into a dedicated `snmp_helper.py` module for better separation of concerns.
- Added a dedicated `SnmpLibraryMissing` error class with a clear user-facing message when `pysnmp-lextudio` is not yet installed.
- Improved error categorisation in the config flow: `ImportError` and transport errors are now caught individually instead of falling through to the generic `unknown` error.
- Fixed `__init__.py` to use the new shared `fetch_snmp_data()` helper from `snmp_helper.py`.
- Updated `strings.json` to include the new `snmp_library_missing` error message and improved host field descriptions.

---

## [1.0.0] – 2026-02-23

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
