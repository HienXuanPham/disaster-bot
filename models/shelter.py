from typing import List, Optional, Dict
from pydantic import BaseModel

class Shelter(BaseModel):
    id: Optional[str] = None
    name: str
    coordinates: List[float]
    address: Optional[str] = None
    shelter_type: str
    capacity: Optional[int] = None
    amenities: List[str] = []
    contact_info: Optional[Dict[str, str]] = None
    description: Optional[str] = None
    embedding: Optional[List[float]] = None
