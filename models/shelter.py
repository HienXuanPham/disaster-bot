from typing import Any, List, Optional, Dict
from pydantic import BaseModel

class Shelter(BaseModel):
    id: Optional[str] = None
    name: str
    locations: Dict[str, Any]
    address: Optional[str] = None
    shelter_type: str
    capacity: Optional[int] = None
    amenities: List[str] = []
    contact_info: Optional[Dict[str, str]] = None
    description: Optional[str] = None
    embedding: Optional[List[float]] = None

    @classmethod
    def from_coordinates(cls, lat: float, lon: float, **kwargs):
        return cls(
            locations={
                "type": "Point",
                "coordinates": [lon, lat]
            },
            **kwargs
        )