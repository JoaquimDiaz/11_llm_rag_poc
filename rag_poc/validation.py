from pydantic import BaseModel, ConfigDict, field_validator, model_validator
from typing import List, Optional
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

from rag_poc import config

class Coordinates(BaseModel):
    lon: float
    lat: float

class Event(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    uid: str
    canonicalurl: str
    title_fr: str
    description_fr: Optional[str]
    longdescription_fr: Optional[str]
    location_city: Optional[str]
    conditions_fr: Optional[str]
    keywords_fr: Optional[List[str]]
    firstdate_begin: datetime
    firstdate_end: datetime
    lastdate_begin: datetime
    lastdate_end: datetime
    accessibility_label_fr: Optional[List[str]]
    location_coordinates: Optional[Coordinates]

    @field_validator('longdescription_fr')
    @classmethod
    def strip_html(cls, v: str) -> str:
        return BeautifulSoup(v, "html.parser").get_text(separator=" ").strip() if v else None

    @field_validator('firstdate_begin', 'firstdate_end', 'lastdate_begin', 'lastdate_end', mode='before')
    @classmethod
    def parse_datetime(cls, v: str) -> datetime:
        return datetime.fromisoformat(v)

    @field_validator('firstdate_begin', mode='after')
    @classmethod
    def validate_begin_date(cls, v: datetime) -> datetime:
        since = datetime.now(v.tzinfo) - timedelta(config.SINCE)
        if v < datetime.now(v.tzinfo):
            raise ValueError("Date must not be more than one year old.")
        return v
    
    @field_validator('lastdate_begin', mode='after')
    @classmethod
    def validate_end_date(cls, v: datetime) -> datetime:
        until = datetime.now(v.tzinfo) + timedelta(config.UNTIL)
        if v > until:
            raise ValueError(
                f"lastdate_begin is too far in the future (>{config.UNTIL} days). Value: {v.isoformat()}"
            )
        return v
    
    @model_validator(mode='before')
    @classmethod
    def check_region(cls, values):
        region = values.get("location_region")
        if region != config.REGION:
            raise ValueError(f"Invalid region: {region}. Only '{config.REGION}' is accepted.")
        return values
