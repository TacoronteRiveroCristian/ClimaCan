"""
Processes downloaded Grafcan JSON data, creates Pandas DataFrames,
and writes the data to InfluxDB using ctrutils.

This script expects data to be organized in the directory structure created by
'grafcan_data_downloader.py':
<input_dir>/<thing_id>/<year>/<month>/<variable_name>.json

Prerequisites:
- Python 3.x
- pandas library (`pip install pandas`)
- ctrutils library (ensure it's in your PYTHONPATH and configured for InfluxDB)
- Environment variables for InfluxDB connection (or passed as arguments for ctrutils):
    - INFLUXDB_HOST
    - INFLUXDB_PORT
    - INFLUXDB_TIMEOUT
    - INFLUXDB_DATABASE (used as the database/bucket name)

Usage Examples:

1. Process all data in 'grafcan_data_output' and send to InfluxDB
   (assuming InfluxDB environment variables for ctrutils are set):
   ----------------------------------------------------------------
   python grafcan_to_influxdb.py grafcan_data_output --influx-database grafcan_historic_data

2. Process data and specify InfluxDB parameters for ctrutils directly:
   ----------------------------------------------------------------
   python grafcan_to_influxdb.py grafcan_data_output \
       --influx-host your_influx_host \
       --influx-port 8086 \
       --influx-database your_target_database_bucket \
       --influx-timeout 5000

3. Process data for a specific station ID (e.g., 30) within the input directory:
   ----------------------------------------------------------------
   python grafcan_to_influxdb.py grafcan_data_output --influx-database grafcan --station-id 30

4. Process data for a specific year and month for all stations:
    ----------------------------------------------------------------
    python grafcan_to_influxdb.py grafcan_data_output --influx-database grafcan --year 2023 --month 01
"""

import argparse
import json
import logging
import os
import re
from pathlib import Path

import pandas as pd

# Assuming ctrutils is in the PYTHONPATH
from ctrutils.database.influxdb.InfluxdbOperation import InfluxdbOperation

# Setup logger
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)


def sanitize_measurement_name(name):
    """Sanitize variable name to be a valid InfluxDB measurement name."""
    name = re.sub(r"\s+", "_", name)
    name = re.sub(r"[^a-zA-Z0-9_.-]", "", name)
    return name if name else "unknown_measurement"


def process_file_to_dataframe(file_path, thing_id, variable_name_original):
    """Reads a JSON data file and converts its observations to a Pandas DataFrame."""
    try:
        with open(file_path, "r") as f:
            observations = json.load(f)

        if not observations:
            logger.info(f"No observations found in {file_path}. Skipping.")
            return None

        df = pd.DataFrame(observations)
        if "resultTime" not in df.columns or "result" not in df.columns:
            logger.warning(
                f"File {file_path} does not contain 'resultTime' or 'result' columns. Skipping."
            )
            return None

        df["time"] = pd.to_datetime(df["resultTime"])
        df = df.rename(columns={"result": "value"})
        df["thing_id"] = str(thing_id)

        df = df[["time", "value", "thing_id"]]
        df = df.set_index(
            "time"
        )  # Set time as index after it has been converted

        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        df.dropna(subset=["value"], inplace=True)

        if df.empty:
            logger.info(
                f"DataFrame for {file_path} is empty after processing. Skipping."
            )
            return None
        return df

    except json.JSONDecodeError:
        logger.error(f"Error decoding JSON from {file_path}. Skipping.")
    except Exception as e:
        logger.error(f"Error processing file {file_path}: {e}. Skipping.")
    return None


def convert_df_to_points(df, measurement_name):
    """Converts a DataFrame to a list of points for InfluxdbOperation."""
    points = []
    if df is None or df.empty:
        return points

    # Assuming 'thing_id' is uniform for all rows in this df, as it comes from one file/station context
    # If not, row['thing_id'] should be used inside the loop.
    # For safety, let's assume it might vary if the DataFrame structure changes later.
    # However, current df structure has thing_id as a single value per df.

    for timestamp, row in df.iterrows():
        point = {
            "measurement": measurement_name,
            "tags": {
                "thing_id": str(row["thing_id"])
            },  # thing_id is a column in the df
            "time": timestamp.to_pydatetime(),  # Use Python datetime object
            "fields": {"value": row["value"]},
        }
        points.append(point)
    return points


def write_to_influxdb_ctrutils(
    client: InfluxdbOperation,
    database: str,
    points: list,
    measurement_name: str,
):
    """Writes points to InfluxDB using InfluxdbOperation."""
    if not points:
        logger.info(f"No points to write for measurement {measurement_name}.")
        return False

    try:
        logger.info(
            f"Writing {len(points)} points to InfluxDB for measurement '{measurement_name}' into database/bucket '{database}'"
        )
        # The ctrutils example uses `database` parameter in write_points.
        # Ensure your InfluxdbOperation handles this correctly for your InfluxDB version (v1 bucket or v2 mapping).
        client.write_points(database=database, points=points)
        logger.info(
            f"Successfully wrote data for {measurement_name} to InfluxDB database/bucket '{database}'."
        )
        return True
    except Exception as e:
        logger.error(
            f"Error writing data for {measurement_name} to InfluxDB via ctrutils: {e}"
        )
    return False


