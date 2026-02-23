"""Constants for the WD MyCloud EX2 Ultra integration."""

DOMAIN = "wd_ex2_ultra"

# Config keys
CONF_SNMP_VERSION = "snmp_version"
CONF_HOST = "host"
CONF_COMMUNITY = "community"
CONF_USERNAME = "username"
CONF_AUTH_PROTOCOL = "auth_protocol"
CONF_AUTH_PASSWORD = "auth_password"
CONF_PRIV_PROTOCOL = "priv_protocol"
CONF_PRIV_PASSWORD = "priv_password"
CONF_SCAN_INTERVAL = "scan_interval"

# SNMP versions
SNMP_VERSION_V2C = "SNMPv2c"
SNMP_VERSION_V3 = "SNMPv3"

# Auth protocols
AUTH_PROTOCOLS = ["MD5", "SHA"]

# Privacy protocols
PRIV_PROTOCOLS = ["DES", "AES"]

# Polling interval options (seconds)
SCAN_INTERVAL_OPTIONS = [30, 60, 120]
DEFAULT_SCAN_INTERVAL = 60

# Sensor definitions: key, name, OID, unit
SENSORS = [
    {
        "key": "cpu_load_1min",
        "name": "CPU Load 1min",
        "oid": "1.3.6.1.4.1.2021.10.1.3.1",
        "unit": "%",
        "icon": "mdi:cpu-64-bit",
        "device_class": None,
        "state_class": "measurement",
    },
    {
        "key": "cpu_load_5min",
        "name": "CPU Load 5min",
        "oid": "1.3.6.1.4.1.2021.10.1.3.2",
        "unit": "%",
        "icon": "mdi:cpu-64-bit",
        "device_class": None,
        "state_class": "measurement",
    },
    {
        "key": "cpu_load_15min",
        "name": "CPU Load 15min",
        "oid": "1.3.6.1.4.1.2021.10.1.3.3",
        "unit": "%",
        "icon": "mdi:cpu-64-bit",
        "device_class": None,
        "state_class": "measurement",
    },
    {
        "key": "ram_total",
        "name": "RAM Total",
        "oid": "1.3.6.1.4.1.2021.4.5.0",
        "unit": "kB",
        "icon": "mdi:memory",
        "device_class": None,
        "state_class": "measurement",
    },
    {
        "key": "ram_free",
        "name": "RAM Free",
        "oid": "1.3.6.1.4.1.2021.4.11.0",
        "unit": "kB",
        "icon": "mdi:memory",
        "device_class": None,
        "state_class": "measurement",
    },
    {
        "key": "ram_used",
        "name": "RAM Used",
        "oid": "1.3.6.1.4.1.2021.4.6.0",
        "unit": "kB",
        "icon": "mdi:memory",
        "device_class": None,
        "state_class": "measurement",
    },
    {
        "key": "disk1_temperature",
        "name": "Disk 1 Temperature",
        "oid": "1.3.6.1.4.1.5127.1.1.1.8.1.11.1",
        "unit": "°C",
        "icon": "mdi:thermometer",
        "device_class": "temperature",
        "state_class": "measurement",
    },
    {
        "key": "disk2_temperature",
        "name": "Disk 2 Temperature",
        "oid": "1.3.6.1.4.1.5127.1.1.1.8.1.11.2",
        "unit": "°C",
        "icon": "mdi:thermometer",
        "device_class": "temperature",
        "state_class": "measurement",
    },
    {
        "key": "disk1_status",
        "name": "Disk 1 Status",
        "oid": "1.3.6.1.4.1.5127.1.1.1.8.1.4.1",
        "unit": "",
        "icon": "mdi:harddisk",
        "device_class": None,
        "state_class": None,
    },
    {
        "key": "disk2_status",
        "name": "Disk 2 Status",
        "oid": "1.3.6.1.4.1.5127.1.1.1.8.1.4.2",
        "unit": "",
        "icon": "mdi:harddisk",
        "device_class": None,
        "state_class": None,
    },
    {
        "key": "network_in",
        "name": "Network In (eth0)",
        "oid": "1.3.6.1.2.1.2.2.1.10.2",
        "unit": "B",
        "icon": "mdi:download-network",
        "device_class": None,
        "state_class": "total_increasing",
    },
    {
        "key": "network_out",
        "name": "Network Out (eth0)",
        "oid": "1.3.6.1.2.1.2.2.1.16.2",
        "unit": "B",
        "icon": "mdi:upload-network",
        "device_class": None,
        "state_class": "total_increasing",
    },
    {
        "key": "system_uptime",
        "name": "System Uptime",
        "oid": "1.3.6.1.2.1.1.3.0",
        "unit": "s",
        "icon": "mdi:timer-outline",
        "device_class": None,
        "state_class": "measurement",
    },
]
