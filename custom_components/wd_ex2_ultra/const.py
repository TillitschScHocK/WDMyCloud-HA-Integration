"""Constants for the WD MyCloud EX2 Ultra integration."""

from homeassistant.const import UnitOfInformation, UnitOfTemperature, UnitOfTime

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

# ============================================================
# WD MYCLOUDEX2ULTRA-MIB base OID
# 1.3.6.1.4.1.5127.1.1.1.8.1
# ============================================================
WD_NAS_AGENT = "1.3.6.1.4.1.5127.1.1.1.8.1"

# Scalar WD OIDs
WD_OID_SYSTEM_TEMP = WD_NAS_AGENT + ".7.0"
WD_OID_FAN_STATUS  = WD_NAS_AGENT + ".8.0"

# WD Disk Table OID column roots (SNMP walk)
WD_DISK_TABLE_ROOT      = WD_NAS_AGENT + ".10"
WD_DISK_COL_NUM         = WD_NAS_AGENT + ".10.1.1"
WD_DISK_COL_VENDOR      = WD_NAS_AGENT + ".10.1.2"
WD_DISK_COL_MODEL       = WD_NAS_AGENT + ".10.1.3"
WD_DISK_COL_SERIAL      = WD_NAS_AGENT + ".10.1.4"
WD_DISK_COL_TEMPERATURE = WD_NAS_AGENT + ".10.1.5"
WD_DISK_COL_CAPACITY    = WD_NAS_AGENT + ".10.1.6"  # in MB -> /1000 -> GB
WD_DISK_COL_STATUS      = WD_NAS_AGENT + ".10.1.7"

# WD Volume Table OID column roots (SNMP walk)
WD_VOL_TABLE_ROOT   = WD_NAS_AGENT + ".9"
WD_VOL_COL_NUM      = WD_NAS_AGENT + ".9.1.1"
WD_VOL_COL_NAME     = WD_NAS_AGENT + ".9.1.2"
WD_VOL_COL_FSTYPE   = WD_NAS_AGENT + ".9.1.3"
WD_VOL_COL_RAIDLEVEL = WD_NAS_AGENT + ".9.1.4"
WD_VOL_COL_SIZE      = WD_NAS_AGENT + ".9.1.5"   # in KB -> /1024/1024 -> GiB
WD_VOL_COL_FREESPACE = WD_NAS_AGENT + ".9.1.6"   # in KB -> /1024/1024 -> GiB

# Lookup maps
DISK_STATUS_MAP = {
    "0": "Normal",
    "1": "Good",
    "2": "Degraded",
    "3": "Failure",
}

FAN_STATUS_MAP = {
    "0": "Normal",
    "1": "Error",
}

RAID_LEVEL_MAP = {
    "0": "JBOD",
    "1": "RAID 0",
    "2": "RAID 1",
    "3": "RAID 5",
    "4": "RAID 10",
}

IF_OPER_STATUS_MAP = {
    1: "up",
    2: "down",
    3: "testing",
    4: "unknown",
    5: "dormant",
    6: "notPresent",
    7: "lowerLayerDown",
}

