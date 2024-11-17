"""
Clase para obtener el último registro de observaciones de una estación de Grafcan
según su ID y organizarlo en un DataFrame.
"""

from typing import Dict, List, Optional

import pandas as pd
from requests import get

from conf import HEADER_API_KEY, TIMEOUT
from src.grafcan.classes.Exceptions import DataFetchError


class FetchObservationsLast:
    """
    Clase para obtener el último registro de observaciones de una estación de Grafcan
    según su ID y organizarlo en un DataFrame.
    """

    def __init__(self):
        """
        Inicializa la clase con la URL de la API.
        """
        self.url = "https://sensores.grafcan.es/api/v1.0/observations_last/?thing="

    def _get_response(self, thing_id: int) -> Optional[List[dict]]:
        """
        Obtiene los datos más recientes de una estación desde la API de Grafcan.

        :param thing_id: ID de la estación en Grafcan.
        :type thing_id: int
        :return: Lista de observaciones si la solicitud es exitosa, None si ocurre un error.
        :rtype: Optional[List[dict]]
        :raises DataFetchError: Si ocurre un error al obtener los datos de la API.
        """
        url = self.url + str(thing_id)
        try:
            response = get(url, headers=HEADER_API_KEY, timeout=TIMEOUT)
            response.raise_for_status()
            observations = response.json().get("observations", [])

            if not observations:
                raise DataFetchError(
                    f"No se encontraron datos para la estación con ID {thing_id}."
                )
            return observations
        except Exception as e:
            raise DataFetchError(
                f"Error al obtener datos de la estación con ID {thing_id}: {e}"
            ) from e

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

        return df_pivoted

    def fetch_last_observation(self, thing_id: int) -> List[Dict]:
        """
        Ejecuta el flujo completo de obtención y procesamiento de observaciones para una estación específica.

        :param thing_id: ID de la estación en Grafcan.
        :type thing_id: int
        :return: DataFrame con el último registro de observaciones, si la obtención fue exitosa.
        :rtype: pd.DataFrame
        :raises DataFetchError: Si no se pueden extraer los datos.
        """
        # Obtener observaciones de la API
        observations = self._get_response(thing_id)
        if observations is None:
            raise DataFetchError(
                f"No se pudieron extraer datos para la estación con ID {thing_id}."
            )

        # Crear lista de puntos con el nombre de la columna, el valor y su unidad de tiempo
        points = [
            {
                "time": observation["resultTime"],
                "fields": {
                    self._clean_column_name(
                        observation["name"] + "_" + observation["unitOfMeasurement"]
                    ).strip("_"): observation["value"]
                },
            }
            for observation in observations
        ]

        return points


if __name__ == "__main__":
    fetcher = FetchObservationsLast()
    points = fetcher.fetch_last_observation(2)
    print(points)
