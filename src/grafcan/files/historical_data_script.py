# /usr/local/bin/python

import argparse
import json
import logging
import os
import re
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import requests

# Setup logger
logger = logging.getLogger(__name__)

BASE_URL = "https://sensores.grafcan.es/api/v1.0"


def sanitize_filename(name):
    """Remove or replace characters not suitable for filenames."""
    name = re.sub(r"\s+", "_", name)  # Replace spaces with underscores
    name = re.sub(
        r"[^a-zA-Z0-9_.-]", "", name
    )  # Remove other invalid characters
    return name if name else "unnamed_variable"


def get_api_key():
    """Fetches the Grafcan API key from environment variables."""
    api_key = os.getenv("GRAFCAN_TOKEN")
    if not api_key:
        logger.error("GRAFCAN_TOKEN environment variable not set.")
        exit(1)
    return api_key


def make_api_request(url, params=None, headers=None):
    """Makes a GET request to the API and handles potential errors."""
    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4XX or 5XX)
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP error occurred: {http_err}")
        logger.error(f"Response content: {response.content}")
    except requests.exceptions.ConnectionError as conn_err:
        logger.error(f"Connection error occurred: {conn_err}")
    except requests.exceptions.Timeout as timeout_err:
        logger.error(f"Timeout error occurred: {timeout_err}")
    except requests.exceptions.RequestException as req_err:
        logger.error(f"An error occurred during the request: {req_err}")
    except json.JSONDecodeError as json_err:
        logger.error(f"Error decoding JSON response: {json_err}")
        logger.error(f"Response content: {response.text}")
    return None


def get_all_datastreams_for_thing(thing_id, headers):
    """Fetches all datastreams (variables) for a given thing_id."""
    all_datastreams = []
    url = f"{BASE_URL}/datastreams/"
    params = {"thing": thing_id, "page_size": 100}  # Adjust page_size if needed

    logger.info(f"Fetching all datastreams for Thing ID: {thing_id}...")
    while url:
        data = make_api_request(
            url, params=params if not all_datastreams else None, headers=headers
        )  # params only for first request
        if data and "results" in data:
            all_datastreams.extend(data["results"])
            url = data.get("next")
            params = None  # Clear params after first request as 'next' URL contains them
            if url:
                logger.info(f"Fetching next page of datastreams: {url}")
        else:
            logger.warning(
                "Could not retrieve datastreams or no results found."
            )
            break
    return all_datastreams


def find_datastream(datastreams, variable_identifier):
    """Finds a specific datastream by name (case-insensitive) or ID."""
    try:
        # Try to convert to int if it's an ID
        variable_id = int(variable_identifier)
        for ds in datastreams:
            if ds.get("id") == variable_id:
                return ds
    except ValueError:
        # If not an int, assume it's a name
        for ds in datastreams:
            if ds.get("name", "").lower() == variable_identifier.lower():
                return ds
    return None


def get_observations(
    datastream_id, start_time_str, end_time_str, headers, page_size=1000
):
    """Fetches observations for a given datastream and time range."""
    all_observations = []
    url = f"{BASE_URL}/observations/"
    params = {
        "datastream": datastream_id,
        "result_time_after": start_time_str,
        "result_time_before": end_time_str,
        "ordering": "result_time",
        "page_size": page_size,
    }
    logger.info(
        f"Fetching observations for Datastream ID: {datastream_id} from {start_time_str} to {end_time_str}"
    )

    while url:
        data = make_api_request(
            url,
            params=params if not all_observations else None,
            headers=headers,
        )  # params only for first request
        if data and "results" in data:
            all_observations.extend(data["results"])
            url = data.get("next")
            params = None  # Clear params after first request
            if url:
                logger.info(f"Fetching next page of observations...")
        else:
            if not all_observations:  # Only print if no data was fetched at all
                logger.warning(
                    f"No observations found or error fetching for Datastream ID: {datastream_id} in this period."
                )
            break
    return all_observations


