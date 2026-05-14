"""Constants for the Elite Climate integration."""

DOMAIN = "elite_climate"
API_BASE_URL = "https://api.edificioelite.com/api"
SCAN_INTERVAL = 300

DEVICE_CLIMATIZACION = "climatizacion"
DEVICE_AGUA = "agua"

CLIMATIZACION_SENSORS = [
    {
        "key": "last_update",
        "name": "Última actualización",
        "field": "timestamp",
        "device_class": "timestamp",
        "state_class": None,
        "unit": None,
        "icon": "mdi:clock-outline",
    },
    {
        "key": "kwh_calor",
        "name": "Energía calefacción",
        "field": "kwh_calor",
        "device_class": "energy",
        "state_class": "measurement",
        "unit": "kWh",
        "icon": None,
    },
    {
        "key": "kwh_frio",
        "name": "Energía refrigeración",
        "field": "kwh_frio",
        "device_class": "energy",
        "state_class": "measurement",
        "unit": "kWh",
        "icon": None,
    },
    {
        "key": "kwh_calor_abs",
        "name": "Energía calefacción (acumulado)",
        "field": "kwh_calor_abs",
        "device_class": "energy",
        "state_class": "total_increasing",
        "unit": "kWh",
        "icon": None,
    },
    {
        "key": "kwh_frio_abs",
        "name": "Energía refrigeración (acumulado)",
        "field": "kwh_frio_abs",
        "device_class": "energy",
        "state_class": "total_increasing",
        "unit": "kWh",
        "icon": None,
    },
    {
        "key": "kwh_calor_mes_inicio",
        "name": "Energía calefacción (este mes)",
        "field": "kwh_calor_mes_inicio",
        "device_class": "energy",
        "state_class": "total",
        "unit": "kWh",
        "icon": None,
    },
    {
        "key": "kwh_frio_mes_inicio",
        "name": "Energía refrigeración (este mes)",
        "field": "kwh_frio_mes_inicio",
        "device_class": "energy",
        "state_class": "total",
        "unit": "kWh",
        "icon": None,
    },
    {
        "key": "temp_impulsion",
        "name": "Tª impulsión",
        "field": "temp_impulsion",
        "device_class": "temperature",
        "state_class": "measurement",
        "unit": "°C",
        "icon": "mdi:thermometer",
    },
    {
        "key": "temp_retorno",
        "name": "Tª retorno",
        "field": "temp_retorno",
        "device_class": "temperature",
        "state_class": "measurement",
        "unit": "°C",
        "icon": "mdi:thermometer-lines",
    },
    {
        "key": "power_w",
        "name": "Potencia actual",
        "field": "power_w",
        "device_class": "power",
        "state_class": "measurement",
        "unit": "W",
        "icon": "mdi:flash",
    },
]

AGUA_SENSORS = [
    {
        "key": "m3_acs",
        "name": "Consumo ACS",
        "field": "m3_acs",
        "device_class": "water",
        "state_class": "measurement",
        "unit": "m³",
        "icon": "mdi:water",
    },
    {
        "key": "kwh_acs",
        "name": "Energía ACS",
        "field": "kwh_acs",
        "device_class": "energy",
        "state_class": "measurement",
        "unit": "kWh",
        "icon": "mdi:fire",
    },
    {
        "key": "m3_acs_abs",
        "name": "Consumo ACS (acumulado)",
        "field": "m3_acs_abs",
        "device_class": "water",
        "state_class": "total_increasing",
        "unit": "m³",
        "icon": "mdi:water",
    },
    {
        "key": "m3_acs_mes_inicio",
        "name": "Consumo ACS (este mes)",
        "field": "m3_acs_mes_inicio",
        "device_class": "water",
        "state_class": "total",
        "unit": "m³",
        "icon": "mdi:water",
    },
]
