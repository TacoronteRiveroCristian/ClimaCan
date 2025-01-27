"""
Clases para manejar las consultas de predicciones provenientes de la API de AEMET.
"""

from typing import Dict

import pandas as pd
import requests


class AemetBaseHandler:
    """
    Clase base para manejar las consultas a la API de AEMET.
    """

    def __init__(self, token: str) -> None:
        """
        Clase base para manejar las consultas a la API de AEMET.

        :param token: str - Token de autorización para la API de AEMET.
        """
        self.token = token
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self.timeout = 20

    def run_query(self, full_url: str) -> Dict:
        """
        Ejecuta una consulta a la API para una URL completa.

        :param full_url: str - URL completa de la API a consultar.
        :return: Dict con los datos obtenidos o None si hubo un error.
        """
        response = requests.get(
            full_url, headers=self.headers, timeout=self.timeout
        )
        response.raise_for_status()

        data = response.json()
        data_url = data.get("datos")

        if data_url:
            data_response = requests.get(data_url, timeout=self.timeout)
            data_response.raise_for_status()
            return data_response.json()
        else:
            raise ValueError("No se encontraron datos para la consulta.")


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
            f"El valor '{value}' no tiene una longitud válida de 4 caracteres."
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
        Procesa los datos de predicción para una URL completa específica.

        :param full_url: str - URL completa con endpoint y parámetros.
        :return: Diccionario con DataFrames de los datos procesados por medida.
        """
        data = self.run_query(full_url)
        if not data:
            raise ValueError(
                f"No se pudieron obtener datos para la URL {full_url}."
            )

        pred = data[0].get("prediccion", {}).get("dia", [])
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

                    # Agregar la fecha de predicción como columna
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

                    # Comprobar que el DataFrame no está vacío
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

        # Comprobar que el diccionario no está vacío
        if not results:
            raise ValueError(
                f"No se encontraron datos procesados para la URL {full_url}."
            )

        return results
