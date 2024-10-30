"""
Script para obtener los datos de las estaciones Meteorológica de Canarias
correspondientes a la API Grafcan.
"""

import os
from pathlib import Path

import pandas as pd
import requests

# URL de la API de estaciones
url = "https://sensores.grafcan.es/api/v1.0/things/"

# Token de API Grafcan
GRAFCAN_TOKEN = os.getenv("GRAFCAN_TOKEN")
# Path del proyecto raiz
ROOT_PROJECT = Path(os.getenv("ROOT_PROJECT", "/workspaces/ClimaCan"))

# Headers de la solicitud
headers = {"accept": "application/json", "Authorization": f"Api-Key {GRAFCAN_TOKEN}"}

# Realizar la solicitud
response = requests.get(url, headers=headers, timeout=50)

# Verificar el estado de la respuesta
if response.status_code == 200:
    # Obtener el texto de la respuesta
    stations = response.json().get("results", [])

    # Lista de estaciones
    dict_station = []
    # Recorrer lista de estaciones
    for station in stations:
        data_station = {
            "id": station["id"],
            "name": station["name"],
            "description": station["description"],
            "main_purpose": station["properties"]["main_purpose"],
            "serial_number": station["properties"]["serial_number"],
            "anemometer_height": station["properties"]["anemometer_height"],
            "geonica_teletrans_id": station["properties"]["geonica_teletrans_id"],
            "location_set": station["location_set"],
        }

        # Agregar datos a la lista de estaciones
        dict_station.append(data_station)

# Crear DataFrame de estaciones
df_stations = pd.DataFrame(dict_station).set_index("id")

# Generar path y guardar archivo
project_root = Path(ROOT_PROJECT)
data_station_folder = project_root / "src/grafcan/data/stations"
data_station_file = data_station_folder / "stations.csv"

# Crear directorio si no existe
data_station_folder.mkdir(parents=True, exist_ok=True)

# Guardar archivo
df_stations.to_csv(data_station_file)
