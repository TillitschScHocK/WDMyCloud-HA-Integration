# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
