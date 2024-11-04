"""
"""

import os
from pathlib import Path

# Variables de entorno
GRAFCAN_TOKEN = os.getenv("GRAFCAN_TOKEN")
WORKING_DIR = Path(os.getenv("WORKDIR"))

# Parametros API KEY
HEADERS = {"accept": "application/json", "Authorization": f"Api-Key {GRAFCAN_TOKEN}"}

# Parametros Grafcan
GRAFCAN__CSV_FILE_GET_URLS_OF_STATIONS = "src/grafcan/data/get_urls_of_stations.csv"
GRAFCAN__LOG_FILE_GET_URLS_OF_STATIONS = "src/grafcan/logs/get_urls_of_stations.log"
GRAFCAN__CSV_FILE_GET_LOCATIONS_OF_STATIONS = (
    "src/grafcan/data/get_locations_of_stations.csv"
)
GRAFCAN__LOG_FILE_GET_LOCATIONS_OF_STATIONS = (
    "src/grafcan/logs/get_locations_of_stations.log"
)
