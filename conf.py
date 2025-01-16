"""
Fichero de configuración para el proyecto ClimaCan.
"""

import os
from pathlib import Path

from ctrutils.database.influxdb.InfluxdbOperation import InfluxdbOperation
from ctrutils.handlers.ErrorHandlerBase import ErrorHandler

# Manejador de errores, necesario para capturar la salida stderr de los scripts principales
ERROR_HANDLER = ErrorHandler()

# Variables de entorno
INFLUXDB_PORT = os.getenv("INFLUXDB_PORT")
GRAFCAN_TOKEN = os.getenv("GRAFCAN_TOKEN")
WORKDIR = Path(os.getenv("WORKDIR"))

# Parametros generales
HEADER_API_KEY = {
    "accept": "application/json",
    "Authorization": f"Api-Key {GRAFCAN_TOKEN}",
}
TIMEOUT = 100
# Numero de copias de ficheros logs
LOG_BACKUP_PERIOD = 7
# Tiempo de retencion de cada copia de los ficheros logs
LOG_RETENTION_PERIOD = "1d"

# Parametros InfluxDB
INFLUXDB_HOST = "climacan-influxdb"
INFLUXDB_TIMEOUT = 5
INFLUXDB_CLIENT = InfluxdbOperation(
    host=INFLUXDB_HOST,
    port=INFLUXDB_PORT,
    timeout=INFLUXDB_TIMEOUT,
)

GRAFCAN_DATABASE_NAME = "grafcan"
TASKS_DATABASE_NAME = "tasks"

# Parametros clase StationMetadataFetcher
GRAFCAN__CSV_FILE_CLASSES_METADATA_STATIONS = (
    WORKDIR / "src/grafcan/data/metadata_stations.csv"
)
GRAFCAN__LOG_FILE_CLASSES_METADATA_STATIONS = (
    WORKDIR / "src/grafcan/files/logs/metadata_stations/metadata_stations.log"
)

# Parametros clase FetchObservationsLast
GRAFCAN__LOG_FILE_CLASSES_OBSERVATIONS_LAST = (
    WORKDIR / "src/grafcan/classes/logs/observations_last/observations_last.log"
)

# Parametros fichero write_last_observations.py
GRAFCAN__LOG_FILE_SCRIPT_WRITE_LAST_OBSERVATIONS = (
    WORKDIR
    / "src/grafcan/files/logs/write_last_observations/write_last_observations.log"
)

# Parametros fichero main_grafcan.py
GRAFCAN__MEASUREMENT_NAME_CHECK_TASKS_SCRIPT_MAIN_GRAFCAN = "tasks_status"
GRACAN__CRONTAB_RUN_UPDATE_HISTORICAL_LOCATIONS = "0 23 * * 1,3,5"
GRACAN__CRONTAB_RUN_WRITE_LAST_OBSERVATIONS = "*/10 * * * *"
