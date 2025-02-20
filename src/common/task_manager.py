"""
"""

import subprocess
from logging import Logger
from pathlib import Path
from typing import Union

from ctrutils.database.influxdb.InfluxdbOperation import InfluxdbOperation


class TaskManager:
    """
    Clase para gestionar la ejecución de tareas, registrar su estado en InfluxDB y manejar errores.

    :param logger: Logger para registrar los eventos.
    :type logger: logging.Logger
    :param environment: Diccionario con las variables de entorno necesarias para las tareas.
    :type environment: dict
    :param database: Nombre de la base de datos donde se registrará el estado.
    :type database: str
    """

    def __init__(
        self,
        logger: Logger,
        environment: str,
        client: InfluxdbOperation,
        database: str,
    ):
        self.logger = logger
        self.environment = environment
        self.client = client
        self.database = database

    def execute_task(
        self,
        task_name: str,
        script_path: Union[Path, str],
        measurement: str,
        field: str,
    ) -> None:
        """
        Ejecuta una tarea, registra su estado y maneja errores.

        :param task_name: Nombre de la tarea.
        :type task_name: str
        :param script_path: Ruta al script que se ejecutará.
        :type script_path: Union[Path, str]
        :param measurement: Nombre de la medición donde se registrará el estado.
        :type measurement: str
        :param field: Campo en la base de datos donde se registrará el estado.
        :type field: str
        """
        self.logger.info(f"Iniciando tarea: '{task_name}'.")

        try:
            result = self._run_script(script_path)
            self._record_status(field, measurement, 1 if result else 0)
            if result:
                self.logger.info(
                    f"Tarea '{task_name}' completada exitosamente."
                )
            else:
                self.logger.error(f"Tarea '{task_name}' fallida.")
        except Exception as e:
            self.logger.error(f"Error al ejecutar la tarea '{task_name}': {e}")
            self._record_status(field, measurement, 0)

    def _run_script(self, script_path: Union[Path, str]) -> bool:
        """
        Ejecuta un script usando subprocess.

        :param script_path: Ruta al script.
        :type script_path: Union[Path, str]
        :return: Verdadero si el script se ejecutó correctamente, falso en caso contrario.
        :rtype: bool
        """
        if isinstance(script_path, Path):
            script_path = str(script_path)

        try:
            subprocess.run(
                [self.environment, script_path],
                check=True,
                capture_output=True,
                text=True,
            )
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Error en el script '{script_path}': {e.stderr}")
            return False

    def _record_status(self, field: str, measurement: str, value: int) -> None:
        """
        Registra el estado de una tarea en InfluxDB.

        :param field: Campo a registrar.
        :type field: str
        :param value: Valor del estado (1 para éxito, 0 para fallo).
        :type value: int
        """
        point = {
            "measurement": measurement,
            "fields": {field: value},
        }
        try:
            self.client.write_points(points=[point], database=self.database)
        except Exception as e:
            raise RuntimeError(
                f"Error al registrar el estado en InfluxDB: {e}"
            ) from e
