"""
Script para almacenar funciones comunes entre los distintos ficheros.
"""

import json
from pathlib import Path
from typing import Union

import unidecode
import yaml


def normalize_text(text: str) -> str:
    """
    Normaliza el texto eliminando caracteres especiales y reemplazando ñ por n.

    :param text: Texto a normalizar.
    :type text: str
    :return: Texto normalizado.
    :rtype: str
    """
    # Eliminar caracteres especiales y reemplazar ñ/Ñ
    return unidecode.unidecode(text).replace("ñ", "n").replace("Ñ", "N")


def generate_grafana_yaml(
    json_file_path: str,
    output_file: Union[Path, str],
    influxdb_url="http://climacan-influxdb:$INFLUXDB_PORT",
) -> None:
    """
    Genera un archivo YAML para configurar las bases de datos en Grafana basado en un archivo JSON de municipios.

    :param json_file_path: Ruta al archivo JSON que contiene los municipios.
    :type json_file_path: str
    :param output_file: Ruta donde se guardara el archivo YAML generado.
    :type output_file: Union[Path, str]
    :param influxdb_url: URL de la base de datos InfluxDB.
    :type influxdb_url: str
    """
    # Leer el archivo JSON
    with open(json_file_path, "r", encoding="utf-8") as json_file:
        municipalities = json.load(json_file)

    # Construir la estructura para el YAML
    datasources = []
    for _, details in municipalities.items():
        datasource = {
            "name": details["municipalities"],
            "type": "influxdb",
            "access": "proxy",
            "url": influxdb_url,
            "database": details["municipalities"],
            "editable": False,
        }
        datasources.append(datasource)

    # Estructura final para el archivo YAML
    yaml_data = {"apiVersion": 1, "datasources": datasources}

    if isinstance(output_file, str):
        output_file = Path(output_file)

    # Crear carpeta en caso de que no exista
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as yaml_file:
        yaml.dump(
            yaml_data, yaml_file, default_flow_style=False, sort_keys=False
        )
