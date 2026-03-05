"""
Fichero de configuracion globale para el proyecto ClimaCan.
"""

import os
import socket
import time
from pathlib import Path

from src.common.postgres_db_handler import PostgresDBHandler

# Directorio de trabajo
WORKDIR = Path(os.getenv("WORKDIR"))

# Token y chatID para alertas de telegram si se requiere
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Parametros InfluxDB
INFLUXDB_HOST = "climacan-influxdb"
INFLUXDB_PORT = os.getenv("INFLUXDB_PORT")
INFLUXDB_TIMEOUT = 5

# Parametros PostgreSQL
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")

# Configuracion de espera de servicios
SERVICE_WAIT_MAX_RETRIES = 10
SERVICE_WAIT_INITIAL_DELAY = 2


def _wait_for_service(host: str, port: int, service_name: str) -> bool:
    """
    Espera a que un servicio este disponible en host:port.
    Usa backoff exponencial con un maximo de SERVICE_WAIT_MAX_RETRIES intentos.

    :param host: Host del servicio.
    :param port: Puerto del servicio.
    :param service_name: Nombre del servicio (para logs).
    :return: True si el servicio esta disponible, False si se agotaron los reintentos.
    """
    delay = SERVICE_WAIT_INITIAL_DELAY
    for attempt in range(1, SERVICE_WAIT_MAX_RETRIES + 1):
        try:
            with socket.create_connection((host, port), timeout=5):
                print(f"[OK] {service_name} disponible en {host}:{port}")
                return True
        except (ConnectionRefusedError, socket.timeout, OSError):
            print(
                f"[Intento {attempt}/{SERVICE_WAIT_MAX_RETRIES}] "
                f"Esperando a {service_name} en {host}:{port}... "
                f"Reintentando en {delay}s"
            )
            time.sleep(delay)
            delay = min(delay * 2, 60)  # Backoff exponencial, tope 60s

    print(
        f"[ERROR] {service_name} no disponible tras "
        f"{SERVICE_WAIT_MAX_RETRIES} intentos."
    )
    return False


def wait_for_services() -> bool:
    """
    Espera a que InfluxDB y PostgreSQL esten disponibles.

    :return: True si ambos servicios estan disponibles.
    """
    influxdb_ok = _wait_for_service(
        INFLUXDB_HOST, int(INFLUXDB_PORT), "InfluxDB"
    )
    postgres_ok = _wait_for_service(
        "climacan-postgres", int(POSTGRES_PORT), "PostgreSQL"
    )
    return influxdb_ok and postgres_ok


def get_postgres_client() -> PostgresDBHandler:
    """
    Crea y devuelve una instancia de PostgresDBHandler.
    Inicializacion lazy para evitar fallos al importar si PostgreSQL no esta listo.

    :return: Instancia de PostgresDBHandler.
    """
    return PostgresDBHandler(
        db=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        host="climacan-postgres",
        port=POSTGRES_PORT,
    )


# Singleton lazy: se instancia al primer acceso, no al importar el modulo
_postgres_client = None


def _get_postgres_client_singleton() -> PostgresDBHandler:
    """Devuelve un singleton de PostgresDBHandler con inicializacion lazy."""
    global _postgres_client
    if _postgres_client is None:
        _postgres_client = get_postgres_client()
    return _postgres_client


class _PostgresClientProxy:
    """Proxy que retrasa la instanciacion de PostgresDBHandler hasta su primer uso."""

    def __getattr__(self, name):
        return getattr(_get_postgres_client_singleton(), name)


# Exponer como postgres_client para mantener compatibilidad con imports existentes
postgres_client = _PostgresClientProxy()
