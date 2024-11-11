"""
Script principal que inicia la ejecucion de los procesos relacionados.
"""

import subprocess

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from ctrutils.handlers.ErrorHandlerBase import ErrorHandler
from ctrutils.handlers.LoggingHandlerBase import LoggingHandler

from conf import (
    GRACAN__CRONTAB_RUN_UPDATE_LIST_OF_STATIONS,
    GRACAN__CRONTAB_RUN_WRITE_LAST_OBSERVATIONS,
)
from conf import GRAFCAN__LOG_FILE_SCRIPT_MAIN_GRAFCAN as LOG_FILE
from src.common.functions import write_status_task

# Instanciar manejadores
LOGGER = LoggingHandler(log_file=LOG_FILE).get_logger
ERROR_HANDLER = ErrorHandler()


def run_update_list_of_stations():
    """
    Actualiza la lista de estaciones de Grafcan, ejecutando el script que la obtiene
    desde la API y la guarda en un archivo CSV.

    :return: None
    """
    task = "run_update_list_of_stations"
    field = f"task_success_{task}"
    script = "src/grafcan/files/update_list_of_stations.py"
    LOGGER.info(f"Iniciando tarea: '{task}'")
    try:
        subprocess.run(
            ["/bin/python3", script],
            check=True,
            capture_output=True,
            text=True,
        )
        LOGGER.info(f"Tarea '{task}' completada exitosamente.")
        write_status_task(field, 1)
    except Exception as e:
        write_status_task(field, 0)
        error_message = f"Error al ejecutar el script '{script}': {e}"
        ERROR_HANDLER.handle_error(error_message, LOGGER)


def run_write_last_observations():
    """
    Obtiene los datos más recientes de las estaciones de Grafcan y los guarda en un archivo CSV.

    :return: None
    """
    task = "run_write_last_observations"
    field = f"task_success_{task}"
    script = "src/grafcan/files/write_last_observations.py"
    LOGGER.info(f"Iniciando tarea: '{task}'")
    try:
        subprocess.run(
            ["/bin/python3", script],
            check=True,
            capture_output=True,
            text=True,
        )
        LOGGER.info(f"Tarea '{task}' completada exitosamente.")
        write_status_task(field, 1)
    except Exception as e:
        write_status_task(field, 0)
        error_message = f"Error al ejecutar el script '{script}': {e}"
        ERROR_HANDLER.handle_error(error_message, LOGGER)


def main() -> None:
    """
    Función principal del script que inicia la ejecucion de los procesos.

    :return: None
    """
    scheduler = BlockingScheduler()

    # Lanzar tarea inicial para actualizar la lista de estaciones
    LOGGER.info("Ejecutando tarea inicial para actualizar la lista de estaciones.")
    run_update_list_of_stations()

    # Configurar tareas programadas
    scheduler.add_job(
        run_update_list_of_stations,
        CronTrigger.from_crontab(GRACAN__CRONTAB_RUN_UPDATE_LIST_OF_STATIONS),
    )
    scheduler.add_job(
        run_write_last_observations,
        CronTrigger.from_crontab(GRACAN__CRONTAB_RUN_WRITE_LAST_OBSERVATIONS),
    )

    LOGGER.info("Scheduler iniciado.")
    scheduler.start()


if __name__ == "__main__":
    main()
