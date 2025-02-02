"""
Módulo para gestionar las consultas de predicciones provenientes de la API de AEMET.

Este módulo proporciona clases para:
  - Realizar la consulta a la API de AEMET y obtener los datos y metadatos.
  - Parsear y formatear cadenas de texto que representan periodos de tiempo en objetos timedelta.
  - Reestructurar y formatear los datos de viento, combinando filas, extrayendo información y
    agregando una columna que mapea la dirección en texto a grados.
  - Procesar la información de predicción de AEMET, convirtiendo cada lista de mediciones en DataFrames
    con el índice adecuado (calculado a partir de la fecha base y el periodo).

Clases principales:
  - AemetBaseHandler:
      Clase base para gestionar las consultas a la API de AEMET. Se encarga de establecer la conexión,
      realizar la solicitud HTTP y procesar la respuesta JSON.

  - PeriodFormatter:
      Clase para parsear y formatear cadenas que representan un "periodo" en un objeto timedelta.
      Interpreta cadenas cortas (<=2 caracteres) como horas y cadenas de 4 caracteres como horas y minutos.
      Si la cadena no cumple el formato esperado, lanza un ValueError.

  - WindDataFormatter:
      Clase para reestructurar los datos de viento. A partir de un DataFrame con columnas como "direccion",
      "velocidad" y "value", agrupa las filas por timestamp, extrae el primer elemento de listas y agrega
      la columna "direccion_degrees" usando un diccionario de mapeo (las claves se transforman a minúsculas).
      Además, renombra "value" a "velocidad_max" y fuerza la conversión a tipo numérico.

  - AemetPredictionHandler:
      Clase que hereda de AemetBaseHandler y utiliza la nueva lógica de formateo. Para cada día de
      predicción:
        - Obtiene la fecha base.
        - Convierte cada lista de mediciones en un DataFrame.
        - Transforma la columna "periodo" en un timedelta mediante PeriodFormatter.parse y suma este
          valor a la fecha base para obtener un índice datetime.
        - Aplica el formateo especial para viento (vientoAndRachaMax) si corresponde.
        - Fuerza la conversión de la columna "value" a tipo float.
      Los DataFrames resultantes se almacenan en un diccionario indexado por la fecha base.

Uso:
  Para utilizar este módulo, se debe instanciar AemetPredictionHandler con el token de autenticación
  de la API de AEMET y luego llamar al método process_municipality_data proporcionando la URL completa.

  Ejemplo:
      handler = AemetPredictionHandler(token="TU_TOKEN")
      results = handler.process_municipality_data("URL_DE_LA_API")
      # 'results' contendrá un diccionario con DataFrames procesados por fecha y variable.

Notas sobre warnings:
  Se recomienda utilizar el módulo estándar "warnings" para notificar al usuario sobre advertencias en
  vez de emplear "print". Por ejemplo:

      import warnings
      warnings.warn("Se ha detectado un valor inesperado.", UserWarning)

  De forma predeterminada, los warnings generados por warnings.warn se muestran en la terminal (por lo general,
  se imprimen en stderr) a menos que la configuración de warnings se haya modificado para filtrarlos o suprimirlos.

"""

import warnings
from datetime import timedelta
from typing import Any, Dict, List

import pandas as pd
import requests


