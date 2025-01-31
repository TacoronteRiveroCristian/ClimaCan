"""
Clases para manejar las consultas de predicciones provenientes de la API de AEMET.
"""

from typing import Any, Dict, List

import pandas as pd
import requests


class AemetBaseHandler:
    """
    Clase base para manejar las consultas a la API de AEMET.
    """

    def __init__(self, token: str) -> None:
        """
        Inicializa la clase con el token de autenticacion.

        :param token: str - Token de autorizacion para la API de AEMET.
        """
        self.token = token
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self.timeout = 20

    def fetch_data(self, full_url: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Ejecuta una consulta a la API de AEMET y retorna los datos y metadatos en un solo diccionario.

        :param full_url: str - URL completa de la API a consultar.
        :return: Dict[str, List[Dict[str, Any]]] - Diccionario con 'data' y 'metadata'.
        :raises ValueError: Si la consulta no retorna una respuesta valida.
        """
        try:
            response = requests.get(
                full_url, headers=self.headers, timeout=self.timeout
            )
            response.raise_for_status()  # Verifica si hubo errores HTTP

            response = response.json()
            state = response.get("estado")

            if state != 200:
                raise ValueError(f"Estado de la consulta erroneo: {state}")

            # Obtener los datos y metadatos de la respuesta
            data = requests.get(
                response.get("datos"),
                headers=self.headers,
                timeout=self.timeout,
            ).json()
            metadata = requests.get(
                response.get("metadatos"),
                headers=self.headers,
                timeout=self.timeout,
            ).json()

            return {
                "data": data or [{}],
                "metadata": metadata or [{}],
            }

        except requests.RequestException as e:
            raise ValueError(f"Error en la consulta a la API: {e}") from e
        except ValueError as e:
            raise ValueError(
                f"Error al procesar la respuesta de la API: {e}"
            ) from e


class AemetPredictionHandler(AemetBaseHandler):
    """
    Clase para manejar las predicciones de la API de AEMET.
    """

    @staticmethod
    def _parse_simple_hours_column(series: pd.Series) -> pd.Series:
        """
        Parsea la columna de horas simples.

        :param series: pd.Series - Serie de datos de horas simples.
        :return: pd.Series - Serie de datos de horas simples parseadas.
        """
        return series.apply(lambda x: pd.Timedelta(hours=float(x)))

    @staticmethod
    def _parse_time_columns_with_periods(series: pd.Series) -> pd.Series:
        """
        Parsea la columna de horas con periodos.

        :param series: pd.Series - Serie de datos de horas con periodos.
        :return: pd.Series - Serie de datos de horas con periodos parseadas.
        """
        return series.apply(
            lambda x: (
                pd.Timedelta(hours=float(x[:2]))
                if len(x) == 4
                else AemetPredictionHandler._raise_invalid_length_error(x)
            )
        )

    @staticmethod
    def _raise_invalid_length_error(value) -> None:
        """
        Lanza un error si el valor no cumple la longitud esperada.

        :param value: Cualquier valor que no cumpla la longitud esperada.
        :raises ValueError: Siempre que se invoque.
        """
        raise ValueError(
            f"El valor '{value}' no tiene una longitud valida de 4 caracteres."
        )

    @staticmethod
    def _process_wind_data(df: pd.DataFrame) -> pd.DataFrame:
        """
        Procesa los datos de viento.

        :param data: pd.DataFrame - DataFrame con los datos de viento.
        :return: pd.DataFrame - DataFrame con los datos de viento procesados.
        """
        data = df.copy()
        # Rellenar valores nulos con la fila anterior
        data["value"] = data["value"].bfill()
        # Eliminar valores nulos
        data.dropna(inplace=True)
        # Corregir contenido de las columnas
        data["direccion"] = data["direccion"].apply(lambda x: x[0])
        data["velocidad"] = data["velocidad"].apply(lambda x: x[0])

        return data

    def process_municipality_data(
        self, full_url: str
    ) -> Dict[str, pd.DataFrame]:
        """
        Procesa los datos de prediccion para una URL completa específica.

        :param full_url: str - URL completa con endpoint y parametros.
        :return: Diccionario con DataFrames de los datos procesados por medida.
        """
        response = self.fetch_data(full_url)
        # Comprobar si la respuesta contiene datos
        if response["data"] == [{}]:
            raise ValueError(
                f"No se pudieron obtener datos para la URL {full_url}."
            )

        pred = response["data"][0].get("prediccion", {}).get("dia", [])
        results = {}

        for day in pred:
            day_of_pred = day.get("fecha")
            dict_of_pred = {}
            for key, value in day.items():
                if not isinstance(value, list) or not value:
                    # Continuar si la clave no tiene datos procesables
                    continue

                try:
                    # Pasar lista de puntos a formato DataFrame
                    df = pd.DataFrame(value)

                    # Agregar la fecha de prediccion como columna
                    df["time"] = day_of_pred
                    df.set_index("time", inplace=True)
                    df.index = pd.to_datetime(df.index)

                    # Procesar la columna 'periodo'
                    if "periodo" in df.columns:
                        if df["periodo"].str.len().max() <= 2:
                            df["periodo"] = (
                                AemetPredictionHandler._parse_simple_hours_column(
                                    df["periodo"]
                                )
                            )
                        else:
                            df["periodo"] = (
                                AemetPredictionHandler._parse_time_columns_with_periods(
                                    df["periodo"]
                                )
                            )

                        # Combinar la columna 'periodo' con el índice
                        df.index = df.index + df["periodo"]
                        df.drop(columns=["periodo"], inplace=True)
                    elif "dato" in df.columns:
                        raise ValueError(
                            "Se ha encontrado la columna 'dato', pero no se ha encontrado la columna 'periodo'."
                        )

                    # Comprobar que el DataFrame no esta vacío
                    if df.empty:
                        continue

                    # Procesar los datos de viento
                    if key == "vientoAndRachaMax":
                        df = AemetPredictionHandler._process_wind_data(df)

                    # Registrar el DataFrame
                    dict_of_pred[key] = df

                except Exception as e:
                    print(f"Error procesando la clave '{key}': {e}")

            # Agregar lista de predicciones al diccionario resultante
            if dict_of_pred:
                results[day_of_pred] = dict_of_pred

        # Comprobar que el diccionario no esta vacío
        if not results:
            raise ValueError(
                f"No se encontraron datos procesados para la URL {full_url}."
            )

        return results


class AemetObservationHandler(AemetBaseHandler):
    """
    Clase para manejar las observaciones de la API de AEMET.
    """

    pass
