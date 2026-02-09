"""
Clase para gestionar los campos del endpoint de AEMET, sus nombres completos y unidades de medida.
"""

from typing import Dict

import pandas as pd


class AemetFields:
    """
    Clase para gestionar los campos del endpoint de AEMET, sus nombres completos y unidades de medida.
    """

    _FIELDS_INFO: Dict[str, Dict[str, str]] = {
        "idema": {"name": "idema", "unit": ""},
        "lon": {"name": "longitud", "unit": "grados"},
        "lat": {"name": "latitud", "unit": "grados"},
        "alt": {"name": "altitud", "unit": "m"},
        "ubi": {"name": "ubicacion", "unit": ""},
        "fint": {"name": "fecha_observacion", "unit": ""},
        "prec": {"name": "precipitacion", "unit": "mm"},
        "pacutp": {"name": "precipitacion_acumulada_disdrometro", "unit": "mm"},
        "pliqtp": {"name": "precipitacion_liquida", "unit": "mm"},
        "psolt": {"name": "precipitacion_solida", "unit": "mm"},
        "vmax": {"name": "velocidad_max_viento", "unit": "m_s"},
        "vv": {"name": "velocidad_media_viento", "unit": "m_s"},
        "vmaxu": {"name": "velocidad_max_viento_ultrasonico", "unit": "m_s"},
        "vvu": {"name": "velocidad_media_viento_ultrasonico", "unit": "m_s"},
        "dv": {"name": "direccion_media_viento", "unit": "grados"},
        "dvu": {"name": "direccion_media_viento_ultrasonico", "unit": "grados"},
        "dmax": {"name": "direccion_viento_max", "unit": "grados"},
        "dmaxu": {"name": "direccion_viento_max_ultrasonico", "unit": "grados"},
        "stdvv": {
            "name": "desviacion_estandar_velocidad_viento",
            "unit": "m_s",
        },
        "stddv": {
            "name": "desviacion_estandar_direccion_viento",
            "unit": "grados",
        },
        "stdvvu": {
            "name": "desviacion_estandar_velocidad_viento_ultrasonico",
            "unit": "m_s",
        },
        "stddvu": {
            "name": "desviacion_estandar_direccion_viento_ultrasonico",
            "unit": "grados",
        },
        "hr": {"name": "humedad_relativa", "unit": "%"},
        "inso": {"name": "duracion_insolacion", "unit": "h"},
        "pres": {"name": "presion", "unit": "hPa"},
        "pres_nmar": {"name": "presion_nivel_mar", "unit": "hPa"},
        "ts": {"name": "temperatura_suelo", "unit": "grados_C"},
        "tss20cm": {"name": "temperatura_subsuelo_20cm", "unit": "grados_C"},
        "tss5cm": {"name": "temperatura_subsuelo_5cm", "unit": "grados_C"},
        "ta": {"name": "temperatura_aire", "unit": "grados_C"},
        "tpr": {"name": "temperatura_punto_rocio", "unit": "grados_C"},
        "tamin": {"name": "temperatura_minima", "unit": "grados_C"},
        "tamax": {"name": "temperatura_maxima", "unit": "grados_C"},
        "vis": {"name": "visibilidad", "unit": "km"},
        "geo700": {"name": "altura_nivel_700hPa", "unit": "m_geopotenciales"},
        "geo850": {"name": "altura_nivel_850hPa", "unit": "m_geopotenciales"},
        "geo925": {"name": "altura_nivel_925hPa", "unit": "m_geopotenciales"},
        "rviento": {"name": "recorrido_viento", "unit": "hm"},
        "nieve": {"name": "espesor_nieve", "unit": "cm"},
    }

    @classmethod
    def has_field(cls, field: str) -> bool:
        """
        Verifica si un campo está en la lista de variables conocidas.

        :param field: str - Nombre del campo a verificar.
        :return: bool - True si el campo existe, False si no.
        """
        return field in cls._FIELDS_INFO

    @classmethod
    def get_renamed_field(cls, field: str, use_long_names: bool = False) -> str:
        """
        Retorna el nombre del campo con su unidad correspondiente.

        :param field: str - Nombre del campo original.
        :param use_long_names: bool - Si True, usa nombres largos (ej: "longitud_grados").
                                    Si False, usa nombres cortos (ej: "lon_grados").
        :return: str - Nombre del campo con su unidad.
        """
        field_info = cls._FIELDS_INFO.get(field, {"name": field, "unit": ""})
        nombre = field_info["name"] if use_long_names else field
        unidad = field_info["unit"]

        return f"{nombre}_{unidad}" if unidad else nombre

    @classmethod
    def rename_dataframe_columns(
        cls, df: pd.DataFrame, use_long_names: bool = False
    ) -> pd.DataFrame:
        """
        Renombra las columnas del DataFrame con nombres y unidades correspondientes.

        :param df: pd.DataFrame - DataFrame con los datos de AEMET.
        :param use_long_names: bool - Si True, usa nombres largos en las columnas.
        :return: pd.DataFrame - DataFrame con columnas renombradas.
        """
        df = df.rename(
            columns={
                col: cls.get_renamed_field(col, use_long_names)
                for col in df.columns
            }
        )
        return df
