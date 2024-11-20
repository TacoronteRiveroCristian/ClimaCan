"""
Script que se encarga de leer el fichero CSV donde contiene todos los metadatos de las estaciones
y registra uno a uno la última observacion de cada estacion en un servidor InfluxDB.
"""

from pathlib import Path
from typing import Dict, List

import pandas as pd
from ctrutils.handlers.LoggingHandlerBase import LoggingHandler

from conf import ERROR_HANDLER, GRAFCAN__CSV_FILE_CLASSES_METADATA_STATIONS
from conf import GRAFCAN__LOG_FILE_SCRIPT_WRITE_LAST_OBSERVATIONS as LOG_FILE
from conf import GRAFCAN_DATABASE_NAME
from conf import INFLUXDB_CLIENT as client
from conf import LOG_BACKUP_PERIOD, LOG_RETENTION_PERIOD
from src.common.functions import normalize_text
from src.grafcan.classes.Exceptions import DataFetchError
from src.grafcan.classes.FetchObservationsLast import FetchObservationsLast

# Configurar logger
handler = LoggingHandler(
    log_file=LOG_FILE,
    log_backup_period=LOG_BACKUP_PERIOD,
    log_retention_period=LOG_RETENTION_PERIOD,
)
LOGGER = handler.configure_logger()

# Crear el objeto FetchObservationsLast
fetcher = FetchObservationsLast()


def read_stations_csv(csv_file: Path) -> pd.DataFrame:
    """
    Lee un archivo CSV y lo convierte en un DataFrame de Pandas.

    :param csv_file: Ruta del archivo CSV.
    :type csv_file: Path
    :return: DataFrame de Pandas con los datos del archivo CSV.
    :rtype: pd.DataFrame
    """
    LOGGER.info(f"Leyendo archivo CSV desde {csv_file}")
    df = pd.read_csv(csv_file, index_col=None).set_index("thing_id")
    df.sort_index(inplace=True)

    # Eliminar cualquier columna que no sea nombrada correctamente
    try:
        df = df.loc[:, ~df.columns.str.contains("^Unnamed")]
    except Exception as e:
        raise Exception(
            f"Ha ocurrido un error al intentar descartar las columnas '^Unnamed'.: {e}"
        ) from e

    LOGGER.info(f"Archivo CSV leido correctamente, {len(df)} estaciones cargadas.")
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
    LOGGER.info("Inicio del proceso de registro de observaciones en InfluxDB.")

    # Leer el DataFrame de los metadatos de las estaciones
    df_stations = read_stations_csv(GRAFCAN__CSV_FILE_CLASSES_METADATA_STATIONS)

    # Recorrer cada fila para obtener el indice y los metadatos de cada estacion
    for index, row in df_stations.iterrows():
        LOGGER.info(f"Procesando estacion con ID '{index}'.")

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
                ERROR_HANDLER.handle_error(warning_message, LOGGER, exit_code=2)
                continue

            LOGGER.info(
                f"Registrando observacion en measurement '{measurement}' para estacion con ID '{index}'."
            )

            # Registrar datos en el servidor InfluxDB
            client.write_points(
                database=GRAFCAN_DATABASE_NAME,
                points=data_points,
            )
            LOGGER.info(
                f"Observacion registrada correctamente en InfluxDB para measurement '{measurement}'."
            )

        except DataFetchError as e:
            warning_message = f"Error al obtener datos para la estacion con ID '{index}': '{e}'"
            ERROR_HANDLER.handle_error(warning_message, LOGGER, exit_code=2)
            continue  # Continuar con la siguiente estacion en caso de error de obtencion de datos
        except Exception as e:
            warning_message = f"Error inesperado al procesar la estacion con ID '{index}': '{e}'"
            ERROR_HANDLER.handle_error(warning_message, LOGGER, exit_code=2)
            continue  # Continuar con la siguiente estacion en caso de error general

    LOGGER.info("Proceso de registro de observaciones completado.\n")
