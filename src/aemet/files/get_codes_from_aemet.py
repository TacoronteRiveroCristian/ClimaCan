"""
"""

import json
from pathlib import Path

import pandas as pd

from conf import WORKDIR
from src.common.functions import normalize_text


def normalize_municipalities(name: str) -> str:
    """
    Normaliza el nombre del municipio eliminando caracteres especiales y ajustando el formato.

    :param name: Nombre del municipio original.
    :return: Nombre del municipio normalizado.
    """
    name = normalize_text(name)
    return name.split(",")[0].replace(" ", "_")


def read_municipalities_excel(file_path: Path) -> pd.DataFrame:
    """
    Lee un archivo Excel con información de municipios y devuelve un DataFrame.

    :param file_path: Ruta del archivo Excel.
    :return: DataFrame con los datos del Excel.
    """
    return pd.read_excel(io=file_path, header=1, dtype=str)


def filter_canary_municipalities(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filtra los municipios de Santa Cruz de Tenerife y Las Palmas.

    :param df: DataFrame original.
    :return: DataFrame filtrado con solo los municipios de interés.
    """
    mask = df["CPRO"].isin(["38", "35"])
    return df[mask].copy()


def process_municipalities_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normaliza y procesa los datos de los municipios.

    :param df: DataFrame original filtrado.
    :return: DataFrame procesado con los nombres normalizados y un índice único.
    """
    df["NOMBRE"] = df["NOMBRE"].apply(normalize_municipalities)
    df["cod"] = df["CPRO"].astype(str) + df["CMUN"].astype(str)
    df.set_index("cod", inplace=True)
    df.rename(columns={"NOMBRE": "municipalities"}, inplace=True)
    return df[["municipalities"]]


def save_to_json(data: dict, file_path: Path):
    """
    Guarda un diccionario en un archivo JSON, asegurándose de que las carpetas contenedoras existen.

    :param data: Diccionario a guardar.
    :param file_path: Ruta completa del archivo JSON.
    """
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)
    print(f"Archivo JSON guardado en: {file_path.resolve()}")


def main():
    """
    Función principal para ejecutar el procesamiento y guardar los datos.
    """
    # Ruta del archivo Excel de entrada
    input_file = WORKDIR / "src/aemet/artifacts/municipalities.xlsx"

    # Ruta del archivo JSON de salida
    output_file = WORKDIR / "src/aemet/artifacts/municipalities.json"

    # Leer y procesar los datos
    df = read_municipalities_excel(input_file)
    df_filtered = filter_canary_municipalities(df)
    df_processed = process_municipalities_data(df_filtered)

    # Guardar los datos procesados en un archivo JSON
    save_to_json(df_processed.to_dict(orient="index"), output_file)


if __name__ == "__main__":
    main()
