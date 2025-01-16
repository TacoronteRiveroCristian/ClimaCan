"""
"""


class AEMETEndpoints:
    """
    Clase para manejar los endpoints de la API de AEMET.
    Proporciona metodos para generar las URLs completas con los parametros necesarios.
    """

    BASE_URL = "https://opendata.aemet.es/opendata"

    # Variables de clase para los endpoints
    PREDICCION_MUNICIPIO_HORARIA = (
        "/api/prediccion/especifica/municipio/horaria/{municipio}"
    )

    @classmethod
    def prediccion_municipio_horaria(cls, municipio: str) -> str:
        """
        Devuelve la URL completa del endpoint de predicción horaria para un municipio.
        :param municipio: Codigo del municipio (CPRO + CMUN).
        :return: URL completa con el municipio rellenado.
        """
        return f"{cls.BASE_URL}{cls.PREDICCION_MUNICIPIO_HORARIA.format(municipio=municipio)}"
