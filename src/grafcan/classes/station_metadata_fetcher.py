"""
Clases para obtener los datos de ubicaciones y estaciones desde la API de Grafcan.
"""

from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
from requests import get


class FetchLocationsData:
    """Clase para obtener los datos de ubicaciones desde la API de Grafcan."""

    def parse_locations_data(self, location: Dict) -> Optional[pd.DataFrame]:
        """Extrae y organiza los datos de localización en un DataFrame."""
        metadata_location = {
            "id": location["id"],
            "name": location["name"],
            "description": location["description"],
            "longitude": location["location"]["coordinates"][0],
            "latitude": location["location"]["coordinates"][1],
        }
        return pd.DataFrame([metadata_location]).add_prefix("location_")


class FetchThingsData:
    """Clase para obtener los datos de las estaciones desde la API de Grafcan."""

    def parse_things_data(self, station: Dict) -> Optional[pd.DataFrame]:
        """Extrae y organiza los datos de estaciones en un DataFrame."""
        station_data = {
            "id": station["id"],
            "name": station["name"],
            "description": station["description"],
            "main_purpose": station["properties"].get("main_purpose"),
            "serial_number": station["properties"].get("serial_number"),
            "anemometer_height": station["properties"].get("anemometer_height"),
            "geonica_teletrans_id": station["properties"].get(
                "geonica_teletrans_id"
            ),
            "location_set": station["location_set"],
        }
        return pd.DataFrame([station_data]).add_prefix("thing_")


class FetchHistoricalLocationsData:
    """Clase para obtener informacion historica de las estaciones desde la API de Grafcan."""

    def format_historical_locations_data(
        self, historical_locations: List
    ) -> List:
        """Formatea la información de localizaciones historicas para Grafcan."""
        formatted_locations = historical_locations["results"]
        for result in formatted_locations:
            list_locations = result["location"]
            if len(list_locations) != 1:
                raise ValueError(
                    f"La clave location debe ser de un solo elemento: '{result}'."
                )
            result["location"] = list_locations[0]
        return formatted_locations


class StationMetadataFetcher(
    FetchLocationsData, FetchThingsData, FetchHistoricalLocationsData
):
    """
    Clase para obtener y procesar los metadatos de las estaciones de Grafcan.

    :param token: Token de autenticación para la API de Grafcan.
    :type token: str
    :param timeout: Tiempo máximo de espera para las solicitudes a la API.
    :type timeout: int
    """

    def __init__(self, token: str, timeout: int = 10) -> None:
        self.historical_locations_url = (
            "https://sensores.grafcan.es/api/v1.0/historicallocations/"
        )
        self.token = token
        self.timeout = timeout

    def get_data_from_api(self, url: str) -> Dict:
        """Obtiene los datos de la API de Grafcan."""
        headers = {
            "accept": "application/json",
            "Authorization": f"Api-Key {self.token}",
        }
        response = get(url, headers=headers, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def save_csv(self, df: pd.DataFrame, output_file: Path) -> None:
        """Guarda el DataFrame en un archivo CSV."""
        output_file.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_file, index=True)

    def build_row(self, location: Dict) -> pd.DataFrame:
        """Construye una fila de datos combinando información de cosas y ubicaciones."""
        start_up_station = location["time"]
        response_thing = self.get_data_from_api(location["thing"])
        df_thing = self.parse_things_data(response_thing)

        response_location = self.get_data_from_api(location["location"])
        df_location = self.parse_locations_data(response_location)

        row = pd.concat([df_thing, df_location], axis=1)
        row["start_up_station"] = start_up_station
        return row

    def process_historical_locations(self) -> pd.DataFrame:
        """Procesa los datos históricos de las estaciones de Grafcan."""
        response_historical_locations = self.get_data_from_api(
            self.historical_locations_url
        )
        historical_locations = self.format_historical_locations_data(
            response_historical_locations
        )

        stations_data = []
        for n, location in enumerate(historical_locations, start=1):
            row = self.build_row(location)
            row.index = [n]
            stations_data.append(row)

        return pd.concat(stations_data)