def main():
    parser = argparse.ArgumentParser(
        description="Process Grafcan JSON data and write to InfluxDB using ctrutils.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "input_dir",
        type=str,
        help="Base directory containing the downloaded Grafcan JSON files (e.g., grafcan_data_output).",
    )
    parser.add_argument(
        "--influx-host",
        type=str,
        default=os.getenv("INFLUXDB_HOST", "localhost"),
        help="InfluxDB host. Can also be set via INFLUXDB_HOST environment variable.",
    )
    parser.add_argument(
        "--influx-port",
        type=int,
        default=int(os.getenv("INFLUXDB_PORT", 8086)),
        help="InfluxDB port. Can also be set via INFLUXDB_PORT environment variable.",
    )
    parser.add_argument(
        "--influx-timeout",
        type=int,
        default=int(
            os.getenv("INFLUXDB_TIMEOUT", 10000)
        ),  # Assuming milliseconds
        help="InfluxDB connection timeout (ms). Can also be set via INFLUXDB_TIMEOUT environment variable.",
    )
    parser.add_argument(
        "--influx-database",  # Changed from influx-bucket
        type=str,
        default=os.getenv("INFLUXDB_DATABASE"),
        help="InfluxDB database/bucket name. Can also be set via INFLUXDB_DATABASE environment variable.",
    )
    parser.add_argument(
        "--station-id",
        type=str,
        default=None,
        help="(Optional) Process data only for this specific station ID (Thing ID). Processes all if not specified.",
    )
    parser.add_argument(
        "--year",
        type=str,
        default=None,
        help="(Optional) Process data only for this specific year (e.g., 2023). Processes all years if not specified.",
    )
    parser.add_argument(
        "--month",
        type=str,
        default=None,
        help="(Optional) Process data only for this specific month (e.g., 01 for January). Processes all months if not specified. Requires --year to be set.",
    )

    args = parser.parse_args()

    if not args.influx_database:
        logger.error(
            "InfluxDB database/bucket name not provided. Set INFLUXDB_DATABASE or use --influx-database."
        )
        exit(1)

    if args.month and not args.year:
        parser.error("--month argument requires --year to be specified.")

    input_path = Path(args.input_dir)
    if not input_path.is_dir():
        logger.error(f"Input directory not found: {args.input_dir}")
        exit(1)

    try:
        logger.info(
            f"Attempting to connect to InfluxDB at {args.influx_host}:{args.influx_port} with timeout {args.influx_timeout}ms."
        )
        client = InfluxdbOperation(
            host=args.influx_host,
            port=args.influx_port,
            timeout=args.influx_timeout,
        )
        # Ping functionality might not be available or named 'ping' in InfluxdbOperation.
        # The example in write_last_observations.py does not show a ping.
        # If connection fails, it will likely raise an error during write_points.
        logger.info(
            f"InfluxdbOperation client initialized. Connectivity will be tested upon first write."
        )
    except Exception as e:
        logger.error(f"Failed to initialize InfluxdbOperation client: {e}")
        exit(1)

    processed_files = 0
    written_to_influx_count = 0

    for station_dir in input_path.iterdir():
        if not station_dir.is_dir():
            continue
        thing_id = station_dir.name
        if args.station_id and thing_id != args.station_id:
            logger.debug(
                f"Skipping station {thing_id} as it does not match requested station ID {args.station_id}."
            )
            continue

        for year_dir in station_dir.iterdir():
            if not year_dir.is_dir():
                continue
            year = year_dir.name
            if args.year and year != args.year:
                logger.debug(
                    f"Skipping year {year} for station {thing_id} as it does not match requested year {args.year}."
                )
                continue

            for month_dir in year_dir.iterdir():
                if not month_dir.is_dir():
                    continue
                month = month_dir.name
                if args.month and month != args.month:
                    logger.debug(
                        f"Skipping month {month} for station {thing_id}, year {year} as it does not match requested month {args.month}."
                    )
                    continue

                logger.info(
                    f"Processing data for Station: {thing_id}, Year: {year}, Month: {month}"
                )
                for data_file in month_dir.glob("*.json"):
                    variable_name_original = data_file.stem
                    measurement_name = sanitize_measurement_name(
                        variable_name_original
                    )

                    logger.info(
                        f"  Reading file: {data_file} for variable: {variable_name_original}"
                    )

                    df = process_file_to_dataframe(
                        data_file, thing_id, variable_name_original
                    )
                    if df is not None and not df.empty:
                        points = convert_df_to_points(df, measurement_name)
                        if write_to_influxdb_ctrutils(
                            client,
                            args.influx_database,
                            points,
                            measurement_name,
                        ):
                            written_to_influx_count += 1
                        processed_files += 1
                    else:
                        logger.info(
                            f"    Skipping InfluxDB write for {data_file} as DataFrame is empty or invalid."
                        )

    logger.info(
        f"Finished processing. Processed {processed_files} files. Successfully wrote data for {written_to_influx_count} data batches to InfluxDB."
    )
    # client.close() # InfluxdbOperation might not have a close() method or might manage connections differently.
    # Refer to ctrutils documentation. For now, removing explicit close.


if __name__ == "__main__":
    main()
