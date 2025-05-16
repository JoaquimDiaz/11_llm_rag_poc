"""
Tests for scripts.fetching.fetch_data

Includes
--------
- A test for a successful API response.
- A test for an empty API response, which must raise ValueError.
"""
from pathlib import Path
from unittest.mock import patch
import pytest
import scripts.fetching as fetching


# ---------------------------------------------------------------------------
# SUCCESS CASE
# ---------------------------------------------------------------------------
@patch("scripts.fetching.pl.DataFrame.write_parquet")                     
@patch("scripts.fetching.validation.Event.model_validate", side_effect=lambda x: x)  
@patch("scripts.fetching.get_json_from_api")                              
def test_main_success(mock_fetch, mock_validate, mock_write, tmp_path):
    """
    fetch_data should run without error when the API returns at least one doc.
    """
    mock_fetch.return_value = [{"field": "value"}]        

    fetching.fetch_data(
        region="TEST",     
        limit=1,
        since=0,
        until=0,
        destination=tmp_path / "out.parquet",
    )


# ---------------------------------------------------------------------------
# EMPTY RESPONSE CASE
# ---------------------------------------------------------------------------
@patch.object(fetching, "get_json_from_api")
def test_main_no_data(mock_fetch, tmp_path):
    """
    fetch_data should raise ValueError when the API returns an empty list.
    """
    mock_fetch.return_value = []                          

    with pytest.raises(ValueError):
        fetching.fetch_data(
            region="TEST",
            limit=1,
            since=0,
            until=0,
            destination=tmp_path / "out.parquet",
        )
