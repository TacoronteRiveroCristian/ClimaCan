"""
Fichero de configuracion globale para el proyecto ClimaCan.
"""

import os
from pathlib import Path

# Directorio de trabajo
WORKDIR = Path(os.getenv("WORKDIR"))

# Parametros InfluxDB
INFLUXDB_HOST = "climacan-influxdb"
INFLUXDB_PORT = os.getenv("INFLUXDB_PORT")
INFLUXDB_TIMEOUT = 5
