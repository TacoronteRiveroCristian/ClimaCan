"""
Script principal que inicia la ejecucion de los procesos relacionados con Grafcan.
"""

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from ctrutils.database.influxdb.InfluxdbOperation import InfluxdbOperation
from ctrutils.handlers.LoggingHandlerBase import LoggingHandler

from src.common.config import INFLUXDB_HOST, INFLUXDB_PORT, INFLUXDB_TIMEOUT
from src.common.task_manager import TaskManager
from src.grafcan.config.config import CSV_FILE_CLASSES_METADATA_STATIONS

# Instanciar cliente de InfluxDB
client = InfluxdbOperation(
    host=INFLUXDB_HOST,
    port=INFLUXDB_PORT,
    timeout=INFLUXDB_TIMEOUT,
)

# Instanciar manejador de logs
logging_handler = LoggingHandler()
stream = logging_handler.create_stream_handler()
logger = logging_handler.add_handlers([stream])

# Instanciar manejador de tareas
task_manager = TaskManager(
    logger=logger,
    environment="/usr/local/bin/python3",
    client=client,
    database="grafcan_tasks",
)


def run_update_historical_locations():
    """
    Actualiza la lista de estaciones de Grafcan desde la API y guarda los resultados en un archivo CSV.
    """
    task_manager.execute_task(
        task_name="Update Historical Locations",
        script_path="src/grafcan/files/update_historical_locations.py",
        measurement="grafcan_locations",
        field="task_success_update_historical_locations",
    )


def run_write_last_observations():
    """
    Obtiene las observaciones más recientes de las estaciones de Grafcan y guarda los resultados en un archivo CSV.
    """
    task_manager.execute_task(
        task_name="Write Last Observations",
        script_path="src/grafcan/files/write_last_observations.py",
        measurement="grafcan_observations",
        field="task_success_write_last_observations",
    )


def main() -> None:
    """
    Función principal del script que inicia la ejecucion de los procesos.
    """
    scheduler = BlockingScheduler()

    # Ejecutar tarea inicial si el archivo de estaciones no existe
    if not CSV_FILE_CLASSES_METADATA_STATIONS.exists():
        logger.info(
            "Ejecutando tarea inicial para actualizar la lista de estaciones."
        )
        run_update_historical_locations()

    # Configurar tareas programadas
    scheduler.add_job(
        run_update_historical_locations,
        CronTrigger.from_crontab("0 23 * * 1,3,5"),
        name="Update Historical Locations",
    )

    run_write_last_observations()
    scheduler.add_job(
        run_write_last_observations,
        CronTrigger.from_crontab("*/10 * * * *"),
        name="Write Last Observations",
    )

    try:
        print("Iniciando scheduler. Presiona Ctrl+C para detenerlo.")
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("Scheduler detenido.")


if __name__ == "__main__":
    main()
