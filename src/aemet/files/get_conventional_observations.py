"""
Script para obtener las observaciones convencionales de las Islas Canarias y
almacenarlas en una base de datos de InfluxDB. Cada estacion meteorologica
corresponde a una tabla de la base de datos.
"""

import re

import pandas as pd
from ctrutils.database.influxdb.InfluxdbOperation import InfluxdbOperation
from ctrutils.handler.diagnostic.error_handler import ErrorHandler
from ctrutils.handler.logging.logging_handler import LoggingHandler

from src.aemet.classes.aemet_end_points import AemetEndPoints
from src.aemet.classes.aemet_fields import AemetFields
from src.aemet.classes.data_handler import AemetBaseHandler
from src.aemet.config.config import TOKEN
from src.common.config import INFLUXDB_HOST, INFLUXDB_PORT, INFLUXDB_TIMEOUT
from src.common.functions import normalize_text

# Base de datos para almacenar las observaciones convencionales
DATABASE = "aemet_conventional_observations"

# Latitud y longitud de las Islas Canarias para realizar el filtrado
LATITUDE = {"min": 27, "max": 29}
LONGITUDE = {"min": -19, "max": -13}

# Inicializar Logger
logging_handler = LoggingHandler()
stream = logging_handler.create_stream_handler()
logger = logging_handler.add_handlers([stream])

# Inicializar clases
aemet = AemetBaseHandler(token=TOKEN)
influxdb = InfluxdbOperation(
    host=INFLUXDB_HOST, port=INFLUXDB_PORT, timeout=INFLUXDB_TIMEOUT
)


def normalize_location(text: str) -> str:
    """
    Normaliza un texto de ubicacion reemplazando caracteres especiales y estandarizando el formato.

    :param text: str - Texto original de la ubicacion.
    :return: str - Texto normalizado.
    """
    txt = normalize_text(text)
    txt = re.sub(
        r"[ \-\/\.\(\)]+", "_", txt
    )  # Sustituir espacios y símbolos por "_"
    txt = re.sub(
        r"_{2,}", "_", txt
    )  # Eliminar múltiples guiones bajos consecutivos
    return txt.strip(
        "_"
    ).lower()  # Eliminar "_" al inicio y final, convertir a minúsculas


def fetch_observations(url: str) -> list:
    """
    Obtiene los datos de observaciones convencionales desde la API de AEMET.

    :param url: str - URL del endpoint de AEMET.
    :return: list - Lista de estaciones meteorologicas.
    :raises ValueError: Si la clave "data" está vacía.
    """
    logger.info(
        "Obteniendo datos de observaciones convencionales desde AEMET..."
    )
    response = aemet.fetch_data(url)
    data = response.get("data")

    if data == [{}]:
        raise ValueError("No existe la clave 'data' en la respuesta de la API.")

    logger.info(f"Se han obtenido '{len(data)}' estaciones meteorologicas.")
    return data


def filter_canary_stations(data: list) -> pd.DataFrame:
    """
    Filtra las estaciones meteorologicas que pertenecen a las Islas Canarias.

    :param data: list - Lista de estaciones meteorologicas.
    :return: pd.DataFrame - DataFrame con las estaciones de Canarias.
    """
    canary_stations = [
        station
        for station in data
        if station["idema"].startswith("C")
        or (
            LATITUDE["min"] <= station["lat"] <= LATITUDE["max"]
            and LONGITUDE["min"] <= station["lon"] <= LONGITUDE["max"]
        )
    ]

    logger.info(
        f"Se han filtrado '{len(canary_stations)}' estaciones en Canarias."
    )
    return pd.DataFrame(canary_stations)


def preprocess_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Procesa el DataFrame aplicando normalizacion y renombrando columnas.

    :param df: pd.DataFrame - DataFrame con los datos meteorologicos.
    :return: pd.DataFrame - DataFrame procesado.
    """
    df = AemetFields.rename_dataframe_columns(df, True)
    df.set_index("fecha_observacion", inplace=True)
    df.index = pd.to_datetime(df.index)
    df["ubicacion"] = df["ubicacion"].apply(normalize_location)

    return df


def store_data_in_influxdb(df: pd.DataFrame) -> None:
    """
    Almacena los datos en InfluxDB dividiendo por ubicacion.

    :param df: pd.DataFrame - DataFrame con los datos meteorologicos.
    """
    for location in df["ubicacion"].unique():
        df_location = df[df["ubicacion"] == location]
        influxdb.write_dataframe(
            database=DATABASE, measurement=location, data=df_location
        )
        logger.info(
            f"Datos almacenados en InfluxDB para la ubicacion: '{location}'"
        )


def main():
    """
    Funcion principal que ejecuta el flujo completo: obtener, procesar y almacenar los datos en InfluxDB.
    """
    try:
        url = AemetEndPoints.observacion_convencional_todas()
        data = fetch_observations(url)
        df = filter_canary_stations(data)

        if df.empty:
            logger.warning(
                "No se encontraron estaciones en Canarias. Finalizando ejecucion."
            )
            return

        df = preprocess_dataframe(df)
        store_data_in_influxdb(df)

        logger.info("Proceso completado")

    except Exception as e:
        error_msg = f"Error en el proceso: {str(e)}"
        ErrorHandler.throw_error(error_msg, logger)


if __name__ == "__main__":
    main()
