"""
Script para obtener las predicciones climatologicas de los municipios
especificados en un archivo JSON desde la API de AEMET y registrarlas
en un servidor InfluxDB.
"""

import json
from time import sleep

from ctrutils.database.influxdb.InfluxdbOperation import InfluxdbOperation
from ctrutils.handler.logging.logging_handler import LoggingHandler
from influxdb.client import InfluxDBClientError

from src.aemet.classes.aemet_end_points import AemetEndPoints
from src.aemet.classes.data_handler import AemetPredictionHandler
from src.aemet.config.config import MUNICIPALITIES_JSON_PATH, TOKEN
from src.common.config import INFLUXDB_HOST, INFLUXDB_PORT, INFLUXDB_TIMEOUT

# Configuracion del script
TIME_SLEEP = 1  # Tiempo de espera inicial entre intentos, en segundos
MAX_RETRIES = 10  # Número maximo de intentos para cada municipio


def read_and_write_predictions(
    code: str,
    municipalitie: str,
    handler: AemetPredictionHandler,
    client: InfluxdbOperation,
) -> None:
    """
    Obtiene las predicciones de un municipio según su codigo y las registra en un servidor InfluxDB.

    :param code: Codigo del municipio.
    :param handler: Instancia del manejador de datos de AEMET.
    :param client: Cliente de InfluxDB para registrar los datos.
    :return: None
    """
    # Crear el endpoint y obtener las predicciones para el municipio correspondiente
    url = AemetEndPoints.prediccion_municipio_horaria(code)
    data_frames = handler.process_municipality_data(url)

    # Iterar cada DataFrame y registrarlo en el servidor InfluxDB
    for _, dfs in data_frames.items():
        for measure, df in dfs.items():
            # Todas las columnas son object, por lo que en la siguiente linea se
            # intenta convertir las columnas a float. Las que generen un error,
            # se quedan como estan, de tipo object
            for col in df.columns:
                try:
                    df[col] = df[col].astype(float)
                except Exception:
                    pass
            # Registrar el DataFrame en el servidor InfluxDB
            client.write_dataframe(
                database=municipalitie,
                measurement=measure,
                data=df,
            )


def fetch_predictions(
    municipalities: dict,
    handler: AemetPredictionHandler,
    client: InfluxdbOperation,
    logger,
):
    """
    Itera sobre todos los municipios para obtener sus predicciones climatologicas.

    :param municipalities: Diccionario con los datos de los municipios.
    :param handler: Instancia del manejador de datos de AEMET.
    :param client: Cliente de InfluxDB para registrar los datos.
    :param logger: Instancia del logger.
    :return: None
    """
    logger.info(
        "Iniciando el proceso de obtencion de predicciones climatologicas..."
    )

    for code, municipalitie in municipalities.items():
        # Intentos de obtener las predicciones
        retries = 0
        success = False

        while retries < MAX_RETRIES and not success:
            try:
                # Llamar a la funcion para obtener y registrar las predicciones
                read_and_write_predictions(
                    code, municipalitie["municipalities"], handler, client
                )
                success = True  # Si no ocurre un error, se considera exitoso
                logger.info(
                    f"Se han obtenido las predicciones para el municipio: '{municipalitie['municipalities']}'"
                )
            except InfluxDBClientError as e:
                logger.error(
                    f"Error al registrar las predicciones para el municipio '{municipalitie['municipalities']}': {e}. "
                    f"Se debe de revisar el formato de los datos debido a los cambios constantes de la API AEMET."
                )
                break
            except Exception as e:
                retries += 1
                logger.error(
                    f"Error al obtener las predicciones para el municipio '{municipalitie['municipalities']}': {e}. "
                    f"Intento {retries}/{MAX_RETRIES}."
                )
                # Aumentar el tiempo de espera progresivamente para evitar saturar la API
                sleep(TIME_SLEEP * retries * 2.5)
            finally:
                if retries == MAX_RETRIES and not success:
                    logger.warning(
                        f"Se supero el número maximo de intentos para el municipio '{municipalitie['municipalities']}'."
                    )

    logger.info("Proceso completado.")


if __name__ == "__main__":
    # Configurar el logger
    logging_handler = LoggingHandler()
    stream = logging_handler.create_stream_handler()
    logger = logging_handler.add_handlers([stream])

    # Instanciar manejador de AEMET para obtener las predicciones
    handler = AemetPredictionHandler(TOKEN)

    # Instanciar cliente de InfluxDB
    client = InfluxdbOperation(
        host=INFLUXDB_HOST,
        port=INFLUXDB_PORT,
        timeout=INFLUXDB_TIMEOUT,
    )

    # Cargar el archivo JSON con los datos de los municipios
    with open(MUNICIPALITIES_JSON_PATH, "r", encoding="utf-8") as file:
        municipalities = json.load(file)

    # Ejecutar el proceso de obtencion de predicciones
    fetch_predictions(municipalities, handler, client, logger)
