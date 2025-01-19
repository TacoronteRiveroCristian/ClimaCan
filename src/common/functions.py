"""
Script para almacenar funciones comunes entre los distintos ficheros.
"""

import unidecode


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
