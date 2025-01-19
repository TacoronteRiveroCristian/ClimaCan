"""
Fichero de configuracion para la seccion AEMET.
"""

import os

from conf import WORKDIR

TOKEN = os.getenv("AEMET_TOKEN")

MUNICIPALITIES_EXCEL_PATH = WORKDIR / "src/aemet/artifacts/municipalities.xlsx"
MUNICIPALITIES_JSON_PATH = WORKDIR / "src/aemet/artifacts/municipalities.json"
