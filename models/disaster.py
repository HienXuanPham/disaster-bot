from typing import List, Optional
from pydantic import BaseModel, field_validator
from datetime import datetime, timezone

class Earthquake(BaseModel):
    place: str
    magnitude: float
    coordinates: List[float]
    time: Optional[datetime] = None
    description: Optional[str] = None
    severity: str

    @field_validator('time', pre=True)
    def convert_timestamp(cls, v):
        if isinstance(v, int):  # milliseconds to datetime
            return datetime.fromtimestamp(v / 1000, tz=timezone.utc)
        return v
