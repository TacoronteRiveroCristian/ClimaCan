"""
Script principal que inicia la ejecucion de los procesos relacionados con Grafcan.
"""

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from ctrutils.database.influxdb.InfluxdbOperation import InfluxdbOperation
from ctrutils.handler.logging.logging_handler import LoggingHandler

from src.common.config import (
    INFLUXDB_HOST,
    INFLUXDB_PORT,
    INFLUXDB_TIMEOUT,
    TELEGRAM_CHAT_ID,
    TELEGRAM_TOKEN,
    wait_for_services,
)
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
telegram = logging_handler.create_telegram_handler(
    token=TELEGRAM_TOKEN,
    chat_id=TELEGRAM_CHAT_ID,
)
logger = logging_handler.add_handlers([stream, telegram])

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
    try:
        task_manager.execute_task(
            task_name="Update Historical Locations",
            script_path="src/grafcan/files/update_historical_locations.py",
            measurement="grafcan_locations",
            field="task_success_update_historical_locations",
        )
    except Exception as e:
        logger.error(
            f"Error crítico en run_update_historical_locations: {e}",
            exc_info=True,
        )


def run_write_last_observations():
    """
    Obtiene las observaciones más recientes de las estaciones de Grafcan y guarda los resultados en un archivo CSV.
    """
    try:
        task_manager.execute_task(
            task_name="Write Last Observations",
            script_path="src/grafcan/files/write_last_observations.py",
            measurement="grafcan_observations",
            field="task_success_write_last_observations",
        )
    except Exception as e:
        logger.error(
            f"Error crítico en run_write_last_observations: {e}", exc_info=True
        )


def main() -> None:
    """
    Función principal del script que inicia la ejecucion de los procesos.
    """
    # Esperar a que los servicios de base de datos esten disponibles
    if not wait_for_services():
        logger.critical(
            "No se pudo conectar a los servicios requeridos. "
            "El scheduler Grafcan no se iniciara."
        )
        return

    scheduler = BlockingScheduler(
        job_defaults={
            "coalesce": True,  # Combinar trabajos atrasados
            "max_instances": 1,  # Solo una instancia por trabajo
            "misfire_grace_time": 600,  # 10 minutos de tolerancia
        }
    )

    # Ejecutar tarea inicial si el archivo de estaciones no existe
    if not CSV_FILE_CLASSES_METADATA_STATIONS.exists():
        logger.info(
            "Ejecutando tarea inicial para actualizar la lista de estaciones."
        )
        try:
            run_update_historical_locations()
        except Exception as e:
            logger.error(
                f"Error en ejecución inicial de localizaciones: {e}",
                exc_info=True,
            )

    # Configurar tareas programadas
    scheduler.add_job(
        run_update_historical_locations,
        CronTrigger.from_crontab("0 23 * * 1,3,5"),
        name="Update Historical Locations",
        misfire_grace_time=3600,
    )

    try:
        run_write_last_observations()
    except Exception as e:
        logger.error(
            f"Error en ejecución inicial de observaciones: {e}", exc_info=True
        )

    scheduler.add_job(
        run_write_last_observations,
        CronTrigger.from_crontab("*/10 * * * *"),
        name="Write Last Observations",
        misfire_grace_time=600,
    )

    try:
        logger.info(
            "Scheduler Grafcan iniciado correctamente. Presiona Ctrl+C para detenerlo."
        )
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler Grafcan detenido por el usuario.")
    except Exception as e:
        logger.critical(
            f"Error crítico en el scheduler Grafcan: {e}", exc_info=True
        )


if __name__ == "__main__":
    main()
