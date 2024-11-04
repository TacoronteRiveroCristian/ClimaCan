"""
Script para obtener la localización, altura y coordenadas de las estaciones meteorológicas
correspondientes a la API Grafcan y guardarlas en un archivo CSV.
"""

import pandas as pd
from ctrutils.handlers.ErrorHandlerBase import ErrorHandler
from ctrutils.handlers.LoggingHandlerBase import LoggingHandler

from conf import GRAFCAN__LOF_FILE_GET_LOCATIONS_OF_STATIONS, HEADERS, WORKING_DIR
from src.grafcan.classes.GrafcanUtils import GrafcanUtils

# Configuración de logger y manejo de errores
log_file = WORKING_DIR / GRAFCAN__LOF_FILE_GET_LOCATIONS_OF_STATIONS
logging_handler = LoggingHandler(log_file=log_file)
logger = logging_handler.get_logger
error_handler = ErrorHandler()

# URL de la API
url = "https://sensores.grafcan.es/api/v1.0/locations/"

# Instanciar la clase GrafcanUtils
grafcan_utils = GrafcanUtils()


def fetch_station_data(url: str, headers: dict, logger) -> list:
    """
    Realiza una solicitud GET a la API y devuelve los datos de estaciones si el estado es exitoso.

    :param url: URL de la API.
    :param headers: Encabezados HTTP para la solicitud.
    :param logger: Instancia del logger para registrar eventos.
    :return: Lista de estaciones en formato JSON.
    """
    stations = grafcan_utils.fetch_station_data(url, headers, logger)
    if len(stations) == 0:
        error_handler.handle_error(
            message="No se han encontrado estaciones en la API", logger=logger
        )
    else:
        logger.info(f"Se han encontrado {len(stations)} estaciones")
    return stations


def extract_coordinates(location: dict) -> pd.Series:
    """
    Extrae las coordenadas (longitud y latitud) de un diccionario de ubicación.

    :param location: Diccionario con la ubicación de una estación.
    :return: Serie con dos elementos: "longitude" y "latitude".
    """
    if isinstance(location, dict) and "coordinates" in location:
        longitude, latitude = location["coordinates"]
        return pd.Series({"longitude": longitude, "latitude": latitude})
    return pd.Series({"longitude": None, "latitude": None})


def parse_station_data(stations: list, logger) -> pd.DataFrame:
    """
    Organiza y transforma los datos de estaciones en un DataFrame.

    :param stations: Lista de estaciones en formato JSON.
    :param logger: Instancia del logger para registrar eventos.
    :return: DataFrame con los datos de estaciones.
    """
    logger.info("Iniciando procesamiento de datos de estaciones")
    df = pd.DataFrame(stations).set_index("id")

    # Ordenar el indice de forma ascendente
    df.sort_index(inplace=True)

    # Extraer coordenadas y eliminar la columna de ubicación original
    df[["longitude", "latitude"]] = df["location"].apply(extract_coordinates)
    df.drop("location", axis=1, inplace=True)
    logger.info("Procesamiento de datos de estaciones completado")
    return df


def save_to_csv(df: pd.DataFrame, logger) -> None:
    """
    Guarda el DataFrame de estaciones en un archivo CSV en la ruta especificada.

    :param df: DataFrame con los datos de estaciones.
    :param logger: Instancia del logger para registrar eventos.
    """
    output_file = WORKING_DIR / "src/grafcan/data/stations/locations_of_stations.csv"
    grafcan_utils.save_stations_to_csv(df, output_file, logger)
    logger.info("Archivo guardado con éxito en la ubicación especificada\n")


if __name__ == "__main__":
    # Obtener datos de estaciones y manejar posibles errores
    stations = fetch_station_data(url, HEADERS, logger)

    # Procesar los datos en un DataFrame
    df_stations = parse_station_data(stations, logger)

    # Guardar el archivo CSV
    save_to_csv(df_stations, logger)
