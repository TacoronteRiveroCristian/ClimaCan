"""
Script principal que inicia la ejecucion de los procesos relacionados.
"""

import subprocess

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from ctrutils.handlers.ErrorHandlerBase import ErrorHandler
from ctrutils.handlers.LoggingHandlerBase import LoggingHandler

from conf import (
    GRACAN__CRONTAB_RUN_UPDATE_HISTORICAL_LOCATIONS,
    GRACAN__CRONTAB_RUN_WRITE_LAST_OBSERVATIONS,
    GRAFCAN__CSV_FILE_CLASSES_METADATA_STATIONS,
)
from src.common.functions import write_status_task

# Instanciar manejadores
handler = LoggingHandler()
LOGGER = handler.configure_logger()
ERROR_HANDLER = ErrorHandler()


def run_update_historical_locations():
    """
    Actualiza la lista de estaciones de Grafcan, ejecutando el script que la obtiene
    desde la API y la guarda en un archivo CSV.

    :return: None
    """
    task = "run_update_historical_locations"
    field = f"task_success_{task}"
    script = "src/grafcan/files/update_historical_locations.py"
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
    except subprocess.CalledProcessError as e:
        write_status_task(field, 0)
        error_message = f"Error al ejecutar el script '{script}': {e.stderr}"
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
    except subprocess.CalledProcessError as e:
        write_status_task(field, 0)
        error_message = f"Error al ejecutar el script '{script}': {e.stderr}"
        ERROR_HANDLER.handle_error(error_message, LOGGER)


def main() -> None:
    """
    Función principal del script que inicia la ejecucion de los procesos.

    :return: None
    """
    scheduler = BlockingScheduler()

    # Lanzar tarea inicial para actualizar la lista de estaciones
    if not GRAFCAN__CSV_FILE_CLASSES_METADATA_STATIONS.exists():
        LOGGER.info("Ejecutando tarea inicial para actualizar la lista de estaciones.")
        run_update_historical_locations()

    # Configurar tareas programadas
    scheduler.add_job(
        run_update_historical_locations,
        CronTrigger.from_crontab(GRACAN__CRONTAB_RUN_UPDATE_HISTORICAL_LOCATIONS),
    )
    scheduler.add_job(
        run_write_last_observations,
        CronTrigger.from_crontab(GRACAN__CRONTAB_RUN_WRITE_LAST_OBSERVATIONS),
    )

    LOGGER.info("Scheduler iniciado.")
    scheduler.start()


if __name__ == "__main__":
    main()
