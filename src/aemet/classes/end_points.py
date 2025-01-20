"""
Modulo para manejar los endpoints de la API de AEMET.
"""


class AemetEndPoints:
    """
    Clase para manejar los endpoints de la API de AEMET.
    Proporciona metodos para generar las URLs completas con los parametros necesarios.
    """

    BASE_URL = "https://opendata.aemet.es/opendata"

    # Variables de clase para los endpoints
    TIME_MUNICIPALITY_PREDICTION = (
        "/api/prediccion/especifica/municipio/horaria/{municipio}"
    )

    @classmethod
    def time_municipality_prediction(cls, municipality: str) -> str:
        """
        Devuelve la URL completa del endpoint de predicción horaria para un municipio.
        :param municipio: Codigo del municipio (CPRO + CMUN).
        :return: URL completa con el municipio rellenado.
        """
        return f"{cls.BASE_URL}{cls.TIME_MUNICIPALITY_PREDICTION.format(municipio=municipality)}"