class AemetBaseHandler:
    """
    Clase base para manejar las consultas a la API de AEMET.

    Esta clase se encarga de inicializar la conexión a la API utilizando el token de autenticación,
    realizar las solicitudes HTTP y procesar la respuesta JSON para extraer tanto los datos como los
    metadatos.

    Args:
        token (str): Token de autorización para la API de AEMET.
        timeout (int, optional): Tiempo máximo de espera de respuesta (en segundos). Por defecto es 20.
    """

    def __init__(self, token: str, timeout: int = 20) -> None:
        self.token = token
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self.timeout = timeout

    def fetch_data(self, full_url: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Ejecuta una consulta a la API de AEMET y retorna los datos y metadatos en un único diccionario.

        Args:
            full_url (str): URL completa de la API a consultar.

        Returns:
            Dict[str, List[Dict[str, Any]]]: Diccionario que contiene las claves "data" y "metadata" con
            la información retornada por la API.

        Raises:
            ValueError: Si la consulta no retorna una respuesta válida o se produce un error en la solicitud.
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


class PeriodFormatter:
    """
    Clase para parsear y formatear cadenas que representan un 'periodo' en un objeto timedelta.

    Esta clase proporciona un método estático que transforma una cadena de texto en un timedelta,
    interpretando dos formatos principales:

      - Si la longitud de la cadena es 2 o menor, se asume que representa la hora en formato de 24 horas
        (por ejemplo, "06" se convierte en 6 horas).
      - Si la longitud de la cadena es 4, se asume que la cadena contiene la hora y los minutos en formato
        de 24 horas (por ejemplo, "1800" se convierte en 18 horas y 0 minutos).

    Si la cadena no cumple con ninguno de estos formatos, se lanza un ValueError indicando que el formato
    no es el esperado.

    Métodos:
        parse(period: str) -> timedelta
            Convierte una cadena de periodo en un objeto timedelta según las reglas descritas.
    """

    @staticmethod
    def parse(period: str) -> timedelta:
        """
        Parsea y formatea el 'periodo' en un objeto timedelta.

        Args:
            period (str): Cadena que representa el periodo. Puede ser de dos formas:
                          - Un string corto (<= 2 caracteres) que representa la hora.
                          - Un string de 4 caracteres que representa la hora y los minutos (HHMM).

        Returns:
            timedelta: Objeto timedelta que representa el periodo indicado.

        Raises:
            ValueError: Si el string no tiene un formato esperado.
        """
        if len(period) <= 2:
            # Se asume que representa la hora en formato "06", "07", etc.
            return timedelta(hours=float(period))
        elif len(period) == 4:
            # Se asumen que presentan la hora y minutos en formato "1800", "0612", etc.
            return timedelta(hours=float(period[:2]), minutes=float(period[2:]))
        else:
            raise ValueError(
                f"El valor '{period}' no tiene un formato esperado."
            )


class WindDataFormatter:
    """
    Clase para formatear datos de viento.

    Esta clase procesa un DataFrame que contiene la información de viento, esperando encontrar
    las columnas "direccion", "velocidad" y "value" (que se renombrará a "velocidad_max"). Se agrupa
    la información por timestamp, extrayendo el primer elemento de las listas presentes en "direccion"
    y "velocidad". Además, se agrega la columna "direccion_degrees", que asigna un valor en grados a
    partir de la dirección textual utilizando un diccionario de mapeo (las claves se transforman a minúsculas).

    Atributos:
        direction_mapping (dict): Diccionario para convertir las direcciones a grados, con todas las claves
                                  en minúsculas.
    """

    # Diccionario para convertir las direcciones a grados (todo en minúsculas)
    direction_mapping = {
        "n": 0,
        "ne": 45,
        "e": 90,
        "se": 135,
        "s": 180,
        "sw": 225,
        "w": 270,
        "nw": 315,
        "calma": -1,
    }

    @staticmethod
    def format_wind_df(df: pd.DataFrame) -> pd.DataFrame:
        """
        Recibe un DataFrame con la información de viento y lo reestructura para obtener
        una sola fila por timestamp, extrayendo y formateando las columnas "direccion",
        "velocidad" y "value" (renombrada a "velocidad_max"), y añadiendo la columna
        "direccion_degrees".

        Se asume que para cada timestamp existen dos filas:
          - Una fila con la información de "direccion" y "velocidad" (en formato de lista).
          - Otra fila con el valor de "value", que se renombrará a "velocidad_max".

        Returns:
            pd.DataFrame: DataFrame formateado con las columnas "direccion", "velocidad", "velocidad_max"
            y "direccion_degrees".
        """
        # Agrupar por el índice datetime.
        df_grouped = df.groupby(level=0).agg(
            {
                "direccion": lambda x: (
                    x.dropna().iloc[0] if not x.dropna().empty else None
                ),
                "velocidad": lambda x: (
                    x.dropna().iloc[0] if not x.dropna().empty else None
                ),
                "value": lambda x: (
                    x.dropna().iloc[0] if not x.dropna().empty else None
                ),
            }
        )

        # Renombrar "value" a "velocidad_max"
        df_grouped.rename(columns={"value": "velocidad_max"}, inplace=True)

        # Extraer el primer elemento de la lista en "direccion" y "velocidad"
        df_grouped["direccion"] = df_grouped["direccion"].apply(
            lambda x: x[0] if isinstance(x, list) and len(x) > 0 else x
        )
        df_grouped["velocidad"] = df_grouped["velocidad"].apply(
            lambda x: x[0] if isinstance(x, list) and len(x) > 0 else x
        )

        # Convertir "velocidad" y "velocidad_max" a numérico (float)
        df_grouped["velocidad"] = pd.to_numeric(
            df_grouped["velocidad"], errors="coerce"
        )
        df_grouped["velocidad_max"] = pd.to_numeric(
            df_grouped["velocidad_max"], errors="coerce"
        )

        # Crear la nueva columna "direccion_degrees" usando el diccionario de mapeo
        df_grouped["direccion_degrees"] = df_grouped["direccion"].apply(
            lambda d: (
                WindDataFormatter.direction_mapping.get(d.lower(), None)
                if isinstance(d, str)
                else None
            )
        )

        return df_grouped


class AemetPredictionHandler(AemetBaseHandler):
    """
    Clase para manejar las predicciones de la API de AEMET utilizando la nueva lógica de formateo.

    Esta clase hereda de AemetBaseHandler e implementa el método process_municipality_data, el cual:
      - Obtiene la fecha base para cada día de predicción.
      - Convierte cada lista de mediciones en un DataFrame.
      - Transforma la columna "periodo" a un objeto timedelta mediante PeriodFormatter.parse.
      - Suma el timedelta a la fecha base para obtener la columna "datetime".
      - Establece "datetime" como índice y elimina la columna "periodo".
      - Aplica el formateo especial para viento (si la medición es "vientoAndRachaMax").
      - Fuerza la conversión de la columna "value" a tipo float, en caso de existir.

    Los DataFrames resultantes se agrupan en un diccionario indexado por la fecha base.

    Args:
        full_url (str): URL completa con endpoint y parámetros para consultar la API.
    """

    def process_municipality_data(self, full_url: str) -> dict:
        """
        Procesa los datos de predicción para una URL completa utilizando la nueva lógica.

        Para cada día de predicción se:
          - Obtiene la fecha base.
          - Convierte cada lista de mediciones en un DataFrame.
          - Transforma la columna "periodo" a timedelta mediante PeriodFormatter.parse.
          - Suma el timedelta a la fecha base para obtener la columna "datetime".
          - Establece "datetime" como índice y elimina la columna "periodo".
          - Aplica el formateo especial para viento (vientoAndRachaMax) si es necesario.
          - Fuerza la columna "value" a tipo float (si existe).

        Args:
            full_url (str): URL completa con endpoint y parámetros.

        Returns:
            dict: Diccionario de DataFrames procesados, indexado por la fecha base y la variable correspondiente.

        Raises:
            ValueError: Si no se pueden obtener datos válidos o si no se encuentran datos procesados.
        """
        response = self.fetch_data(full_url)
        if response["data"] == [{}]:
            raise ValueError(
                f"No se pudieron obtener datos para la URL {full_url}."
            )

        pred = response["data"][0].get("prediccion", {}).get("dia", [])
        results = {}

        for day in pred:
            # Obtener la fecha base de los datos
            date = day.get("fecha")
            dict_of_pred = {}
            for key, value in day.items():
                # Saltar las claves de tipo str (por ejemplo, 'fecha', 'orto', 'ocaso')
                # o aquellas que no sean listas o estén vacías.
                if (
                    isinstance(value, str)
                    or not isinstance(value, list)
                    or not value
                ):
                    warnings.warn(
                        f"Saltando la clave '{key}' con valor '{value}' por no ser una lista de datos de predicciones.",
                        UserWarning,
                    )
                    continue

                # Convertir la lista de mediciones en un DataFrame
                df = pd.DataFrame(value)
                # Convertir la columna "periodo" a timedelta
                df["periodo"] = df["periodo"].apply(PeriodFormatter.parse)
                # Crear la columna "datetime" sumando la fecha base y el periodo
                df["datetime"] = pd.to_datetime(date) + df["periodo"]
                # Establecer "datetime" como índice y eliminar la columna "periodo"
                df.set_index("datetime", inplace=True, drop=True)
                df.drop(columns=["periodo"], inplace=True)

                # Si la medición es de viento, aplicar el formateo específico
                if key == "vientoAndRachaMax":
                    df = WindDataFormatter.format_wind_df(df)

                dict_of_pred[key] = df

            if dict_of_pred:
                results[date] = dict_of_pred

        if not results:
            raise ValueError(
                f"No se encontraron datos procesados para la URL {full_url}."
            )

        return results
