"""
Clase para manejar los endpoints de la API de AEMET
"""


class AemetEndPoints:
    """
    Clase para manejar los endpoints de la API de AEMET.
    Proporciona metodos para generar las URLs completas con los parametros necesarios.
    """

    BASE_URL = "https://opendata.aemet.es/opendata"

    # Variables de clase para los endpoints
    PREDICCION_MUNICIPIO_HORARIA = (
        "/api/prediccion/especifica/municipio/horaria/{municipio}"
    )
    OBSERVAION_CONVENCIONAL_TODAS = "/api/observacion/convencional/todas"
    OBSERVAION_CONVENCIONAL_IDEMA = (
        "/api/observacion/convencional/datos/estacion/{idema}"
    )
    INFORMACION_ESPECIFICA_MUNICIPIOS = "/api/maestro/municipios"

    @classmethod
    def prediccion_municipio_horaria(cls, municipio: str) -> str:
        """
        Devuelve la URL completa del endpoint de predicción horaria para un municipio.
        :param municipio: Codigo del municipio. El formato debe ser CPRO + CMUN.
        :return: URL completa con el municipio rellenado.
        """
        return f"{cls.BASE_URL}{cls.PREDICCION_MUNICIPIO_HORARIA.format(municipio=municipio)}"

    @classmethod
    def observacion_convencional_todas(cls) -> str:
        """
        Devuelve la URL completa del endpoint de observación convencional para todas las estaciones.
        :return: URL completa.
        """
        return f"{cls.BASE_URL}{cls.OBSERVAION_CONVENCIONAL_TODAS}"

    @classmethod
    def observacion_convencional_idema(cls, idema: str) -> str:
        """
        Devuelve la URL completa del endpoint de observación convencional para una estacion.
        :param idema: Codigo de la estacion.
        :return: URL completa con el idema rellenado.
        """
        return f"{cls.BASE_URL}{cls.OBSERVAION_CONVENCIONAL_IDEMA.format(idema=idema)}"

    @classmethod
    def informacion_especifica_municipios(cls) -> str:
        """
        Devuelve la URL completa del endpoint de informacion especifica de municipios.
        :return: URL completa.
        """
        return f"{cls.BASE_URL}{cls.INFORMACION_ESPECIFICA_MUNICIPIOS}"
