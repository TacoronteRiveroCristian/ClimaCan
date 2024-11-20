"""
Script para obtener y procesar los metadatos de las estaciones de Grafcan y
guardarlos en un archivo CSV.
"""

from typing import Dict, List, Optional

import pandas as pd
from ctrutils.handlers.LoggingHandlerBase import LoggingHandler
from requests import get

from conf import ERROR_HANDLER
from conf import GRAFCAN__CSV_FILE_CLASSES_METADATA_STATIONS as CSV_FILE
from conf import GRAFCAN__LOG_FILE_CLASSES_METADATA_STATIONS as LOG_FILE
from conf import HEADER_API_KEY, LOG_BACKUP_PERIOD, LOG_RETENTION_PERIOD, TIMEOUT


class FetchLocationsData:
    """Clase para obtener los datos de ubicaciones desde la API de Grafcan."""

    def parse_locations_data(self, location: Dict) -> Optional[pd.DataFrame]:
        """Extrae y organiza los datos de localización en un DataFrame."""
        try:
            metadata_location = {
                "id": location["id"],
                "name": location["name"],
                "description": location["description"],
                "longitude": location["location"]["coordinates"][0],
                "latitude": location["location"]["coordinates"][1],
            }
        except KeyError as e:
            raise KeyError(
                f"Falta la clave esperada: '{e}' en la estación '{location.get('id')}'."
            ) from e
        except Exception as e:
            raise Exception(
                f"Error al procesar la estación '{location.get('id')}': '{e}'"
            ) from e
        else:
            df_locations = pd.DataFrame([metadata_location]).add_prefix("location_")
            return df_locations


class FetchThingsData:
    """Clase para obtener los datos de las estaciones desde la API de Grafcan."""

    def parse_things_data(self, station: Dict) -> Optional[pd.DataFrame]:
        """Extrae y organiza los datos de estaciones en un DataFrame."""
        try:
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
        except KeyError as e:
            raise KeyError(
                f"Falta la clave esperada: '{e}' en la estación '{station.get('id')}'."
            ) from e
        except Exception as e:
            raise Exception(
                f"Error al procesar la estación '{station.get('id')}': '{e}'"
            ) from e
        else:
            df_things = pd.DataFrame([station_data]).add_prefix("thing_")
            return df_things


class FetchHistoricalLocationsData:
    """Clase para obtener informacion historica de las estaciones desde la API de Grafcan."""

    def format_historical_locations_data(self, historical_locations: List) -> List:
        """Formatea la información de localizaciones historicas para Grafcan."""
        formatted_locations = historical_locations["results"]
        for result in formatted_locations:
            list_locations = result["location"]
            if len(list_locations) != 1:
                raise Exception(
                    f"La clave location debe ser de un solo elemento: '{result}'."
                )
            else:
                result["location"] = list_locations[0]
        return formatted_locations


class StationMetadataFetcher(
    FetchLocationsData, FetchThingsData, FetchHistoricalLocationsData
):
    """Clase para obtener y procesar los metadatos de las estaciones de Grafcan."""

    def __init__(self) -> None:
        super().__init__()
        self.historical_locations_url = (
            "https://sensores.grafcan.es/api/v1.0/historicallocations/"
        )
        self.headers = HEADER_API_KEY
        self.timeout = TIMEOUT

        # Configurar logger
        handler = LoggingHandler(
            log_file=LOG_FILE,
            log_backup_period=LOG_BACKUP_PERIOD,
            log_retention_period=LOG_RETENTION_PERIOD,
        )
        self.logger = handler.configure_logger()
        self.error = ERROR_HANDLER

    def get_data_from_api(self, url: str) -> Dict:
        """Obtiene los datos de la API de Grafcan."""
        try:
            self.logger.info(f"Solicitando datos de la API: '{url}'")
            response = get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
        except Exception as e:
            self.logger.error(f"Error al obtener los datos de la API: '{e}'")
            raise
        else:
            self.logger.info(f"Datos obtenidos con éxito de la API: '{url}'")
            return response.json()

    def save_csv(self, df: pd.DataFrame) -> None:
        """Guarda el DataFrame en un archivo CSV."""
        try:
            self.logger.info(f"Guardando datos en el archivo CSV: '{CSV_FILE}'")
            CSV_FILE.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(CSV_FILE, index=True)
            self.logger.info("Datos guardados exitosamente en el archivo CSV.")
        except Exception as e:
            self.logger.error(f"Error al guardar datos en el archivo CSV: '{e}'")
            raise

    def build_row(self, location: Dict) -> pd.DataFrame:
        """Construye una fila de datos combinando información de cosas y ubicaciones."""
        try:
            start_up_station = location["time"]
            response_thing = self.get_data_from_api(location["thing"])
            df_thing = self.parse_things_data(response_thing)

            response_location = self.get_data_from_api(location["location"])
            df_location = self.parse_locations_data(response_location)

            row = pd.concat([df_thing, df_location], axis=1)
            row["start_up_station"] = start_up_station

            self.logger.info(
                f"Datos procesados para la estación ID: '{location['thing']}'"
            )
            return row
        except Exception as e:
            self.logger.error(
                f"Error al procesar la estación '{location['thing']}': '{e}'"
            )
            return None

    def run(self):
        """Ejecuta el proceso de obtención y procesamiento de datos históricos de las estaciones."""
        try:
            self.logger.info(
                "Iniciando el proceso de obtención y procesamiento de datos históricos."
            )
            response_historical_locations = self.get_data_from_api(
                self.historical_locations_url
            )
            historical_location = self.format_historical_locations_data(
                response_historical_locations
            )
        except Exception as e:
            error_message = f"Error al obtener o formatear datos históricos: '{e}'"
            self.error.handle_error(error_message, self.logger)
            return

        stations_data = []
        for n, location in enumerate(historical_location, start=1):
            row = self.build_row(location)
            row.index = [n]
            if row is not None:
                stations_data.append(row)
            else:
                warning_message = f"Omitiendo estación ID: '{location['thing']}' debido a un error en el procesamiento."
                self.error.handle_error(warning_message, self.logger, exit_code=2)
                continue

        try:
            df_historical_locations = pd.concat(stations_data)
            self.save_csv(df_historical_locations)
        except Exception as e:
            error_message = f"Error al guardar datos históricos: '{e}'"
            self.error.handle_error(error_message, self.logger)
        else:
            self.logger.info("Proceso completado exitosamente.\n")


if __name__ == "__main__":
    stations_metadata_fetcher = StationMetadataFetcher()
    stations_metadata_fetcher.run()
