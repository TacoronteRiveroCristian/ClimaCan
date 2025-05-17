import os
import re

import pandas as pd
import requests

API_KEY = os.getenv("GRAFCAN_TOKEN")
BASE = "https://sensores.grafcan.es/api/v1.0"
HEADERS = {
    "accept": "application/json",
    "Authorization": f"Api-Key {API_KEY}",
}

streams = requests.get(
    f"{BASE}/datastreams/",
    params={"thing": 30},  # thing_id = 30  → Alojera
    headers=HEADERS,
).json()["results"]

temp_ds = None
for s in streams:
    try:
        if re.search(r"(?i)temp(erature)?", s["name"]):
            temp_ds = s
            break
    except KeyError as e:
        print(f"Error accediendo a stream: {e}")
        print(f"Stream problemático: {s}")
        continue

if temp_ds is None:
    print("No se encontró ningún datastream de temperatura.")
    exit()

ds_id = temp_ds["id"]

print(f"Obteniendo datos para el datastream ID: {ds_id}")

obs_response = requests.get(
    f"{BASE}/observations/",
    params={
        "datastream": ds_id,
        "result_time_after": "2021-05-17T00:00:00Z",
        "result_time_before": "2021-05-17T23:59:59Z",
        "ordering": "result_time",
        "page_size": 1000,
    },
    headers=HEADERS,
).json()

all_observations = obs_response["results"]
next_page_url = obs_response.get("next")

while next_page_url:
    print(f"Fetching next page: {next_page_url}")
    page_response = requests.get(next_page_url, headers=HEADERS).json()
    all_observations.extend(page_response["results"])
    next_page_url = page_response.get("next")

if all_observations:
    df = pd.DataFrame(all_observations)
    print(f"Total de registros obtenidos: {len(df)}")
    if not df.empty:
        print(df[["resultTime", "result"]])
    else:
        print("El DataFrame está vacío después de procesar las observaciones.")
else:
    print("No se obtuvieron datos.")
