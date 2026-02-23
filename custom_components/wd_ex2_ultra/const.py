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

# ============================================================
# WD MYCLOUDEX2ULTRA-MIB base OID
# enterprises(1.3.6.1.4.1) . WD(5127) . productID(1) . projectID(1)
#   . modelID(1) . submodelID(8) . nasAgent(1)
# => 1.3.6.1.4.1.5127.1.1.1.8.1
# ============================================================
WD_NAS_AGENT = "1.3.6.1.4.1.5127.1.1.1.8.1"

# Scalar WD OIDs (append .0 for GET)
WD_OID_SYSTEM_TEMP   = WD_NAS_AGENT + ".7.0"   # mycloudex2ultraTemperature
WD_OID_FAN_STATUS    = WD_NAS_AGENT + ".8.0"   # mycloudex2ultraFanStatus
WD_OID_SW_VERSION    = WD_NAS_AGENT + ".2.0"   # mycloudex2ultraSoftwareVersion
WD_OID_HOSTNAME      = WD_NAS_AGENT + ".3.0"   # mycloudex2ultraHostName

# WD Disk Table OID column roots (without row index)
# Table:  nasAgent.10
# Entry:  nasAgent.10.1
# Cols:   .1 DiskNum  .2 Vendor  .3 Model  .4 Serial  .5 Temperature  .6 Capacity
WD_DISK_TABLE_ROOT      = WD_NAS_AGENT + ".10"
WD_DISK_COL_NUM         = WD_NAS_AGENT + ".10.1.1"  # walk this to find disk indices
WD_DISK_COL_VENDOR      = WD_NAS_AGENT + ".10.1.2"
WD_DISK_COL_MODEL       = WD_NAS_AGENT + ".10.1.3"
WD_DISK_COL_SERIAL      = WD_NAS_AGENT + ".10.1.4"
WD_DISK_COL_TEMPERATURE = WD_NAS_AGENT + ".10.1.5"
WD_DISK_COL_CAPACITY    = WD_NAS_AGENT + ".10.1.6"

# WD Volume Table OID column roots
# Table:  nasAgent.9
# Cols:   .1 VolumeNum  .2 Name  .3 FsType  .4 RaidLevel  .5 Size  .6 FreeSpace
WD_VOL_COL_NUM        = WD_NAS_AGENT + ".9.1.1"
WD_VOL_COL_NAME       = WD_NAS_AGENT + ".9.1.2"
WD_VOL_COL_FSTYPE     = WD_NAS_AGENT + ".9.1.3"
WD_VOL_COL_RAIDLEVEL  = WD_NAS_AGENT + ".9.1.4"
WD_VOL_COL_SIZE       = WD_NAS_AGENT + ".9.1.5"
WD_VOL_COL_FREESPACE  = WD_NAS_AGENT + ".9.1.6"

# ============================================================
# Static sensors (scalar OIDs, fetched with get_cmd)
# ============================================================
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
        "unit": "MiB",
        "icon": "mdi:memory",
        "device_class": None,
        "state_class": "measurement",
        "transform": "kb_to_mib",
    },
    {
        "key": "ram_free",
        "name": "RAM Free",
        "oid": "1.3.6.1.4.1.2021.4.11.0",
        "unit": "MiB",
        "icon": "mdi:memory",
        "device_class": None,
        "state_class": "measurement",
        "transform": "kb_to_mib",
    },
    {
        "key": "ram_used",
        "name": "RAM Used",
        "oid": "1.3.6.1.4.1.2021.4.6.0",
        "unit": "MiB",
        "icon": "mdi:memory",
        "device_class": None,
        "state_class": "measurement",
        "transform": "kb_to_mib",
    },
    {
        "key": "system_temperature",
        "name": "System Temperature",
        "oid": WD_OID_SYSTEM_TEMP,
        "unit": "°C",
        "icon": "mdi:thermometer",
        "device_class": "temperature",
        "state_class": "measurement",
    },
    {
        "key": "fan_status",
        "name": "Fan Status",
        "oid": WD_OID_FAN_STATUS,
        "unit": "",
        "icon": "mdi:fan",
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
