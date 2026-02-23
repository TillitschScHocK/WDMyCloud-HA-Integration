> ⚠️ **Attention:** This project is currently under development.  
> Values are not yet fully or accurately tracked and may be incomplete or incorrect.

# WD MyCloud EX2 Ultra – Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
![Version](https://img.shields.io/badge/version-1.0.0-blue)

A custom Home Assistant integration for the **WD MyCloud EX2 Ultra** NAS, using SNMP to monitor CPU load, RAM, disk temperatures, disk status, network traffic, and system uptime — all without any manual YAML configuration.

---

## Features

- Full **Config Flow** setup via *Settings → Integrations* (no `configuration.yaml` needed)
- Supports **SNMPv2c** and **SNMPv3**
- **13 pre-configured sensors** with automatic OID polling
- Configurable **polling interval** (30 / 60 / 120 seconds)
- Compatible with **HACS** for easy installation and updates

---

## Requirements

- Home Assistant 2023.1 or newer
- SNMP enabled on your WD MyCloud EX2 Ultra (WD Dashboard → Network → SNMP)
- Python package: `pysnmp` (installed automatically)

---

## Installation

### Via HACS (recommended)

1. Open HACS in Home Assistant.
2. Click **Integrations** → three-dot menu → **Custom repositories**.
3. Add `https://github.com/TillitschScHocK/WDMyCloud-HA-Integration` as an **Integration**.
4. Search for **WD MyCloud EX2 Ultra** and click **Install**.
5. Restart Home Assistant.

### Manual Installation

1. Copy the `custom_components/wd_ex2_ultra` folder into your Home Assistant `custom_components` directory.
2. Restart Home Assistant.

---

## Setup

1. Go to **Settings → Devices & Services → Add Integration**.
2. Search for **WD MyCloud EX2 Ultra**.
3. **Step 1 – SNMP Version:** Choose `SNMPv2c` or `SNMPv3`.
4. **Step 2 – Connection Details:**
   - *SNMPv2c:* Enter the IP/hostname and community string (default: `public`).
   - *SNMPv3:* Enter the IP/hostname, username, auth protocol (MD5/SHA), auth password, privacy protocol (DES/AES), and privacy password.
5. Select the **polling interval** (30, 60, or 120 seconds; default: 60 s).
6. The integration validates the connection before saving. If it fails, check that SNMP is enabled and the credentials are correct.

---

## Sensors

| Sensor | OID | Unit |
|---|---|---|
| CPU Load 1min | `1.3.6.1.4.1.2021.10.1.3.1` | % |
| CPU Load 5min | `1.3.6.1.4.1.2021.10.1.3.2` | % |
| CPU Load 15min | `1.3.6.1.4.1.2021.10.1.3.3` | % |
| RAM Total | `1.3.6.1.4.1.2021.4.5.0` | kB |
| RAM Free | `1.3.6.1.4.1.2021.4.11.0` | kB |
| RAM Used | `1.3.6.1.4.1.2021.4.6.0` | kB |
| Disk 1 Temperature | `1.3.6.1.4.1.5127.1.1.1.8.1.11.1` | °C |
| Disk 2 Temperature | `1.3.6.1.4.1.5127.1.1.1.8.1.11.2` | °C |
| Disk 1 Status | `1.3.6.1.4.1.5127.1.1.1.8.1.4.1` | — |
| Disk 2 Status | `1.3.6.1.4.1.5127.1.1.1.8.1.4.2` | — |
| Network In (eth0) | `1.3.6.1.2.1.2.2.1.10.2` | Bytes |
| Network Out (eth0) | `1.3.6.1.2.1.2.2.1.16.2` | Bytes |
| System Uptime | `1.3.6.1.2.1.1.3.0` | s |

---

## Enabling SNMP on the WD MyCloud EX2 Ultra

1. Log in to the WD Dashboard.
2. Navigate to **Settings → Network → SNMP**.
3. Enable SNMP and set a community string (for v2c) or configure a user (for v3).

---

## Troubleshooting

| Problem | Solution |
|---|---|
| `cannot_connect` error | Verify the IP address and that SNMP is enabled on the NAS |
| `invalid_auth` error | Check the community string (v2c) or SNMPv3 credentials |
| Sensors show `unavailable` | Check Home Assistant logs for SNMP timeout or OID errors |
| No data after restart | Ensure `pysnmp` is installed; restart HA after HACS install |

---

## License

MIT – see [LICENSE](LICENSE)
