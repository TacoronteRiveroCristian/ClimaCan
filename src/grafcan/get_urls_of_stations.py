"""
Script para obtener los datos de las estaciones meteorológicas de Canarias
correspondientes a la API Grafcan y guardarlos en un archivo CSV.
"""

from typing import List, Optional

import pandas as pd
from ctrutils.handlers.ErrorHandlerBase import ErrorHandler
from ctrutils.handlers.LoggingHandlerBase import LoggingHandler

from conf import GRAFCAN__LOF_FILE_GET_URLS_OF_STATIONS, HEADERS, WORKING_DIR
from src.grafcan.classes.GrafcanUtils import GrafcanUtils

# Configuración de logger y manejo de errores
log_file = WORKING_DIR / GRAFCAN__LOF_FILE_GET_URLS_OF_STATIONS
logging_handler = LoggingHandler(log_file=log_file)
logger = logging_handler.get_logger
error_handler = ErrorHandler()

# URL de la API
url = "https://sensores.grafcan.es/api/v1.0/things/"

# Instanciar la clase GrafcanUtils
grafcan_utils = GrafcanUtils()


def fetch_station_data(url: str, headers: dict, logger) -> List:
    """
    Obtiene los datos de las estaciones meteorológicas desde la API Grafcan.

    Realiza una solicitud a la API utilizando la URL y encabezados proporcionados.
    En caso de éxito, devuelve una lista de estaciones en formato JSON.
    Si no se encuentran estaciones, maneja el error y registra un mensaje.

    :param url: URL de la API de Grafcan.
    :param headers: Encabezados HTTP para la solicitud.
    :param logger: Instancia del logger para registrar mensajes y errores.
    :return: Lista de estaciones en formato JSON, si se obtienen con éxito.
    """
    stations = grafcan_utils.fetch_station_data(url, headers, logger)
    if len(stations) == 0:
        error_handler.handle_error(
            message="No se han encontrado estaciones", logger=logger
        )
        return []
    else:
        logger.info(f"Se han encontrado {len(stations)} estaciones")
        return stations


def save_to_csv(df: pd.DataFrame, logger) -> None:
    # Crear path del archivo .csv
    """
    Guarda el DataFrame de estaciones en un archivo CSV en la ruta especificada.

    :param df: DataFrame con los datos de estaciones.
    :param logger: Instancia del logger para registrar eventos.
    """
    output_file = WORKING_DIR / "src/grafcan/data/stations/url_of_stations.csv"
    # Almacenar los datos en el archivo .csv
    grafcan_utils.save_stations_to_csv(df, output_file, logger)
    logger.info("Archivo guardado con éxito en la ubicación especificada\n")


def parse_station_data(stations: List, logger) -> Optional[pd.DataFrame]:
    """
    Extrae y organiza los datos de estaciones en un DataFrame.

    :param stations: Lista de estaciones en formato JSON.
    :param logger: Instancia del logger para registrar eventos.
    :return: DataFrame con los datos de estaciones.
    """
    logger.info("Iniciando procesamiento de datos de estaciones")
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
            logger.error(error_message)
            error_handler.handle_error(message=error_message, logger=logger)

    df = pd.DataFrame(parsed_stations).set_index("id")
    logger.info("Datos de estaciones procesados correctamente")
    return df


if __name__ == "__main__":

    # Obtener datos de estaciones y manejar posibles errores
    stations = fetch_station_data(url, HEADERS, logger)

    # Procesar los datos en un DataFrame
    df_stations = parse_station_data(stations, logger)

    # Guardar el archivo CSV
    save_to_csv(df_stations, logger)
