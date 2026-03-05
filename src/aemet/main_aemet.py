"""
Script principal que inicia la ejecucion de los procesos relacionados
con el servicio AEMET.
"""

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from ctrutils.database.influxdb.InfluxdbOperation import InfluxdbOperation
from ctrutils.handler.logging.logging_handler import LoggingHandler

from src.aemet.config.config import (
    DATABASE_PROVISIONING_YAML_PATH,
    MUNICIPALITIES_JSON_PATH,
)
from src.common.config import (
    INFLUXDB_HOST,
    INFLUXDB_PORT,
    INFLUXDB_TIMEOUT,
    TELEGRAM_CHAT_ID,
    TELEGRAM_TOKEN,
    wait_for_services,
)
from src.common.functions import generate_grafana_yaml
from src.common.task_manager import TaskManager

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
    database="aemet_tasks",
)


def run_canary_aemet_prediction() -> None:
    """
    Funcion principal que ejecuta la tarea AEMET para predicciones de Canarias.
    """
    try:
        task_manager.execute_task(
            task_name="Canary AEMET Prediction",
            script_path="src/aemet/files/get_canary_predictions.py",
            measurement="main_aemet",
            field="task_success_canary_aemet_prediction",
        )
    except Exception as e:
        logger.error(
            f"Error crítico en run_canary_aemet_prediction: {e}", exc_info=True
        )


def run_update_canary_municipalities() -> None:
    """
    Funcion principal que ejecuta la tarea para actualizar la lista de codigos
    de los municipios de Canarias y asi realizar posteriormente las predicciones.

    Posteriormente, se actualiza la base de datos que se encuentra en Grafana.
    """
    try:
        task_manager.execute_task(
            task_name="Update Canary Municipalities",
            script_path="src/aemet/files/get_canary_metadata.py",
            measurement="main_aemet",
            field="task_success_update_canary_municipalities",
        )
        # Crear provisionamiento de bases de datos para Grafana
        generate_grafana_yaml(
            json_file_path=MUNICIPALITIES_JSON_PATH,
            output_file=DATABASE_PROVISIONING_YAML_PATH,
        )
    except Exception as e:
        logger.error(
            f"Error crítico en run_update_canary_municipalities: {e}",
            exc_info=True,
        )


def run_get_conventional_observations() -> None:
    """
    Funcion principal que ejecuta la tarea para obtener las observaciones
    convencionales de Canarias.
    """
    try:
        task_manager.execute_task(
            task_name="Get Conventional Observations",
            script_path="src/aemet/files/get_conventional_observations.py",
            measurement="main_aemet",
            field="task_success_get_conventional_observations",
        )
    except Exception as e:
        logger.error(
            f"Error crítico en run_get_conventional_observations: {e}",
            exc_info=True,
        )


if __name__ == "__main__":
    # Configurar el scheduler con mayor resiliencia
    scheduler = BlockingScheduler(
        job_defaults={
            "coalesce": True,  # Combinar trabajos atrasados
            "max_instances": 1,  # Solo una instancia por trabajo
            "misfire_grace_time": 3600,  # 1 hora de tolerancia
        }
    )

    # Esperar a que los servicios de base de datos esten disponibles
    if not wait_for_services():
        logger.critical(
            "No se pudo conectar a los servicios requeridos. "
            "El scheduler AEMET no se iniciara."
        )
        exit(0)  # Salida limpia para no activar reintentos en run.sh

    # Ejecutar tareas iniciales de forma segura
    logger.info("Ejecutando tareas iniciales...")
    try:
        run_update_canary_municipalities()
    except Exception as e:
        logger.error(
            f"Error en ejecución inicial de municipios: {e}", exc_info=True
        )

    try:
        run_canary_aemet_prediction()
    except Exception as e:
        logger.error(
            f"Error en ejecución inicial de predicciones: {e}", exc_info=True
        )

    try:
        run_get_conventional_observations()
    except Exception as e:
        logger.error(
            f"Error en ejecución inicial de observaciones: {e}", exc_info=True
        )

    # Programar las tareas
    scheduler.add_job(
        run_update_canary_municipalities,
        CronTrigger.from_crontab("0 0 1,8,15,21 * 1"),
        name="Every Week of the Month Update Canary Municipalities Task",
        misfire_grace_time=3600,
    )

    scheduler.add_job(
        run_canary_aemet_prediction,
        CronTrigger.from_crontab("0 */6 * * *"),
        name="Every 6 hours Canary AEMET Prediction Task",
        misfire_grace_time=3600,
    )

    scheduler.add_job(
        run_get_conventional_observations,
        CronTrigger.from_crontab("2 * * * *"),
        name="Daily Get Conventional Observations Task",
        misfire_grace_time=3600,
    )

    try:
        logger.info(
            "Scheduler AEMET iniciado correctamente. Presiona Ctrl+C para detenerlo."
        )
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler AEMET detenido por el usuario.")
    except Exception as e:
        logger.critical(
            f"Error crítico en el scheduler AEMET: {e}", exc_info=True
        )
