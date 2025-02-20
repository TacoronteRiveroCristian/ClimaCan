"""
Fichero de configuracion globale para el proyecto ClimaCan.
"""

import os
from pathlib import Path
from src.common.postgres_db_handler import PostgresDBHandler

# Directorio de trabajo
WORKDIR = Path(os.getenv("WORKDIR"))

# Parametros InfluxDB
INFLUXDB_HOST = "climacan-influxdb"
INFLUXDB_PORT = os.getenv("INFLUXDB_PORT")
INFLUXDB_TIMEOUT = 5

# Parametros PostgreSQL
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_USER =   os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD =   os.getenv("POSTGRES_PASSWORD")
POSTGRES_PORT =   os.getenv("POSTGRES_PORT")

# Singleton de la clase PostgresDBHandler
postgres_client = PostgresDBHandler(
    db=POSTGRES_DB,
    user=POSTGRES_USER,
    password=POSTGRES_PASSWORD,
    host="climacan-postgres",
    port=POSTGRES_PORT,
)
