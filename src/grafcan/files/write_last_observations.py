"""
Script que se encarga de leer el fichero CSV donde contiene todos los metadatos de las estaciones
y registra uno a uno la última observacion de cada estacion en un servidor InfluxDB.
"""

from pathlib import Path
from typing import Dict, List

import pandas as pd
from ctrutils.database.influxdb.InfluxdbOperation import InfluxdbOperation
from ctrutils.handlers.ErrorHandlerBase import ErrorHandler
from ctrutils.handlers.LoggingHandlerBase import LoggingHandler

from src.grafcan.classes.fetch_observations_last import FetchObservationsLast
from src.common.config import INFLUXDB_HOST, INFLUXDB_PORT, INFLUXDB_TIMEOUT
from src.common.functions import normalize_text
from grafcan.classes.exceptions import DataFetchError
from src.grafcan.config.config import CSV_FILE_CLASSES_METADATA_STATIONS, TOKEN

# Configurar logger
logging_handler = LoggingHandler()
stream = logging_handler.create_stream_handler()
logger = logging_handler.add_handlers([stream])

# Configurar manejador de errores
error_handler = ErrorHandler()

# Crear el objeto FetchObservationsLast
fetcher = FetchObservationsLast(TOKEN)

# Configurar el cliente de InfluxDB
client = InfluxdbOperation(
    host=INFLUXDB_HOST,
    port=INFLUXDB_PORT,
    timeout=INFLUXDB_TIMEOUT,
)


def read_stations_csv(csv_file: Path) -> pd.DataFrame:
    """
    Lee un archivo CSV y lo convierte en un DataFrame de Pandas.

    :param csv_file: Ruta del archivo CSV.
    :type csv_file: Path
    :return: DataFrame de Pandas con los datos del archivo CSV.
    :rtype: pd.DataFrame
    """
    logger.info(f"Leyendo archivo CSV desde {csv_file}")
    df = pd.read_csv(csv_file, index_col=None).set_index("thing_id")
    df.sort_index(inplace=True)

    # Eliminar cualquier columna que no sea nombrada correctamente
    try:
        df = df.loc[:, ~df.columns.str.contains("^Unnamed")]
    except Exception as e:
        raise Exception(
            f"Ha ocurrido un error al intentar descartar las columnas '^Unnamed'.: {e}"
        ) from e

    logger.info(
        f"Archivo CSV leido correctamente, {len(df)} estaciones cargadas."
    )
    return df


def normalize_measurement(text: str) -> str:
    """
    Normaliza el texto eliminando caracteres especiales y espacios en blanco y mayúsculas.

    :param text: Texto a normalizar.
    :type text: str
    :return: Texto normalizado.
    :rtype: str
    """
    text = normalize_text(text)
    return (
        text.replace(" ", "_")
        .replace(",", "")
        .lower()
        .replace("(", "")
        .replace(")", "")
    )


def add_features_to_points(
    points: List[Dict], measurement: str, tags: Dict
) -> List[Dict]:
    """
    Agrega clave measurement a cada diccionario y elimina claves en "fields" con valores nulos.

    :param points: Lista de diccionarios con datos de la estación.
    :type points: List[Dict]
    :param measurement: Nombre del tipo de medición.
    :type measurement: str
    :return: Lista de diccionarios con la clave measurement y sin claves nulas.
    :rtype: List[Dict]
    """
    # Agregar clave measurement a cada diccionario y eliminar claves en "fields" con valores nulos
    valid_points = []
    # Agregar clave measurement y tags a cada diccionario y eliminar toda clave que contenga valor nulo
    for point in points:
        # Agregar measurement
        point["measurement"] = measurement
        # Agregar tags
        point["tags"] = tags

        # Crear lista de claves a eliminar en el caso de que sean nulos sus valores
        keys_to_remove = [
            key for key, value in point["fields"].items() if value is None
        ]
        for key in keys_to_remove:
            del point[key]

        # Comprobar si "fields" tiene al menos un valor; si es asi, agregar a los puntos válidos
        if point["fields"]:
            valid_points.append(point)

    # Solo devolver puntos con "fields" no vacios
    return valid_points


if __name__ == "__main__":
    logger.info("Inicio del proceso de registro de observaciones en InfluxDB.")

    # Leer el DataFrame de los metadatos de las estaciones
    df_stations = read_stations_csv(CSV_FILE_CLASSES_METADATA_STATIONS)

    # Recorrer cada fila para obtener el indice y los metadatos de cada estacion
    for index, row in df_stations.iterrows():
        logger.info(f"Procesando estacion con ID '{index}'.")

        try:
            # Obtener la observacion más reciente de la estacion correspondiente
            last_observation = fetcher.fetch_last_observation(index)
            # Obtener diccionario de metadatos de la estacion
            station_metadata = row.to_dict()
            # Obtener measurement para esta estacion a partir del nombre de la localizacion
            measurement = station_metadata["location_name"]
            # Agregar el measurement a cada diccionario de la lista de puntos y eliminar los valores nulos
            data_points = add_features_to_points(
                last_observation, measurement, station_metadata
            )

            # Comprobar si hay datos disponibles, sino continuar con la siguiente estacion
            if len(data_points) == 0:
                warning_message = f"No se han encontrado datos para la estacion con ID '{index}'."
                logger.warning(warning_message)
                continue

            logger.info(
                f"Registrando observacion en measurement '{measurement}' para estacion con ID '{index}'."
            )

            # Registrar datos en el servidor InfluxDB
            client.write_points(
                database="grafcan",
                points=data_points,
            )
            logger.info(
                f"Observacion registrada correctamente en InfluxDB para measurement '{measurement}'."
            )

        except DataFetchError as e:
            warning_message = f"Error al obtener datos para la estacion con ID '{index}': '{e}'"
            logger.warning(warning_message)
            continue  # Continuar con la siguiente estacion en caso de error de obtencion de datos
        except Exception as e:
            warning_message = f"Error inesperado al procesar la estacion con ID '{index}': '{e}'"
            logger.warning(warning_message)
            continue  # Continuar con la siguiente estacion en caso de error general

    logger.info("Proceso de registro de observaciones completado.\n")
