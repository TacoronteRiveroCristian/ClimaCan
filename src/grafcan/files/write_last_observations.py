"""
Script que se encarga de leer el fichero CSV donde contiene todos los metadatos de las estaciones
y registra uno a uno la ultima observacion de cada estacion en un servidor InfluxDB.
"""

from pathlib import Path

import pandas as pd
from ctrutils.handlers.ErrorHandlerBase import ErrorHandler
from ctrutils.handlers.LoggingHandlerBase import LoggingHandler

from conf import GRAFCAN__CSV_FILE_CLASSES_METADATA_STATIONS
from conf import GRAFCAN__LOG_FILE_SCRIPT_WRITE_LAST_OBSERVATIONS as LOG_FILE
from conf import GRAFCAN_DATABASE_NAME
from conf import INFLUXDB_CLIENT as client
from src.common.functions import normalize_text
from src.grafcan.classes.FetchObservationsLast import FetchObservationsLast

# Configuración del logger
ERROR_HANDLER = ErrorHandler()
LOGGER = LoggingHandler(log_file=LOG_FILE).get_logger

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
    df = pd.read_csv(csv_file).set_index("things_id")
    LOGGER.info(f"Archivo CSV leído correctamente, {len(df)} estaciones cargadas.")
    return df


def normalize_measurement(text: str) -> str:
    """
    Normaliza el texto eliminando caracteres especiales y espacios en blanco y mayusculas.

    :param text: Texto a normalizar.
    :type text: str
    :return: Texto normalizado.
    :rtype: str
    """
    text = normalize_text(text)
    text = (
        text.replace(" ", "_")
        .replace(",", "")
        .lower()
        .replace("(", "")
        .replace(")", "")
    )
    return text


if __name__ == "__main__":
    LOGGER.info("Inicio del proceso de registro de observaciones en InfluxDB.")

    # Leer el DataFrame de los metadatos de las estaciones
    df_stations = read_stations_csv(GRAFCAN__CSV_FILE_CLASSES_METADATA_STATIONS)

    # Recorrer cada fila para obtener el índice y los metadatos de cada estación
    for index, row in df_stations.iterrows():
        LOGGER.info(f"Procesando estación con ID {index}.")

        # Obtener la observación más reciente de la estación correspondiente
        last_observation = fetcher.fetch_last_observation(index)
        if last_observation.empty:
            warning_message = f"No se encontraron observaciones recientes para la estación con ID {index}."
            ERROR_HANDLER.handle_error(warning_message, LOGGER, exit_code=2)
            continue

        # Obtener diccionario de metadatos de la estación
        station_metadata = row.to_dict()
        # Obtener measurement para esta estación a partir del nombre de la localización
        measurement = normalize_measurement(station_metadata["locations_name"])
        error_message = f"Registrando observación en measurement '{measurement}' para estación con ID {index}."
        ERROR_HANDLER.handle_error(error_message, LOGGER)

        # Registrar datos en el servidor InfluxDB
        try:
            client.write_points(
                database=GRAFCAN_DATABASE_NAME,
                measurement=measurement,
                data=last_observation,
                tags=station_metadata,
            )
            LOGGER.info(
                f"Observación registrada correctamente en InfluxDB para measurement '{measurement}'."
            )
        except Exception as e:
            warning_message = f"Error al registrar observación para estación con ID {index} en measurement '{measurement}': {e}"
            ERROR_HANDLER.handle_error(warning_message, LOGGER, exit_code=2)

    LOGGER.info("Proceso de registro de observaciones completado.")
