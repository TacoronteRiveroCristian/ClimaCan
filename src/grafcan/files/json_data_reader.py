"""
Basic script to read Grafcan JSON data files from a specified directory structure
and convert each into a Pandas DataFrame for inspection.

Directory structure expected:
<input_dir>/<thing_id>/<year>/<month>/<variable_name>.json
"""

import argparse
import json
import logging
from pathlib import Path

import pandas as pd

from src.grafcan.classes.utils import normalize_variable_name

# Setup logger
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

DEFAULT_INPUT_DIR = (
    "src/grafcan/files/grafcan_data_output"  # Default directory if not provided
)


def process_json_file_to_df(file_path):
    """Reads a single JSON data file and converts it to a Pandas DataFrame."""
    try:
        with open(file_path, "r") as f:
            observations = json.load(f)

        if not observations:
            logger.info(
                f"No observations found in {file_path}. Returning empty DataFrame."
            )
            return pd.DataFrame()  # Return an empty DataFrame

        df = pd.DataFrame(observations)

        # Basic check for essential columns
        if "resultTime" not in df.columns:
            logger.warning(
                f"File {file_path} is missing 'resultTime' column. Cannot convert to datetime."
            )
            # Optionally, you might still return df here or an empty one depending on desired strictness
            return df  # Or pd.DataFrame()

        df["resultTime"] = pd.to_datetime(df["resultTime"])

        logger.info(
            f"Successfully created DataFrame from {file_path}. Shape: {df.shape}"
        )
        # You can add more processing or printing here, e.g.:
        # print(f"\nDataFrame from {file_path}:")
        # with pd.option_context('display.max_rows', 5):
        # print(df.head())
        return df

    except json.JSONDecodeError:
        logger.error(f"Error decoding JSON from {file_path}. Skipping.")
    except Exception as e:
        logger.error(f"Error processing file {file_path}: {e}. Skipping.")
    return pd.DataFrame()  # Return an empty DataFrame on error


def main():
    parser = argparse.ArgumentParser(
        description="Reads Grafcan JSON data files and creates Pandas DataFrames.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "input_dir",
        type=str,
        nargs="?",  # Makes the argument optional
        default=DEFAULT_INPUT_DIR,  # Uses the default if not provided
        help=f"Base directory containing the downloaded Grafcan JSON files. Defaults to '{DEFAULT_INPUT_DIR}'.",
    )
    # Optional: Add arguments for specific station, year, month if needed for filtering
    # parser.add_argument("--station-id", type=str, help="Specific station ID to process.")
    # parser.add_argument("--year", type=str, help="Specific year to process.")
    # parser.add_argument("--month", type=str, help="Specific month to process (requires --year).")

    args = parser.parse_args()

    base_input_path = Path(args.input_dir)
    if not base_input_path.is_dir():
        logger.error(
            f"Input directory '{base_input_path}' not found. Please create it or specify a valid path."
        )
        exit(1)

    logger.info(f"Starting to process JSON files from: {base_input_path}")
    file_count = 0
    df_creation_success = 0

    # Iterate through the directory structure
    # <input_dir>/<thing_id>/<year>/<month>/<variable_name>.json
    for station_dir in base_input_path.iterdir():
        if not station_dir.is_dir():
            continue
        # thing_id = station_dir.name # Example: if you want to use thing_id
        # if args.station_id and thing_id != args.station_id: continue

        for year_dir in station_dir.iterdir():
            if not year_dir.is_dir():
                continue
            # if args.year and year_dir.name != args.year: continue

            for month_dir in year_dir.iterdir():
                if not month_dir.is_dir():
                    continue
                # if args.month and month_dir.name != args.month: continue

                for json_file in month_dir.glob("*.json"):
                    file_count += 1
                    logger.info(f"Processing file: {json_file}")
                    df = process_json_file_to_df(json_file)
                    if not df.empty:
                        df_creation_success += 1
                        # Set resultTime as index
                        df = df.set_index("resultTime")
                        # Rename the index to "time"
                        df.index.name = "time"

                        # Get variable name from filename
                        variable_name_from_file = json_file.stem
                        normalized_var_name = normalize_variable_name(
                            variable_name_from_file
                        )

                        # Rename the column result to name of the variable
                        df = df.rename(columns={"result": normalized_var_name})
                    else:
                        logger.warning(
                            f"DataFrame for {json_file} is empty or could not be created."
                        )

    logger.info(
        f"Finished processing. Looked at {file_count} JSON files. Successfully created {df_creation_success} DataFrames."
    )


if __name__ == "__main__":
    main()
