<p align="center">
  <img src="https://raw.githubusercontent.com/TillitschScHocK/WDMyCloud-HA-Integration/main/custom_components/wd_ex2_ultra/brand/icon.png" width="160" alt="WD MyCloud EX2 Ultra Logo" />
</p>

<h1 align="center">WD MyCloud EX2 Ultra</h1>

<p align="center">
  <a href="https://github.com/hacs/integration"><img src="https://img.shields.io/badge/HACS-Custom-orange.svg" alt="HACS Custom" /></a>
  <img src="https://img.shields.io/badge/version-1.0-blue" alt="Version" />
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License" />
</p>

<p align="center">
  SNMP-based monitoring for your WD MyCloud EX2 Ultra NAS inside Home Assistant.
</p>

## Features

- UI-based **Config Flow** setup (no `configuration.yaml`)
- **SNMPv2c** and **SNMPv3** support
- **30+ sensors** covering system, CPU, memory, disks, volume, network, and fan
- Configurable **polling interval** (30 / 60 / 120 seconds)
- Easy installation and updates via **HACS**

## Requirements

- Home Assistant 2026 or newer
- SNMP enabled on your WD MyCloud EX2 Ultra (WD Dashboard → Network → SNMP)

## Installation

### HACS (recommended)

1. Open **HACS** → **Integrations** → **⋮** → **Custom repositories**.
2. Add `https://github.com/TillitschScHocK/WDMyCloud-HA-Integration` as **Integration**.
3. Search for **WD MyCloud EX2 Ultra** and click **Install**.
4. Restart Home Assistant.

### Manual

1. Copy the `custom_components/wd_ex2_ultra` folder into your `custom_components` directory.
2. Restart Home Assistant.

## Setup

1. Go to **Settings → Devices & Services → Add Integration**.
2. Search for **WD MyCloud EX2 Ultra**.
3. Select **SNMPv2c** or **SNMPv3** and follow the config.
4. Provide your credentials and choose a **polling interval** (default: 60 s).
5. The integration validates the connection automatically before saving.

## Sensors

| Category    | Sensors                                                                               | Unit              |
| ----------- | ------------------------------------------------------------------------------------- | ----------------- |
| **System**  | Uptime, Temperature, Process Count                                                    | s, °C, —          |
| **CPU**     | CPU Core 1, CPU Core 2                                                                | %                 |
| **Memory**  | RAM Total, Used, Buffer, Cache                                                        | MiB               |
| **Swap**    | Swap Total, Used                                                                      | MiB               |
| **Disks**   | Disk 1 & 2 Capacity, Health, Temperature, Model, Vendor                               | GB, —, °C, —, —   |
| **Volume**  | Volume Total, Used; Volume_1 Free, Used, Total Size, RAID Level, Used Percent         | GiB, —            |
| **Network** | LAN Speed, LAN Status; Network In / Out (egiga0), In Discards, In Errors, Out Errors  | Mbit/s, —, B, —   |
| **Fan**     | Fan Status                                                                            | —                 |

## Enabling SNMP on the NAS

1. Log in to the WD Dashboard.
2. Navigate to **Settings → Network → SNMP**.
3. Enable SNMP and configure your community string (v2c) or user credentials (v3).

## Troubleshooting

| Problem                    | Solution                                                                 |
| -------------------------- | ------------------------------------------------------------------------ |
| `cannot_connect`           | Verify the NAS IP and ensure SNMP is enabled.                            |
| `invalid_auth`             | Double-check the community string or SNMPv3 credentials.                 |
| Sensors show `unavailable` | Check the Home Assistant logs for SNMP timeouts or missing OIDs.         |

## License

MIT — see [LICENSE](LICENSE)