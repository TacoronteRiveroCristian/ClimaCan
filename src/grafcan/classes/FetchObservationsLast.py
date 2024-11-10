"""
Clase para obtener el últimos registro de observaciones de una estación de Grafcan
según su ID y organizarlo en un DataFrame.
"""

from typing import List, Optional

import pandas as pd
from ctrutils.handlers.ErrorHandlerBase import ErrorHandler
from ctrutils.handlers.LoggingHandlerBase import LoggingHandler
from requests import get

from conf import GRAFCAN__LOG_FILE_CLASSES_OBSERVATIONS_LAST as LOG_FILE
from conf import HEADER_API_KEY, INFLUXDB_CLIENT, TIMEOUT


class FetchObservationsLast:
    """
    Clase para obtener el último registro de observaciones de una estación de Grafcan
    según su ID y organizarlo en un DataFrame.
    """

    def __init__(self):
        """
        Inicializa la clase con la URL de la API y herramientas de log y manejo de errores.
        """
        self.url = "https://sensores.grafcan.es/api/v1.0/observations_last/?thing="
        self.logger = LoggingHandler(log_file=LOG_FILE).get_logger
        self.error_handler = ErrorHandler()
        self.client = INFLUXDB_CLIENT

    def _get_response(self, thing_id: int) -> Optional[List[dict]]:
        """
        Obtiene los datos más recientes de una estación desde la API de Grafcan.

        :param thing_id: ID de la estación en Grafcan.
        :type thing_id: int
        :return: Lista de observaciones si la solicitud es exitosa, None si ocurre un error.
        :rtype: Optional[List[dict]]
        """
        url = self.url + str(thing_id)
        try:
            self.logger.info(
                f"Solicitando datos de la estación con ID {thing_id} desde {url}"
            )
            response = get(url, headers=HEADER_API_KEY, timeout=TIMEOUT)
            response.raise_for_status()
            observations = response.json().get("observations", [])

            if not observations:
                self.logger.warning(
                    f"No se encontraron datos para la estación con ID {thing_id}"
                )
            else:
                self.logger.info(
                    f"Datos obtenidos con éxito: {response.json().get('count')} métricas encontradas."
                )
            return observations
        except Exception as e:
            error_message = (
                f"Error al obtener datos de la estación con ID {thing_id}: {e}"
            )
            self.error_handler.handle_error(error_message, self.logger)
            return None

    def _clean_column_name(self, name: str) -> str:
        """
        Limpia y formatea el nombre de la columna eliminando espacios y caracteres especiales.

        :param name: Nombre de la columna a limpiar.
        :type name: str
        :return: Nombre de columna formateado.
        :rtype: str
        """
        return (
            name.lower()
            .replace(" ", "_")
            .replace(".", "")
            .replace("(", "")
            .replace(")", "")
            .replace("°", "")
        )

    def _parse_observations(self, observations: List[dict]) -> pd.DataFrame:
        """
        Procesa las observaciones de la estación en un DataFrame con un índice de tiempo único.

        :param observations: Lista de observaciones a procesar.
        :type observations: List[dict]
        :return: DataFrame con los datos de observación formateados.
        :rtype: pd.DataFrame
        """
        # Crear DataFrame a partir de las observaciones
        df = pd.DataFrame(observations)[
            ["name", "value", "unitOfMeasurement", "resultTime"]
        ]

        # Limpiar y formatear el nombre de las columnas
        df["column_name"] = (df["name"] + "_" + df["unitOfMeasurement"]).apply(
            self._clean_column_name
        )

        # Pivotar el DataFrame para que cada métrica sea una columna, usando 'resultTime' como índice
        df_pivoted = df.pivot(index="resultTime", columns="column_name", values="value")

        # Convertir el índice de tiempo a formato datetime
        df_pivoted.index = pd.to_datetime(df_pivoted.index)

        self.logger.info(
            f"Observaciones procesadas en DataFrame con {df_pivoted.shape[1]} columnas."
        )

        return df_pivoted

    def fetch_last_observation(self, thing_id: int) -> pd.DataFrame:
        """
        Ejecuta el flujo completo de obtención y procesamiento de observaciones para una estación específica.

        :param thing_id: ID de la estación en Grafcan.
        :type thing_id: int
        :return: DataFrame con el último registro de observaciones, si la obtención fue exitosa.
        :rtype: pd.DataFrame
        """
        self.logger.info(
            f"Iniciando proceso de obtención y procesamiento de datos para la estación con ID {thing_id}."
        )

        # Obtener observaciones de la API
        observations = self._get_response(thing_id)
        if observations is None:
            error_message = (
                f"No se pudieron extraer datos para la estación con ID {thing_id}."
            )
            self.error_handler.handle_error(error_message, self.logger)
            return pd.DataFrame()  # Devuelve un DataFrame vacío en caso de error

        # Procesar las observaciones y devolver el DataFrame resultante
        dataframe = self._parse_observations(observations)

        self.logger.info(
            f"Proceso completado para la estación con ID {thing_id}. DataFrame listo para su uso.\n"
        )

        return dataframe


if __name__ == "__main__":
    fetcher = FetchObservationsLast()
    df = fetcher.fetch_last_observation(2)
    print(df)
