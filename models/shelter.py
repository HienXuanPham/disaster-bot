from typing import List, Optional
from pydantic import BaseModel

class Shelter(BaseModel):
    id: Optional[str] = None
    name: str
    coordinates: List[float]
    address: Optional[str] = None
    shelter_type: str
    capacity: Optional[int] = None
    amenities: List[str] = []
    description: Optional[str] = None
    embedding: Optional[List[float]] = None
