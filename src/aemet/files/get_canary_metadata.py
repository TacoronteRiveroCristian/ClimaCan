"""
Script para extraer los metadatos de los municipios canarios desde la API de AEMET
y registrarlos en un servidor PostgreSQL y archivo JSON.

Los codigos correspondientes a las islas Canarias son el 35 y 38.
"""

import json
import re
import time
from pathlib import Path
from typing import Dict, List, Union

import pandas as pd
import requests
from ctrutils.handler.diagnostic.error_handler import ErrorHandler
from ctrutils.handler.logging.logging_handler import LoggingHandler

from src.aemet.classes.aemet_end_points import AemetEndPoints
from src.aemet.config.config import HEADER, MUNICIPALITIES_JSON_PATH
from src.common.config import postgres_client
from src.common.functions import normalize_text

# Configurar logger
logging_handler = LoggingHandler()
stream = logging_handler.create_stream_handler()
logger = logging_handler.add_handlers([stream])


def get_response(url: str) -> Union[Dict, List]:
    """
    Funcion para realizar una solicitud HTTP y obtener la respuesta en formato JSON.

    :param url: URL de la solicitud HTTP.
    :type url: str
    :return: La respuesta en formato JSON.
    """
    try:
        logger.info(f"Solicitando datos a la URL: {url}")
        response = requests.get(url, headers=HEADER, timeout=20)
        response.raise_for_status()
        logger.info(f"Respuesta recibida correctamente desde {url}")
        return response.json()
    except requests.exceptions.RequestException as e:
        error_msg = f"Error en la solicitud HTTP a {url}: {e}"
        logger.error(error_msg)
        ErrorHandler.throw_error(error_msg, logger)


def get_metadata_from_municipalities() -> List[Dict]:
    """
    Funcion para obtener los metadatos de los municipios canarios desde la API de AEMET.

    :return: Lista de diccionarios con los metadatos de los municipios.
    """
    logger.info("Obteniendo metadatos de los municipios desde AEMET...")

    # Obtener el JSON general de los metadatos de los municipios
    metadata_response = get_response(
        AemetEndPoints.informacion_especifica_municipios()
    )

    # Obtener la URL de datos detallados desde el JSON de respuesta
    metadata_url = metadata_response["datos"]
    logger.info(f"Obteniendo metadatos completos desde la URL: {metadata_url}")

    # Obtener la lista de metadatos
    metadata = get_response(metadata_url)

    if metadata:
        logger.info(f"Se obtuvieron {len(metadata)} registros de municipios.")
    else:
        logger.warning("No se encontraron datos en la respuesta de la API.")

    return metadata


def filter_metadata(metadata: List[Dict]) -> List[Dict]:
    """
    Filtra los metadatos de los municipios canarios.

    :param metadata: Lista con los metadatos de los municipios.
    :type metadata: List[Dict]
    :return: Lista con los metadatos filtrados de municipios canarios.
    """
    logger.info("Filtrando municipios canarios...")

    canary_municipalities = [
        entry for entry in metadata if entry["id"].startswith(("id35", "id38"))
    ]

    logger.info(
        f"Se han filtrado {len(canary_municipalities)} municipios canarios."
    )
    return canary_municipalities


def build_dataframe(metadata: List[Dict]) -> pd.DataFrame:
    """
    Construye un DataFrame a partir de los metadatos de los municipios canarios.

    :param metadata: Lista de metadatos de los municipios canarios.
    :type metadata: List[Dict]
    :return: DataFrame con los metadatos de los municipios canarios.
    """

    def normalize_txt_with_spaces(text: str) -> str:
        return normalize_text(re.sub(r", .*", "", text)).replace(" ", "_")

    logger.info("Construyendo DataFrame con los datos filtrados...")

    df = pd.DataFrame(metadata)

    # Eliminar columnas innecesarias
    columns_to_drop = ["latitud", "id_old", "url", "destacada", "longitud"]
    df.drop(columns=columns_to_drop, inplace=True)

    # Quitar "id" del campo id y convertir en índice
    df["id"] = df["id"].str.replace("id", "")

    # Normalizar nombres de municipios y capitales
    df["capital"] = df["capital"].apply(normalize_txt_with_spaces)
    df["nombre"] = df["nombre"].apply(normalize_txt_with_spaces)

    logger.info(
        f"DataFrame construido con {df.shape[0]} registros y {df.shape[1]} columnas."
    )

    return df


def save_to_json(data: pd.DataFrame, json_path: Path) -> None:
    """
    Guarda el DataFrame en un archivo JSON.

    :param data: DataFrame con los datos a guardar.
    :type data: pd.DataFrame
    """
    logger.info("Guardando DataFrame en un archivo JSON...")
    # Convertir DataFrame a diccionario
    data_dict = data.set_index("id")["nombre"].to_dict()

    # Guardar como archivo JSON
    json_path.parent.mkdir(parents=True, exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as file:
        json.dump(data_dict, file, indent=4, ensure_ascii=False)
    logger.info(f"DataFrame guardado correctamente en el path '{json_path}'.")


def main() -> None:
    """
    Ejecuta el flujo para obtener, procesar y registrar los metadatos de los municipios canarios.

    Este flujo realiza las siguientes acciones:
    - Obtiene los metadatos de los municipios canarios desde la API de AEMET.
    - Filtra y procesa los metadatos para construir un DataFrame.
    - Registra los datos procesados en una base de datos PostgreSQL.

    Maneja excepciones para registrar errores críticos en el proceso.
    """
    start_time = time.time()  # Medir tiempo de ejecución

    try:
        logger.info(
            "Iniciando el proceso de extracción de metadatos de municipios canarios."
        )

        # Obtener los metadatos de los municipios canarios
        metadata = get_metadata_from_municipalities()
        if not metadata:
            logger.warning(
                "No se obtuvieron datos de la API. Terminando ejecución."
            )
            return

        # Filtrar municipios canarios
        canary_metadata = filter_metadata(metadata)

        # Construir DataFrame
        data = build_dataframe(canary_metadata)

        # Registrar en PostgreSQL
        logger.info("Registrando datos en PostgreSQL...")
        postgres_client.write_dataframe(data, "municipios_canarios", "replace")
        logger.info("Datos insertados correctamente en la base de datos.")
        # Generar archivo JSON
        save_to_json(data, MUNICIPALITIES_JSON_PATH)

    except Exception as e:
        error_msg = f"Error en el proceso: {str(e)}"
        logger.critical(error_msg)
        ErrorHandler.throw_error(error_msg, logger)

    end_time = time.time()
    logger.info(
        f"Proceso finalizado en {round(end_time - start_time, 2)} segundos."
    )


if __name__ == "__main__":
    main()
