"""
Fetch data from the OpenData API, validate it, and save to a Parquet file.

Steps:
    1. Send a GET request to the API endpoint.
    2. Validate the response using a Pydantic model.
    3. Clean the HTML content (if applicable).
    4. Save valid data to a Parquet file.

Configuration:
    Constants are defined in `rag_poc/config.py`, including:
        - UNTIL: Number of days in the future to filter.
        - REGION: The French region to restrict data to.
        - WRITE_ERRORS: If True, write validation errors to a file.
"""

from datetime import datetime, timedelta
import json
import logging
import pathlib
import polars as pl
from pydantic import ValidationError
import requests
from typing import Optional, List, Dict, Any

from rag_poc import config, validation

logger = logging.getLogger(__name__)

def fetch_data(
    region: str, 
    limit: int, 
    since: int, 
    until: int,
    destination: pathlib.Path
) -> None:
    """
    
    """
    # ------ Parameters ------
    date_since: str = (datetime.today() - timedelta(days=since)).strftime("%Y-%m-%dT%H:%M:%S")
    date_until: str = (datetime.today() + timedelta(days=until)).strftime("%Y-%m-%dT%H:%M:%S")
    url: str = f'{config.BASE_URL}{config.ENDPOINT}'

    params = {
        'where': (
            f'location_region="{region}"'
            f' AND firstdate_begin >= "{date_since}"'
            f' AND lastdate_begin <= "{date_until}"'
        ),
        'limit': limit
    }

    logger.debug("url=%s", url)
    logger.debug("since=%s", since)
    logger.debug("until=%s", until)
    logger.debug("params=%s", params)

    setup_folders()
    
    # ------ 1. Fetching data from the API ------#

    data_raw: list = get_json_from_api(url=url, params=params)

    if not data_raw:
        raise ValueError("The API call did not return any data.")
    
    logger.debug(data_raw[0])

    # ------ 2. Validating documents ------ #

    data = []
    wrong_data_list = []

    for doc in data_raw:
        try:
            data.append(validation.Event.model_validate(doc))
        except ValidationError as e:
            wrong_data_list.append({'doc': doc, 'error': e})
    
    if wrong_data_list:
        logger.warning("Documents received from API did not pass validation: %i", len(wrong_data_list))
        
        if config.WRITE_ERRORS:
            logger.warning(f"Writing errors to '{config.ERROR_FILE}'")

            error_file = config.ERROR_FILE.with_suffix(".jsonl")

            if not error_file.exists():
                logger.info("Error file does not exist, creating error file: `%s`.", error_file)
                error_file.touch()

            with error_file.open("w", encoding="utf-8") as file:
                for item in wrong_data_list:
                    json.dump(item, file, ensure_ascii=False, default=str)
                    file.write("\n")

    df = pl.DataFrame(data, infer_schema_length=1000)

    logger.info(f"Final data shape: {df.shape}")

    # ------ 3. Writing data to parquet ------
    output_file = destination

    df.write_parquet(output_file)
    logger.info("Data saved to '%s'", output_file)

def setup_folders() -> None:
    """" Make sure the various data folders exist. Create them if missing. """
    if not config.DATA.exists():
        logger.warning("DATA folder does not exist.")
        logger.warning("Creating data folder: `%s`.", config.DATA)
        config.DATA.mkdir()

    if not config.RAW.exists():
        logger.warning("RAW folder does not exist.")
        logger.warning("Creating RAW folder: `%s`.", config.RAW)
        config.RAW.mkdir()

    if not config.VECTORS_FOLDER.exists():
        logger.warning("VECTORS_FOLDER folder does not exist.")
        logger.warning("Creating VECTORS_FOLDER: `%s`.", config.VECTORS_FOLDER)
        config.VECTORS_FOLDER.mkdir()

def get_json_from_api(
        url: str, 
        params: Dict[str, str] = None,
        timeout: Optional[int] = 10
) -> List[Dict[str, Any]]:
    """
    Fetch JSON from an API and return it as a list of dictionaries.
    Wraps single-dict responses in a list for consistency.
    """
    if params is None:
        params = {}

    try:
        response = requests.get(url=url, params=params, timeout=timeout)
        response.raise_for_status()
        data = response.json()
        return data if isinstance(data, list) else [data]
    
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Request failed: {e}")

if __name__== "__main__":
   fetch_data(
       region=config.REGION,
       limit=10,
       since=config.SINCE,
       until=config.UNTIL,
       destination=config.DATA_FILE
   ) 