"""
Script que se encarga de obtener los metadatos de las estaciones de Grafcan
y guardarlos en un archivo CSV.
"""

from ctrutils.handlers.LoggingHandlerBase import LoggingHandler

from src.grafcan.classes.station_metadata_fetcher import StationMetadataFetcher
from src.grafcan.config.config import CSV_FILE_CLASSES_METADATA_STATIONS, TOKEN

# Configurar logger
logging_handler = LoggingHandler()
stream = logging_handler.create_stream_handler()
logger = logging_handler.add_handlers([stream])

if __name__ == "__main__":
    fetcher = StationMetadataFetcher(token=TOKEN)

    try:
        logger.info("Iniciando el proceso de obtención de datos históricos.")
        df = fetcher.process_historical_locations()
        fetcher.save_csv(df, CSV_FILE_CLASSES_METADATA_STATIONS)
        logger.info("Datos históricos procesados y guardados exitosamente.")
    except Exception as e:
        logger.error(f"Error durante el proceso: {e}")
