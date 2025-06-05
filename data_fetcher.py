from typing import List
import logging
from services.shelter_service import ShelterService
from services.earthquake_service import EarthquakeService
from models.shelter import Shelter
from models.disaster import Earthquake

logger = logging.getLogger(__name__)

class DataFetcher:
  def __init__(self):
    self.shelter_service = ShelterService()
    self.earthquake_service = EarthquakeService()

  async def fetch_osm_shelters(self, bbox: str = None) -> List[Shelter]:
    try:
      if not bbox:
        bbox = "37.0,-125.0,49.0,-66.0" # Default
      
      logger.info(f"Fetching shelters for bbox: {bbox}")

      shelters_data = await self.shelter_service.extract_shelters_from_osm(bbox)
      
      logger.info(f"Successfully processed {len(shelters_data)} shelters")
      return shelters_data
    except Exception as e:
      logger.error(f"Error fetching OSM shelters: {e}")
      return []
    
  async def fetch_earthquakes(self) -> List[Earthquake]:
    try:
      earthquakes_data = await self.earthquake_service.fetch_earthquakes_data()

      logger.info(f"Successfully fetched {len(earthquakes_data)} earthquakes data")
      return earthquakes_data
    except Exception as e:
      logger.error(f"Error fetching USGS data: {e}")
      return []


