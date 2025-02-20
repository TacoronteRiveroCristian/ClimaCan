"""
Fichero de configuracion para la seccion AEMET.
"""

import os

from src.common.config import WORKDIR

# Token y header para el uso de la API
TOKEN = os.getenv("AEMET_TOKEN")
HEADER = {"api_key": TOKEN}

# Paths relativos
MUNICIPALITIES_EXCEL_PATH = WORKDIR / "src/aemet/artifacts/municipalities.xlsx"
MUNICIPALITIES_JSON_PATH = WORKDIR / "src/aemet/artifacts/municipalities.json"
DATABASE_PROVISIONING_YAML_PATH = (
    WORKDIR
    / "docker/volumes/grafana/provisioning/datasources/aemet-datasources.yaml"
)
