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

GRAFCAN_DATABASE_NAME = "grafcan"

# Parametros clase StationMetadataFetcher
GRAFCAN__CSV_FILE_CLASSES_METADATA_STATIONS = (
    WORKING_DIR / "src/grafcan/data/metadata_stations.csv"
)
GRAFCAN__LOG_FILE_CLASSES_METADATA_STATIONS = (
    WORKING_DIR / "src/grafcan/classes/logs/metadata_stations.log"
)

# Parametros clase FetchObservationsLast
GRAFCAN__LOG_FILE_CLASSES_OBSERVATIONS_LAST = (
    WORKING_DIR / "src/grafcan/classes/logs/observations_last.log"
)

# Parametros fichero write_last_observations.py
GRAFCAN__LOG_FILE_SCRIPT_WRITE_LAST_OBSERVATIONS = (
    WORKING_DIR / "src/grafcan/files/logs/write_last_observations.log"
)

# Parametros fichero main_grafcan.py
GRAFCAN__LOG_FILE_SCRIPT_MAIN_GRAFCAN = (
    WORKING_DIR / "src/grafcan/files/logs/main_grafcan.log"
)
GRAFCAN__MEASUREMENT_NAME_CHECK_TASKS_SCRIPT_MAIN_GRAFCAN = "tasks_status"
GRACAN__CRONTAB_RUN_UPDATE_LIST_OF_STATIONS = "0 23 * * 1,3,5"
GRACAN__CRONTAB_RUN_WRITE_LAST_OBSERVATIONS = "*/10 * * * *"
