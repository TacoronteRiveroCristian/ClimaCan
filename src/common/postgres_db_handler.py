"""
Clase para manejar operaciones con PostgreSQL utilizando SQLAlchemy.
"""

from typing import Literal

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError


class PostgresDBHandler:
    """
    Clase para manejar operaciones con PostgreSQL utilizando SQLAlchemy.

    :param db: Nombre de la base de datos.
    :param user: Usuario de la base de datos.
    :param password: Contraseña de la base de datos.
    :param host: Host de la base de datos (por defecto localhost).
    :param port: Puerto de la base de datos (por defecto 5432).
    """

    def __init__(
        self,
        db: str,
        user: str,
        password: str,
        host: str = "localhost",
        port: int = 5432,
    ):
        self.db = db
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        self.engine = self._create_engine()

    def _create_engine(self):
        """Crea la conexión a la base de datos usando SQLAlchemy."""
        try:
            connection_str = f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"
            return create_engine(connection_str)
        except SQLAlchemyError as e:
            print(f"Error al conectar con la base de datos: {e}")
            return None

    def write_dataframe(
        self,
        df: pd.DataFrame,
        table_name: str,
        if_exists: Literal["fail", "replace", "append"],
    ):
        """
        Guarda un DataFrame en PostgreSQL.

        :param df: DataFrame de pandas a guardar.
        :param table_name: Nombre de la tabla en la base de datos.
        :param if_exists: Comportamiento si la tabla ya existe:
            - 'fail': Lanza un error si la tabla ya existe.
            - 'replace': Elimina la tabla existente y crea una nueva.
            - 'append': Añade los nuevos datos a la tabla sin modificar los existentes.
        """
        try:
            df.to_sql(table_name, self.engine, if_exists=if_exists, index=False)
            print(f"Datos insertados correctamente en la tabla '{table_name}'")
        except SQLAlchemyError as e:
            print(f"Error al escribir en la base de datos: {e}")

    def read_dataframe(
        self,
        query: str,
    ) -> pd.DataFrame:
        """
        Ejecuta una consulta SQL y devuelve los resultados en un DataFrame.

        :param query: Consulta SQL a ejecutar.
        :return: DataFrame con los resultados.
        """
        try:
            return pd.read_sql(query, self.engine)
        except SQLAlchemyError as e:
            print(f"Error al leer de la base de datos: {e}")
            return pd.DataFrame()