# ============================================================
# Static scalar sensors (21 total)
# transform key must match a function in snmp_helper.py
# ============================================================
SENSORS = [
    # --- System ---
    {
        "key": "system_uptime",
        "name": "System Uptime",
        "oid": "1.3.6.1.2.1.1.3.0",
        "unit": UnitOfTime.SECONDS,
        "device_class": "duration",
        "state_class": "measurement",
        "icon": "mdi:timer-outline",
        "transform": "timeticks_to_seconds",
    },
    # --- CPU (HR-MIB hrProcessorLoad) ---
    {
        "key": "cpu_core1",
        "name": "CPU Core 1",
        "oid": "1.3.6.1.2.1.25.3.3.1.2.196608",
        "unit": "%",
        "device_class": None,
        "state_class": "measurement",
        "icon": "mdi:cpu-64-bit",
    },
    {
        "key": "cpu_core2",
        "name": "CPU Core 2",
        "oid": "1.3.6.1.2.1.25.3.3.1.2.196609",
        "unit": "%",
        "device_class": None,
        "state_class": "measurement",
        "icon": "mdi:cpu-64-bit",
    },
    # --- RAM (HR-MIB hrStorageTable, alloc_unit = 1024 bytes) ---
    {
        "key": "ram_total",
        "name": "RAM Total",
        "oid": "1.3.6.1.2.1.25.2.3.1.5.1",
        "unit": UnitOfInformation.MEBIBYTES,
        "device_class": "data_size",
        "state_class": "measurement",
        "icon": "mdi:memory",
        "transform": "hrStorage_kb_to_mib",
    },
    {
        "key": "ram_used",
        "name": "RAM Used",
        "oid": "1.3.6.1.2.1.25.2.3.1.6.1",
        "unit": UnitOfInformation.MEBIBYTES,
        "device_class": "data_size",
        "state_class": "measurement",
        "icon": "mdi:memory",
        "transform": "hrStorage_kb_to_mib",
    },
    {
        "key": "ram_cache",
        "name": "RAM Cache",
        "oid": "1.3.6.1.2.1.25.2.3.1.6.7",
        "unit": UnitOfInformation.MEBIBYTES,
        "device_class": "data_size",
        "state_class": "measurement",
        "icon": "mdi:memory",
        "transform": "hrStorage_kb_to_mib",
    },
    {
        "key": "ram_buffer",
        "name": "RAM Buffer",
        "oid": "1.3.6.1.2.1.25.2.3.1.6.6",
        "unit": UnitOfInformation.MEBIBYTES,
        "device_class": "data_size",
        "state_class": "measurement",
        "icon": "mdi:memory",
        "transform": "hrStorage_kb_to_mib",
    },
    # --- Swap (HR-MIB hrStorageTable, alloc_unit = 1024 bytes) ---
    {
        "key": "swap_total",
        "name": "Swap Total",
        "oid": "1.3.6.1.2.1.25.2.3.1.5.10",
        "unit": UnitOfInformation.MEBIBYTES,
        "device_class": "data_size",
        "state_class": "measurement",
        "icon": "mdi:harddisk",
        "transform": "hrStorage_kb_to_mib",
    },
    {
        "key": "swap_used",
        "name": "Swap Used",
        "oid": "1.3.6.1.2.1.25.2.3.1.6.10",
        "unit": UnitOfInformation.MEBIBYTES,
        "device_class": "data_size",
        "state_class": "measurement",
        "icon": "mdi:harddisk",
        "transform": "hrStorage_kb_to_mib",
    },
    # --- Processes ---
    {
        "key": "process_count",
        "name": "Process Count",
        "oid": "1.3.6.1.2.1.25.1.6.0",
        "unit": None,
        "device_class": None,
        "state_class": "measurement",
        "icon": "mdi:format-list-numbered",
    },
    # --- Main Volume Storage (HR-MIB index 57, alloc_unit = 512 bytes) ---
    {
        "key": "volume_total",
        "name": "Volume Total",
        "oid": "1.3.6.1.2.1.25.2.3.1.5.57",
        "unit": UnitOfInformation.GIBIBYTES,
        "device_class": "data_size",
        "state_class": "measurement",
        "icon": "mdi:harddisk",
        "transform": "hrStorage_blocks_to_gib",
    },
    {
        "key": "volume_used",
        "name": "Volume Used",
        "oid": "1.3.6.1.2.1.25.2.3.1.6.57",
        "unit": UnitOfInformation.GIBIBYTES,
        "device_class": "data_size",
        "state_class": "measurement",
        "icon": "mdi:harddisk",
        "transform": "hrStorage_blocks_to_gib",
    },
    # --- Network (IF-MIB, interface index 2 = egiga0) ---
    {
        "key": "network_in",
        "name": "Network In (egiga0)",
        "oid": "1.3.6.1.2.1.31.1.1.1.6.2",
        "unit": UnitOfInformation.BYTES,
        "device_class": "data_size",
        "state_class": "total_increasing",
        "icon": "mdi:download-network",
    },
    {
        "key": "network_out",
        "name": "Network Out (egiga0)",
        "oid": "1.3.6.1.2.1.31.1.1.1.10.2",
        "unit": UnitOfInformation.BYTES,
        "device_class": "data_size",
        "state_class": "total_increasing",
        "icon": "mdi:upload-network",
    },
    {
        "key": "network_speed",
        "name": "LAN Speed",
        "oid": "1.3.6.1.2.1.2.2.1.5.2",
        "unit": None,
        "device_class": None,
        "state_class": None,
        "icon": "mdi:ethernet",
        "transform": "bps_to_mbit",
    },
    {
        "key": "network_status",
        "name": "LAN Status",
        "oid": "1.3.6.1.2.1.2.2.1.8.2",
        "unit": None,
        "device_class": None,
        "state_class": None,
        "icon": "mdi:lan",
        "transform": "if_oper_status_map",
    },
    {
        "key": "network_in_discards",
        "name": "Network In Discards (egiga0)",
        "oid": "1.3.6.1.2.1.2.2.1.13.2",
        "unit": None,
        "device_class": None,
        "state_class": "total_increasing",
        "icon": "mdi:alert-network",
    },
    {
        "key": "network_in_errors",
        "name": "Network In Errors (egiga0)",
        "oid": "1.3.6.1.2.1.2.2.1.14.2",
        "unit": None,
        "device_class": None,
        "state_class": "total_increasing",
        "icon": "mdi:network-off",
    },
    {
        "key": "network_out_errors",
        "name": "Network Out Errors (egiga0)",
        "oid": "1.3.6.1.2.1.2.2.1.20.2",
        "unit": None,
        "device_class": None,
        "state_class": "total_increasing",
        "icon": "mdi:network-off",
    },
    # --- WD-specific scalars ---
    {
        "key": "system_temperature",
        "name": "System Temperature",
        "oid": WD_OID_SYSTEM_TEMP,
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": "temperature",
        "state_class": "measurement",
        "icon": "mdi:thermometer",
        "transform": "parse_wd_temperature",
    },
    {
        "key": "fan_status",
        "name": "Fan Status",
        "oid": WD_OID_FAN_STATUS,
        "unit": None,
        "device_class": None,
        "state_class": None,
        "icon": "mdi:fan",
        "transform": "fan_status_map",
    },
]
