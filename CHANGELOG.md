# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.2] – 2026-02-23

### Fixed

- Added `parse_wd_temperature()` function to handle WD's proprietary temperature format `'Centigrade:48 \tFahrenheit:118'` which the NAS returns for disk temperature OIDs. The parser extracts the Celsius value and converts it to a float.
- Improved `build_auth_data()` to catch `ImportError` immediately and raise `SnmpLibraryMissing`, preventing the error from cascading into `test_snmp_connection()`.
- Pinned `pysnmp-lextudio` to exact version `6.2.6` in `manifest.json` to ensure consistent behavior across installations.
- Updated `fetch_snmp_data()` to apply special parsing for any sensor key containing `"temperature"`.

---

## [1.0.1] – 2026-02-23

### Fixed

- Changed SNMP library dependency from `pysnmp` to `pysnmp-lextudio>=6.0.0` (the actively maintained fork with updated import paths).
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
