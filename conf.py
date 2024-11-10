"""
Fichero de configuración para el proyecto ClimaCan.
"""

import os
from pathlib import Path

from ctrutils.database.influxdb.InfluxdbOperation import InfluxdbOperation

# Variables de entorno
GRAFCAN_TOKEN = os.getenv("GRAFCAN_TOKEN")
WORKING_DIR = Path(os.getenv("WORKDIR"))

# Parametros generales
HEADER_API_KEY = {
    "accept": "application/json",
    "Authorization": f"Api-Key {GRAFCAN_TOKEN}",
}
TIMEOUT = 100

# Parametros InfluxDB
INFLUXDB_HOST = "climacan-influxdb"
INFLUXDB_PORT = 8086
INFLUXDB_TIMEOUT = 100
INFLUXDB_CLIENT = InfluxdbOperation(
    host=INFLUXDB_HOST,
    port=INFLUXDB_PORT,
    timeout=INFLUXDB_TIMEOUT,
)

# Parametros clase StationMetadataFetcher
GRAFCAN__CSV_FILE_METADATA_STATIONS = "src/grafcan/data/metadata_stations.csv"
GRAFCAN__LOG_FILE_METADATA_STATIONS = "src/grafcan/logs/metadata_stations.log"

# Parametros clase FetchObservationsLast
GRAFCAN__LOG_FILE_OBSERVATIONS_LAST = "src/grafcan/logs/observations_last.log"