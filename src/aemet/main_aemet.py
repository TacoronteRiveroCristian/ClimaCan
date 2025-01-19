from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from ctrutils.database.influxdb.InfluxdbOperation import InfluxdbOperation
from ctrutils.handlers.LoggingHandlerBase import LoggingHandler

from conf import INFLUXDB_HOST, INFLUXDB_PORT, INFLUXDB_TIMEOUT
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
    environment="/usr/bin/python3",
    client=client,
    database="aemet_tasks",
)


def main_task():
    """
    Función principal que ejecuta la tarea AEMET para predicciones de Canarias.
    """
    task_manager.execute_task(
        task_name="Canary AEMET Prediction",
        script_path="src/aemet/files/get_canary_predictions.py",
        measurement="main_aemet",
        field="task_success_canary_aemet_prediction",
    )


if __name__ == "__main__":
    # Configurar el scheduler
    scheduler = BlockingScheduler()

    # Programar las tareas
    scheduler.add_job(
        main_task,
        CronTrigger(hour=4, minute=0),
        name="Daily Canary AEMET Prediction Task",
    )

    try:
        print("Iniciando scheduler. Presiona Ctrl+C para detenerlo.")
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("Scheduler detenido.")
