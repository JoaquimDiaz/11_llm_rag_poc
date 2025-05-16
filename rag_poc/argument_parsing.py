import argparse
import logging

from rag_poc import config

LEVEL_BY_VERBOSITY = {
    0: logging.WARNING,
    1: logging.INFO,
    2: logging.DEBUG,
}
MAX_VERBOSITY = max(LEVEL_BY_VERBOSITY)

def build_parser() -> argparse.ArgumentParser:
    """ Return an argument-parser configured """
    p = argparse.ArgumentParser(description="RAG-POC service")
    subparsers = p.add_subparsers(dest="command")

    # --------------------
    # Logs verbosity
    # --------------------
    p.add_argument(
        "-v", "--verbose",
        action="count",
        default=0,
        help="Increase log verbosity (-v, -vv for more)"
    )

    # --------------------
    # Run API fetching
    # --------------------
    fetch_parser = subparsers.add_parser("fetch", help="Run API fetching from opendata")
    fetch_parser.add_argument(
        "--region",
        type=str,
        default=config.REGION,
        help="The region to restrict the API request to."
    )
    fetch_parser.add_argument(
        "--since",
        type=int,
        default=config.SINCE, 
        help="The number of days in the past to include in the fetching."
    )
    fetch_parser.add_argument(
        "--until",
        type=int,
        default=config.UNTIL,
        help="The number of days in the futur to include in the fetching."
    )
    fetch_parser.add_argument(
        "--limit",
        type=int,
        default=config.LIMIT,
        help="Limit to apply to the API get response."
    )
    fetch_parser.add_argument(
        "--destination",
        type=str,
        default=config.DATA_FILE,
        help="Destination file to save the file to."
    )
    
    # --------------------
    # Run FAISS index building
    # --------------------
    indexing_parser = subparsers.add_parser("index", help="Run FAISS index building from source and save vector store")
    indexing_parser.add_argument(
        "--source",
        type=str,
        default=config.DATA_FILE,
        help="Path to the file source."
    )
    indexing_parser.add_argument(
        "--destination",
        type=str,
        default=config.VECTORS_FOLDER,
        help="Path to the destination folder for the FAISS index and metadata."
    )
    indexing_parser.add_argument(
        "--columns",
        nargs='+',
        default=config.COLUMN_EMBEDDING,
        help="List of columns to use for the embedding."
    )
    indexing_parser.add_argument(
        "--id",
        type=str,
        default=config.ID_COLUMN,
        help="Space-separated list of columns to use for the embedding."
    )

    # --------------------
    # Run Streamlit app
    # --------------------
    serve_parser = subparsers.add_parser("app", help="Run Streamlit RAG app")
    serve_parser.add_argument(
        "--port",
        type=int,
        default=8501,
        help="Port to serve the Streamlit app on (default: 8501)"
    )

    return p

def set_verbosity(v_count: int) -> int:
    """
    Map the -v count to a logging level.
    If there is more than two flags, returns the max verbosity level.
    """
    level = min(v_count, MAX_VERBOSITY)
    return LEVEL_BY_VERBOSITY.get(level, logging.DEBUG)