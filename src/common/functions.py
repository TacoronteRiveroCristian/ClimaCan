"""
Script para almacenar funciones comunes entre los distintos ficheros.
"""

import unidecode

from conf import (
    GRAFCAN__MEASUREMENT_NAME_CHECK_TASKS_SCRIPT_MAIN_GRAFCAN,
    TASKS_DATABASE_NAME,
)
from conf import INFLUXDB_CLIENT as client


def normalize_text(text: str) -> str:
    """
    Normaliza el texto eliminando caracteres especiales y reemplazando ñ por n.

    :param text: Texto a normalizar.
    :type text: str
    :return: Texto normalizado.
    :rtype: str
    """
    # Eliminar caracteres especiales y reemplazar ñ/Ñ
    return unidecode.unidecode(text).replace("ñ", "n").replace("Ñ", "N")


def write_status_task(field: str, value: int) -> None:
    """
    Escribe el estado de una tarea en la base de datos de Grafcan.

    :param field: Nombre del campo en la base de datos.
    :type field: str
    :param value: Valor a escribir en el campo.
    :type value: str
    """
    point = [
        {
            "measurement": GRAFCAN__MEASUREMENT_NAME_CHECK_TASKS_SCRIPT_MAIN_GRAFCAN,
            "fields": {field: value},
        }
    ]
    client.write_points(
        points=point,
        database=TASKS_DATABASE_NAME,
    )
