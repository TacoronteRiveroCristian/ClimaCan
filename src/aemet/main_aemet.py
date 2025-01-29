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
from src.common.config import INFLUXDB_HOST, INFLUXDB_PORT, INFLUXDB_TIMEOUT
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
logger = logging_handler.add_handlers([stream])

# Instanciar manejador de tareas
task_manager = TaskManager(
    logger=logger,
    environment="/usr/local/bin/python3",
    client=client,
    database="aemet_tasks",
)


def run_canary_aemet_prediction():
    """
    Funcion principal que ejecuta la tarea AEMET para predicciones de Canarias.
    """
    task_manager.execute_task(
        task_name="Canary AEMET Prediction",
        script_path="src/aemet/files/get_canary_predictions.py",
        measurement="main_aemet",
        field="task_success_canary_aemet_prediction",
    )


def run_update_canary_municipalities():
    """
    Funcion principal que ejecuta la tarea para actualizar la lista de codigos
    de los municipios de Canarias y asi realizar posteriormente las predicciones.

    Posteriormente, se actualiza la base de datos que se encuentra en Grafana.
    """
    task_manager.execute_task(
        task_name="Update Canary Municipalities",
        script_path="src/aemet/files/get_canary_ids.py",
        measurement="main_aemet",
        field="task_success_update_canary_municipalities",
    )
    # Crear provisionamiento de bases de datos para Grafana
    generate_grafana_yaml(
        json_file_path=MUNICIPALITIES_JSON_PATH,
        output_file=DATABASE_PROVISIONING_YAML_PATH,
    )


if __name__ == "__main__":
    # Configurar el scheduler
    scheduler = BlockingScheduler()

    # Programar las tareas
    run_update_canary_municipalities()
    scheduler.add_job(
        run_update_canary_municipalities,
        CronTrigger.from_crontab("0 3 1 * *"),
        name="Monthly Update Canary Municipalities Task",
    )

    run_canary_aemet_prediction()
    scheduler.add_job(
        run_canary_aemet_prediction,
        CronTrigger.from_crontab("0 4 * * *"),
        name="Daily Canary AEMET Prediction Task",
    )

    try:
        print("Iniciando scheduler. Presiona Ctrl+C para detenerlo.")
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("Scheduler detenido.")