def main():
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()],
    )

    parser = argparse.ArgumentParser(
        description="Extract historical data from Grafcan API or list available variables for a Thing."
    )
    parser.add_argument("thing_id", type=int, help="Thing ID for the station.")
    parser.add_argument(
        "--list-variables",
        action="store_true",
        help="List all available variables (Datastreams) for the given Thing ID and exit.",
    )
    parser.add_argument(
        "start_date",
        type=str,
        nargs="?",  # Make optional
        default=None,  # Default to None
        help="Start date for data extraction (YYYY-MM-DD). Required if not using --list-variables.",
    )
    parser.add_argument(
        "end_date",
        type=str,
        nargs="?",  # Make optional
        default=None,  # Default to None
        help="End date for data extraction (YYYY-MM-DD). Required if not using --list-variables.",
    )
    parser.add_argument(
        "--variable",
        type=str,
        default="ALL",
        help="Specific variable name or ID to fetch, or 'ALL' for all variables (default). Only used if not --list-variables.",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="grafcan_data_output",
        help="Base directory to save the output JSON files. Only used if not --list-variables.",
    )
    parser.add_argument(
        "--page_size",
        type=int,
        default=1000,
        help="Page size for API observation requests. Only used if not --list-variables.",
    )

    args = parser.parse_args()

    api_key = get_api_key()
    headers = {
        "accept": "application/json",
        "Authorization": f"Api-Key {api_key}",
    }

    if args.list_variables:
        logger.info(f"Listing variables for Thing ID: {args.thing_id}")
        available_datastreams = get_all_datastreams_for_thing(
            args.thing_id, headers
        )
        if available_datastreams:
            logger.info(
                f"Available variables (Datastreams) for Thing ID {args.thing_id}:"
            )
            for ds in available_datastreams:
                logger.info(
                    f"  Name: {ds.get('name', 'N/A')}, ID: {ds.get('id', 'N/A')}, Description: {ds.get('description', 'N/A')}"
                )
        else:
            logger.info(f"No variables found for Thing ID: {args.thing_id}.")
        return  # Exit after listing variables

    # If not --list-variables, then start_date and end_date are required
    if not args.start_date or not args.end_date:
        parser.error(
            "the following arguments are required when not using --list-variables: start_date, end_date"
        )

    try:
        start_datetime = datetime.strptime(args.start_date, "%Y-%m-%d")
        end_datetime = datetime.strptime(args.end_date, "%Y-%m-%d")
    except ValueError:
        logger.error("Invalid date format. Please use YYYY-MM-DD.")
        exit(1)

    if end_datetime < start_datetime:
        logger.error("End date cannot be before start date.")
        exit(1)

    base_output_path = Path(args.output_dir)

    available_datastreams = get_all_datastreams_for_thing(
        args.thing_id, headers
    )
    if not available_datastreams:
        logger.info(
            f"No datastreams found for Thing ID: {args.thing_id}. Exiting."
        )
        return

    datastreams_to_process = []
    if args.variable.upper() == "ALL":
        datastreams_to_process = available_datastreams
        # We don't need to print all variables again if they just listed them
        # and then decided to download all. But if they directly chose ALL, it's good to list.
        # However, the get_all_datastreams_for_thing already logs this.
        # Let's only log the "Starting data extraction..."
        logger.info(
            f"Starting data extraction for all variables for Thing ID {args.thing_id}..."
        )
    else:
        selected_ds = find_datastream(available_datastreams, args.variable)
        if selected_ds:
            datastreams_to_process.append(selected_ds)
            logger.info(
                f"Found requested variable: Name: {selected_ds.get('name', 'N/A')}, ID: {selected_ds.get('id', 'N/A')}"
            )
        else:
            logger.error(
                f"Variable '{args.variable}' not found for Thing ID {args.thing_id}."
            )
            logger.info(
                "Available variables are (run with --list-variables for more detail):"
            )
            for ds in available_datastreams:
                logger.info(
                    f"  Name: {ds.get('name', 'N/A')}, ID: {ds.get('id', 'N/A')}"
                )
            return

    current_month_start = datetime(start_datetime.year, start_datetime.month, 1)

    while current_month_start <= end_datetime:
        # Determine the end of the current month
        if current_month_start.month == 12:
            current_month_end = datetime(
                current_month_start.year + 1, 1, 1
            ) - timedelta(seconds=1)
        else:
            current_month_end = datetime(
                current_month_start.year, current_month_start.month + 1, 1
            ) - timedelta(seconds=1)

        # Ensure we don't go past the user-defined end_date for the last month
        actual_month_end_query = min(
            current_month_end,
            datetime(
                end_datetime.year,
                end_datetime.month,
                end_datetime.day,
                23,
                59,
                59,
            ),
        )
        actual_month_start_query = max(
            current_month_start,
            datetime(
                start_datetime.year,
                start_datetime.month,
                start_datetime.day,
                0,
                0,
                0,
            ),
        )

        # Make sure the start of the query is not after the end of the query for the current month
        if actual_month_start_query > actual_month_end_query:
            current_month_start = (
                datetime(
                    current_month_start.year, current_month_start.month + 1, 1
                )
                if current_month_start.month < 12
                else datetime(current_month_start.year + 1, 1, 1)
            )
            continue

        logger.info(
            f"\nProcessing data for month: {current_month_start.strftime('%Y-%m')}"
        )

        for ds in datastreams_to_process:
            ds_id = ds.get("id")
            ds_name = ds.get("name", f"unknown_variable_{ds_id}")
            sanitized_ds_name = sanitize_filename(ds_name)

            if not ds_id:
                logger.warning(f"Skipping datastream without ID: {ds_name}")
                continue

            logger.info(f"  Processing variable: {ds_name} (ID: {ds_id})")

            # Format for API: YYYY-MM-DDTHH:MM:SSZ
            api_start_time = actual_month_start_query.strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )
            api_end_time = actual_month_end_query.strftime("%Y-%m-%dT%H:%M:%SZ")

            observations = get_observations(
                ds_id, api_start_time, api_end_time, headers, args.page_size
            )

            if observations:
                output_path = (
                    base_output_path
                    / str(args.thing_id)
                    / str(current_month_start.year)
                    / f"{current_month_start.month:02d}"
                )
                output_path.mkdir(parents=True, exist_ok=True)
                file_path = output_path / f"{sanitized_ds_name}.json"

                try:
                    with open(file_path, "w") as f:
                        json.dump(observations, f, indent=4)
                    logger.info(
                        f"    Successfully saved {len(observations)} records to {file_path}"
                    )
                except IOError as e:
                    logger.error(f"    Error writing file {file_path}: {e}")

                # Optional: Convert to DataFrame for quick check, can be removed for performance
                # df = pd.DataFrame(observations)
                # if not df.empty:
                #     logger.info(f"    Sample of fetched data for {ds_name}:")
                #     logger.info(df[["resultTime", "result"]].head())
                # else:
                #     logger.info(f"    No data frame created, observations list might be structured differently or empty after all.")
            else:
                logger.info(
                    f"    No observations found for {ds_name} (ID: {ds_id}) in {current_month_start.strftime('%Y-%m')}."
                )
            logger.info("-" * 30)

        # Move to the next month
        if current_month_start.month == 12:
            current_month_start = datetime(current_month_start.year + 1, 1, 1)
        else:
            current_month_start = datetime(
                current_month_start.year, current_month_start.month + 1, 1
            )

    logger.info("\nData extraction process finished.")


if __name__ == "__main__":
    main()
