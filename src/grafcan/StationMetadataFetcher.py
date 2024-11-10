"""
"""

from typing import List, Optional

import pandas as pd
import unidecode
from ctrutils.handlers.ErrorHandlerBase import ErrorHandler
from ctrutils.handlers.LoggingHandlerBase import LoggingHandler
from requests import get

from conf import GRAFCAN__CSV_FILE_METADATA_STATIONS as CSV_FILE
from conf import GRAFCAN__LOG_FILE_METADATA_STATIONS as LOG_FILE
from conf import (
    GRAFCAN__TIMEOUT_METADATA_STATIONS,
    GRAFCAN_NAME_DATABASE_METADATA_STATIONS,
    GRAFCAN_NAME_MEASUREMENT_METADATA_STATIONS,
    HEADERS,
    INFLUXDB_CLIENT,
    WORKING_DIR,
)


class StationMetadataFetcher:
    def __init__(self):
        # Configuraciones y herramientas
        # End point de la API para extraer informacion de las estaciones
        self.url = "https://sensores.grafcan.es/api/v1.0/things/"
        # Archivos de salida .csv
        self.output_file = WORKING_DIR / CSV_FILE
        # Herramientas de manejo de logs y errores
        self.logger = LoggingHandler(log_file=WORKING_DIR / LOG_FILE).get_logger
        self.error_handler = ErrorHandler()
        self.client = INFLUXDB_CLIENT

    def remove_special_characters(self, text: str) -> str:
        """Elimina caracteres especiales y tildes de una cadena de texto."""
        if isinstance(text, str):
            text = unidecode.unidecode(text).replace("ñ", "n").replace("Ñ", "N")
        return text

    def fetch_things_data(self) -> Optional[List]:
        """Obtiene los datos de las estaciones desde la API de Grafcan."""
        try:
            response = get(
                self.url, headers=HEADERS, timeout=GRAFCAN__TIMEOUT_METADATA_STATIONS
            )
            response.raise_for_status()
            stations = response.json().get("results", [])
            if not stations:
                self.error_handler.handle_error(
                    "No se han encontrado estaciones", self.logger
                )
            else:
                self.logger.info(f"Se han encontrado {len(stations)} estaciones")
            return stations
        except Exception as e:
            self.error_handler.handle_error(str(e), self.logger)
            return None

    def parse_things_data(self, stations: List) -> Optional[pd.DataFrame]:
        """Extrae y organiza los datos de estaciones en un DataFrame."""
        parsed_stations = []
        for station in stations:
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
                parsed_stations.append(station_data)
            except KeyError as e:
                error_message = (
                    f"Falta la clave esperada: {e} en la estación {station.get('id')}"
                )
                self.error_handler.handle_error(error_message, self.logger)

        df_things = pd.DataFrame(parsed_stations)
        self.logger.info(
            f"Datos de estaciones procesados correctamente: {df_things.shape}"
        )
        return df_things

    def parse_locations_data(self, df_stations: pd.DataFrame) -> Optional[pd.DataFrame]:
        """Organiza y transforma los datos de localización en un DataFrame."""
        parse_locations = []
        for _, row in df_stations.iterrows():
            if len(row["location_set"]) > 1:
                self.error_handler.handle_error(
                    "Estación con más de una ubicación, genera inconsistencia en los datos",
                    self.logger,
                )
            try:
                location_url = row["location_set"][0]
                location_data = get(
                    location_url,
                    headers=HEADERS,
                    timeout=GRAFCAN__TIMEOUT_METADATA_STATIONS,
                ).json()
                metadata_location = {
                    "id": location_data["id"],
                    "name": location_data["name"],
                    "description": location_data["description"],
                    "longitude": location_data["location"]["coordinates"][0],
                    "latitude": location_data["location"]["coordinates"][1],
                }
                parse_locations.append(metadata_location)
            except KeyError as e:
                error_message = f"Falta la clave esperada: {e} en la estación {location_data.get('id')}"
                self.error_handler.handle_error(error_message, self.logger)

        df_locations = pd.DataFrame(parse_locations)
        self.logger.info(
            f"Datos de localización procesados correctamente: {df_locations.shape}"
        )
        return df_locations

    def merge_dataframes(
        self, df_things: pd.DataFrame, df_locations: pd.DataFrame
    ) -> pd.DataFrame:
        """Une los DataFrames de estaciones y ubicaciones, y normaliza texto."""
        # Agregar prefijos para diferenciar las columnas
        df_things = df_things.add_prefix("things_")
        df_locations = df_locations.add_prefix("locations_")
        # Unir los DataFrames
        df_merge = pd.merge(df_things, df_locations, left_index=True, right_index=True)
        # Eliminar la columna "things_location_set" de la cual se extrajo los datos de locations
        df_merge.drop("things_location_set", axis=1, inplace=True)

        # Normalizar texto
        object_columns = df_merge.select_dtypes(include="object").columns
        df_merge[object_columns] = df_merge[object_columns].applymap(
            self.remove_special_characters
        )

        self.logger.info(
            f"Unión y procesamiento de estaciones y localizaciones completado: {df_merge.shape}"
        )
        return df_merge

    def save_to_csv(self, df: pd.DataFrame) -> None:
        """Guarda el DataFrame resultante en un archivo CSV."""
        # Crear carpeta de datos donde se va a almacenar el archivo
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(self.output_file, index=False)
        self.logger.info(
            f"Archivo guardado con éxito en la ubicación {self.output_file}"
        )

        # Guardar datos en servidor InfluxDB
        self.client.write_points(
            database=GRAFCAN_NAME_DATABASE_METADATA_STATIONS,
            measurement=GRAFCAN_NAME_MEASUREMENT_METADATA_STATIONS,
            data=df,
        )
        self.logger.info(
            f"Datos guardados en InfluxDB:{GRAFCAN_NAME_DATABASE_METADATA_STATIONS}/{GRAFCAN_NAME_MEASUREMENT_METADATA_STATIONS}"
        )

    def run(self):
        """Ejecuta el flujo completo de obtención, procesamiento y almacenamiento de metadatos."""
        self.logger.info("Iniciando proceso de obtención y procesamiento de metadatos")
        stations = self.fetch_things_data()
        if stations is None:
            self.logger.error("No se pudieron obtener datos de las estaciones")
            return
        df_stations = self.parse_things_data(stations)
        if df_stations is None or df_stations.empty:
            self.logger.error("No se pudieron procesar los datos de estaciones")
            return
        df_locations = self.parse_locations_data(df_stations)
        if df_locations is None or df_locations.empty:
            self.logger.error("No se pudieron procesar los datos de localización")
            return
        df_merged = self.merge_dataframes(df_stations, df_locations)
        self.save_to_csv(df_merged)
        self.logger.info(
            "Proceso de obtención y procesamiento de metadatos completado\n"
        )


if __name__ == "__main__":
    fetcher = StationMetadataFetcher()
    fetcher.run()
