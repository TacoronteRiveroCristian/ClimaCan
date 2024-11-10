"""
Clase para obtener y procesar los metadatos de las estaciones de Grafcan y
guardarlos en un archivo CSV.
"""

from typing import List, Optional

import pandas as pd
import unidecode
from ctrutils.handlers.ErrorHandlerBase import ErrorHandler
from ctrutils.handlers.LoggingHandlerBase import LoggingHandler
from requests import get

from conf import GRAFCAN__CSV_FILE_CLASSES_METADATA_STATIONS as CSV_FILE
from conf import GRAFCAN__LOG_FILE_CLASSES_METADATA_STATIONS as LOG_FILE
from conf import HEADER_API_KEY, TIMEOUT


class StationMetadataFetcher:
    """
    Clase para obtener y procesar los metadatos de las estaciones de Grafcan.
    """

    def __init__(self):
        """
        Constructor de la clase.
        """
        self.url = "https://sensores.grafcan.es/api/v1.0/things/"
        self.output_file = CSV_FILE
        self.logger = LoggingHandler(log_file=LOG_FILE).get_logger
        self.error_handler = ErrorHandler()

    def _remove_special_characters(self, text: str) -> str:
        """
        Elimina caracteres especiales y tildes de una cadena de texto.

        :param text: Texto a limpiar.
        :type text: str
        :return: Texto sin caracteres especiales.
        :rtype: str
        """
        if isinstance(text, str):
            text = unidecode.unidecode(text).replace("ñ", "n").replace("Ñ", "N")
        return text

    def _fetch_things_data(self) -> Optional[List[dict]]:
        """
        Obtiene los datos de las estaciones desde la API de Grafcan.

        :return: Lista de estaciones si la solicitud es exitosa, None si ocurre un error.
        :rtype: Optional[List[dict]]
        """
        try:
            self.logger.info("Solicitando datos de estaciones desde la API.")
            response = get(self.url, headers=HEADER_API_KEY, timeout=TIMEOUT)
            response.raise_for_status()
            stations = response.json().get("results", [])
            if not stations:
                self.logger.warning("No se han encontrado estaciones.")
            else:
                self.logger.info(f"Se han encontrado {len(stations)} estaciones.")
            return stations
        except Exception as e:
            self.error_handler.handle_error(
                f"Error al obtener datos de estaciones: {e}", self.logger
            )
            return None

    def _parse_things_data(self, stations: List[dict]) -> Optional[pd.DataFrame]:
        """
        Extrae y organiza los datos de estaciones en un DataFrame.

        :param stations: Lista de estaciones a procesar.
        :type stations: List[dict]
        :return: DataFrame con los datos de las estaciones.
        :rtype: Optional[pd.DataFrame]
        """
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
                self.error_handler.handle_error(
                    f"Falta la clave esperada: {e} en la estación {station.get('id')}.",
                    self.logger,
                )
        df_things = pd.DataFrame(parsed_stations)
        self.logger.info(
            f"Datos de estaciones procesados correctamente: {df_things.shape}."
        )
        return df_things

    def _parse_locations_data(
        self, df_stations: pd.DataFrame
    ) -> Optional[pd.DataFrame]:
        """
        Organiza y transforma los datos de localización en un DataFrame.

        :param df_stations: DataFrame con datos de las estaciones.
        :type df_stations: pd.DataFrame
        :return: DataFrame con los datos de localización.
        :rtype: Optional[pd.DataFrame]
        """
        parse_locations = []
        for _, row in df_stations.iterrows():
            if len(row["location_set"]) > 1:
                self.error_handler.handle_error(
                    "Estación con más de una ubicación, genera inconsistencia en los datos.",
                    self.logger,
                )
            try:
                location_url = row["location_set"][0]
                location_data = get(
                    location_url, headers=HEADER_API_KEY, timeout=TIMEOUT
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
                self.error_handler.handle_error(
                    f"Falta la clave esperada: {e} en la estación {location_data.get('id')}.",
                    self.logger,
                )
        df_locations = pd.DataFrame(parse_locations)
        self.logger.info(
            f"Datos de localización procesados correctamente: {df_locations.shape}."
        )
        return df_locations

    def _merge_dataframes(
        self, df_things: pd.DataFrame, df_locations: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Une los DataFrames de estaciones y ubicaciones, y normaliza texto.

        :param df_things: DataFrame con datos de estaciones.
        :type df_things: pd.DataFrame
        :param df_locations: DataFrame con datos de localización.
        :type df_locations: pd.DataFrame
        :return: DataFrame combinado de estaciones y ubicaciones.
        :rtype: pd.DataFrame
        """
        df_things = df_things.add_prefix("things_")
        df_locations = df_locations.add_prefix("locations_")
        df_merge = pd.merge(df_things, df_locations, left_index=True, right_index=True)
        df_merge.drop("things_location_set", axis=1, inplace=True)

        object_columns = df_merge.select_dtypes(include="object").columns
        df_merge[object_columns] = df_merge[object_columns].applymap(
            self._remove_special_characters
        )
        self.logger.info(
            f"Unión y procesamiento de estaciones y localizaciones completado: {df_merge.shape}."
        )
        return df_merge

    def _save_to_csv(self, df: pd.DataFrame) -> None:
        """
        Guarda el DataFrame resultante en un archivo CSV.

        :param df: DataFrame a guardar.
        :type df: pd.DataFrame
        """
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(self.output_file, index=False)
        self.logger.info(
            f"Archivo guardado con éxito en la ubicación {self.output_file}."
        )

    def run(self):
        """
        Ejecuta el flujo completo de obtención, procesamiento y almacenamiento de metadatos.
        """
        self.logger.info("Iniciando proceso de obtención y procesamiento de metadatos.")
        stations = self._fetch_things_data()
        if stations is None:
            self.logger.error("No se pudieron obtener datos de las estaciones.")
            return
        df_stations = self._parse_things_data(stations)
        if df_stations is None or df_stations.empty:
            self.logger.error("No se pudieron procesar los datos de estaciones.")
            return
        df_locations = self._parse_locations_data(df_stations)
        if df_locations is None or df_locations.empty:
            self.logger.error("No se pudieron procesar los datos de localización.")
            return
        df_merged = self._merge_dataframes(df_stations, df_locations)
        self._save_to_csv(df_merged)
        self.logger.info(
            "Proceso de obtención y procesamiento de metadatos completado.\n"
        )


if __name__ == "__main__":
    fetcher = StationMetadataFetcher()
    fetcher.run()
