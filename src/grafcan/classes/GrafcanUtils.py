"""
Script para interactuar con la API de Grafcan y manejar datos de estaciones meteorológicas.
"""

from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
import requests


class GrafcanUtils:
    """
    Utilidades para interactuar con la API de Grafcan y manejar datos de estaciones meteorológicas.
    """

    @staticmethod
    def fetch_station_data(url: str, headers: dict, logger) -> List[Any]:
        """
        Realiza una solicitud GET a la API y devuelve los resultados si el estado es exitoso.

        :param url: URL de la API.
        :param headers: Encabezados de la solicitud HTTP.
        :param logger: Instancia del logger para registrar eventos.
        :return: Lista de estaciones en formato JSON.
        """
        logger.info(f"Enviando solicitud a la API de Grafcan en {url}")
        response = requests.get(url, headers=headers, timeout=50)
        if response.status_code == 200:
            logger.info(f"Solicitud exitosa. Código de estado: {response.status_code}")
            return response.json().get("results", [])  # type: ignore
        else:
            logger.error(f"Error en la solicitud: código {response.status_code}")
            return []

    @staticmethod
    def save_stations_to_csv(df: pd.DataFrame, output_path: Path, logger) -> None:
        """
        Guarda el DataFrame de estaciones en un archivo CSV en la ubicación especificada.

        :param df: DataFrame de estaciones.
        :param output_path: Ruta donde se guardará el archivo CSV.
        :param logger: Instancia del logger para registrar eventos.
        """
        output_path.parent.mkdir(
            parents=True, exist_ok=True
        )  # Crear directorio si no existe
        df.to_csv(output_path)
        logger.info(f"Archivo guardado en: {output_path}")
