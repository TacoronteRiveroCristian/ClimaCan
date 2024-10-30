"""
"""

import os
from pathlib import Path

# Variables de entorno
GRAFCAN_TOKEN = os.getenv("GRAFCAN_TOKEN")
WORKING_DIR = Path(os.getenv("ROOT_PROJECT", "/workspaces/ClimaCan"))

# Parametros API KEY
HEADERS = {"accept": "application/json", "Authorization": f"Api-Key {GRAFCAN_TOKEN}"}

# Parametros Grafcan
GRAFCAN__LOF_FILE_GET_URLS_OF_STATIONS = "src/grafcan/log/get_urls_of_stations.log"
GRAFCAN__LOF_FILE_GET_LOCATIONS_OF_STATIONS = (
    "src/grafcan/log/get_locations_of_stations.log"
)
