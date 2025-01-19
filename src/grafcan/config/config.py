"""
Fichero de configuracion para la seccion Grafcan.
"""

import os

from src.common.config import WORKDIR

TOKEN = os.getenv("GRAFCAN_TOKEN")

CSV_FILE_CLASSES_METADATA_STATIONS = (
    WORKDIR / "src/grafcan/data/metadata_stations.csv"
)

### main_grafcan.py ###
GRAFCAN__MEASUREMENT_NAME_CHECK_TASKS_SCRIPT_MAIN_GRAFCAN = "tasks_status"
