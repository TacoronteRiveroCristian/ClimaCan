"""
Script para obtener y guardar los metadatos de las estaciones de Grafcan
en un archivo CSV.
"""

from src.grafcan.classes.StationMetadataFetcher import StationMetadataFetcher

if __name__ == "__main__":
    fetcher = StationMetadataFetcher()
    fetcher.run()
