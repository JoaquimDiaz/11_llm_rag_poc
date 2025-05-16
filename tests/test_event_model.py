"""
Tests for the `Event` Pydantic model in rag_poc.validation.

Covers:
- Validation of a correct event input.
- Rejection of events with:
    - Invalid region.
    - Dates too far in the past.
    - Dates too far in the future.
    - Malformed date strings.
"""

import pytest
from pydantic import ValidationError
from datetime import datetime, timedelta, timezone
from rag_poc import validation, config 

# A sample valid event used as the base for most tests
VALID_EVENT = {
    "uid": "event123",
    "canonicalurl": "https://example.com/event123",
    "title_fr": "Un évènement",
    "description_fr": "Une description.",
    "longdescription_fr": "<p>Contenu long</p>",
    "conditions_fr": "Aucune",
    "location_city": "Ville",
    "keywords_fr": ["art", "musique"],
    "firstdate_begin": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
    "firstdate_end": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat(),
    "lastdate_begin": (datetime.now(timezone.utc) + timedelta(days=3)).isoformat(),
    "lastdate_end": (datetime.now(timezone.utc) + timedelta(days=4)).isoformat(),
    "accessibility_label_fr": ["PMR"],
    "location_coordinates": {"lat": 48.11, "lon": -1.67},
    "location_region": config.REGION,
}

def test_valid_event_passes():
    """
    Test that a valid event dictionary creates an Event instance without error.
    """
    event = validation.Event(**VALID_EVENT)
    assert event.uid == "event123"

def test_invalid_region_raises():
    """
    Test that an invalid region raises a validation error.
    """
    data = VALID_EVENT.copy()
    data["location_region"] = "WrongRegion"
    with pytest.raises(ValidationError) as exc:
        validation.Event(**data)
    assert "Invalid region" in str(exc.value)

def test_past_firstdate_begin_raises():
    """
    Test that an event with firstdate_begin more than one year in the past fails validation.
    """
    data = VALID_EVENT.copy()
    since = config.SINCE - 1
    data["firstdate_begin"] = (datetime.now(timezone.utc) - timedelta(days=since)).isoformat()
    with pytest.raises(ValidationError) as exc:
        validation.Event(**data)
    assert "Date must not be more than one year old." in str(exc.value)

def test_far_future_lastdate_begin_raises():
    """
    Test that an event with lastdate_begin too far in the future is rejected.
    """
    data = VALID_EVENT.copy()
    until = config.UNTIL + 1
    data["lastdate_begin"] = (datetime.now(timezone.utc) + timedelta(days=until)).isoformat()
    with pytest.raises(ValidationError) as exc:
        validation.Event(**data)
    assert "lastdate_begin is too far in the future" in str(exc.value)

def test_invalid_date_format_raises():
    """
    Test that an improperly formatted date string raises a validation error.
    """
    data = VALID_EVENT.copy()
    data["firstdate_begin"] = "not-a-date"
    with pytest.raises(ValidationError):
        validation.Event(**data)
