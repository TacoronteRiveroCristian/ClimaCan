"""
Fichero de configuración para el proyecto ClimaCan.
"""

import os
from pathlib import Path

from ctrutils.database.influxdb.InfluxdbOperation import InfluxdbOperation

# Variables de entorno
GRAFCAN_TOKEN = os.getenv("GRAFCAN_TOKEN")
WORKING_DIR = Path(os.getenv("WORKDIR"))

# Parametros API KEY
HEADERS = {"accept": "application/json", "Authorization": f"Api-Key {GRAFCAN_TOKEN}"}

# Parametros InfluxDB
INFLUXDB_HOST = "climacan-influxdb"
INFLUXDB_PORT = 8086
INFLUXDB_TIMEOUT = 100
INFLUXDB_CLIENT = InfluxdbOperation(
    host=INFLUXDB_HOST,
    port=INFLUXDB_PORT,
    timeout=INFLUXDB_TIMEOUT,
)

# Parametros Grafcan
GRAFCAN_NAME_DATABASE_METADATA_STATIONS = "metadata_stations"
GRAFCAN_NAME_MEASUREMENT_METADATA_STATIONS = "stations"
GRAFCAN__CSV_FILE_METADATA_STATIONS = "src/grafcan/data/metadata_stations.csv"
GRAFCAN__LOG_FILE_METADATA_STATIONS = "src/grafcan/logs/metadata_stations.log"
GRAFCAN__TIMEOUT_METADATA_STATIONS = 100
