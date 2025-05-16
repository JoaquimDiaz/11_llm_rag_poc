from datetime import datetime
from dotenv import load_dotenv
import logging
import logging.config
import os
from pathlib import Path
from typing import Optional

today = datetime.now().strftime(format="%y%m%d")

LOG_FILE = f"pipeline_log_{today}.log"
LOG_LEVEL = logging.INFO

#01_fetch_api
BASE_URL = 'https://public.opendatasoft.com/api/explore/v2.1'
ENDPOINT = '/catalog/datasets/evenements-publics-openagenda/exports/json'

LIMIT = 5000
REGION = 'Bretagne'
SINCE = 365
UNTIL = 365

HTML_COLUMN = 'longdescription_fr'

WRITE_ERRORS = True

#02_build_index
ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

load_dotenv(ROOT / ".env") 

RAW        = DATA / "raw"
VECTORS_FOLDER    = DATA / "vectors"

DATA_FILE =  (RAW / "api_data").with_suffix(".parquet")
ERROR_FILE =  DATA / "error"

TEXTS_FILE = VECTORS_FOLDER / "texts"
EMBED_FILE = VECTORS_FOLDER / "embeddings"
INDEX_FILE = str(VECTORS_FOLDER / "index.faiss") # Writing as str because faisse io doesnt accept Path object
META_FILE  = VECTORS_FOLDER / "metadata"

ID_COLUMN = 'uid'
COLUMN_EMBEDDING = [
    "title_fr",
    "longdescription_fr",
    "description_fr",
    "conditions_fr"
]

def load_api_key(key: Optional[str] = "MISTRAL_API_KEY") -> str:
    """
    Load api key from the .env file.
    """
    load_dotenv()
    api_key = os.getenv(key)

    if not api_key:
        raise ValueError("No api key retrieved")

    return api_key

def setup_logging(level = logging.INFO) -> None:
    """
    Setup basicConfig for logging, with output to the console.
    """
    logging.basicConfig(
        level=level,
        format="%(levelname)s [%(module)s|L%(lineno)d] %(asctime)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S"
    )

if __name__ == "__main__":

    load_api_key()
    print("done")
