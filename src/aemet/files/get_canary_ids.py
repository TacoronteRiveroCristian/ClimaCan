"""
Script para obtener el codigo de cada municipio canario de la API de AEMET
y guardarlo en un archivo JSON.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Union

import pandas as pd
import requests

from src.aemet.config.config import (
    MUNICIPALITIES_EXCEL_PATH,
    MUNICIPALITIES_JSON_PATH,
)
from src.common.functions import normalize_text


def download_municipalities_excel(save_path: Union[str, Path]) -> None:
    """
    Descarga el archivo Excel de municipios desde la URL del INE. Si no se encuentra el archivo del año actual,
    intenta descargar el del año anterior.

    :param save_path: str o Path - Ruta donde se guardará el archivo descargado.
    """
    if isinstance(save_path, str):
        save_path = Path(save_path)
    if not isinstance(save_path, Path):
        raise TypeError(
            f"save_path debe ser una cadena o un objeto Path. Recibido: {type(save_path)}"
        )

    save_path.parent.mkdir(parents=True, exist_ok=True)

    current_year = datetime.now().strftime("%y")
    previous_year = str(int(current_year) - 1).zfill(2)

    urls = [
        f"https://www.ine.es/daco/daco42/codmun/diccionario{current_year}.xlsx",
        f"https://www.ine.es/daco/daco42/codmun/diccionario{previous_year}.xlsx",
    ]

    for url in urls:
        try:
            response = requests.get(url, stream=True, timeout=20)
            response.raise_for_status()

            with open(save_path, "wb") as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)

            print(f"Archivo descargado y guardado en: {save_path} desde {url}")
            return
        except requests.exceptions.RequestException as e:
            print(f"No se pudo descargar el archivo desde {url}: {e}")

    raise FileNotFoundError(
        "No se pudo descargar el archivo para el año actual ni el anterior."
    )


def generate_municipalities_json(input_file: Path, output_file: Path):
    """
    Genera un archivo JSON con los datos procesados de municipios a partir de un archivo Excel.

    :param input_file: Ruta del archivo Excel de entrada.
    :param output_file: Ruta del archivo JSON de salida.
    """

    def normalize_municipalities(name: str) -> str:
        name = normalize_text(name)
        return name.split(",")[0].replace(" ", "_")

    def read_municipalities_excel(file_path: Path) -> pd.DataFrame:
        return pd.read_excel(io=file_path, header=1, dtype=str)

    def filter_canary_municipalities(df: pd.DataFrame) -> pd.DataFrame:
        mask = df["CPRO"].isin(["38", "35"])
        return df[mask].copy()

    def process_municipalities_data(df: pd.DataFrame) -> pd.DataFrame:
        df["NOMBRE"] = df["NOMBRE"].apply(normalize_municipalities)
        df["cod"] = df["CPRO"].astype(str) + df["CMUN"].astype(str)
        df.set_index("cod", inplace=True)
        df.rename(columns={"NOMBRE": "municipalities"}, inplace=True)
        return df[["municipalities"]]

    def save_to_json(data: dict, file_path: Path):
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, ensure_ascii=False)
        print(f"Archivo JSON guardado en: {file_path.resolve()}")

    # Leer y procesar los datos
    df = read_municipalities_excel(input_file)
    df_filtered = filter_canary_municipalities(df)
    df_processed = process_municipalities_data(df_filtered)

    # Guardar en JSON
    save_to_json(df_processed.to_dict(orient="index"), output_file)


def main():
    """
    Ejecuta las funciones principales de descarga y procesamiento de municipios.
    """

    # Descargar el archivo Excel
    download_municipalities_excel(MUNICIPALITIES_EXCEL_PATH)

    # Generar el archivo JSON
    generate_municipalities_json(
        MUNICIPALITIES_EXCEL_PATH, MUNICIPALITIES_JSON_PATH
    )


if __name__ == "__main__":
    main()
