import aiohttp
from typing import List, Dict, Any
import logging
from geopy.geocoders import Nominatim
from models.disaster import Earthquake

logger = logging.getLogger(__name__)

class EarthquakeService:
  def __init__(self):
    self.usgs_url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson"
    self.geolocator = Nominatim(user_agent="disaster_bot")
    self.earthquakes_data: List[Earthquake] = []

  async def fetch_earthquakes_data(self) -> List[Dict[str, Any]]:
    try:
      logger.info("Fetching earthquake data from USGS...")

      async with aiohttp.ClientSession() as session:
        async with session.get(self.usgs_url) as response:
          if response.status == 200:
            data = await response.json()

            earthquakes_data = []
            for feature in data.get("features", []):
              props = feature.get("properties", {})
              geom = feature.get("geometry", {})
              coordinates = geom.get("coordinates", [])

              earthquake = self._parse_earthquake_data(props, coordinates)

              if earthquake:
                earthquakes_data.append(earthquake)
            
            self.earthquakes_data = earthquakes_data
            logger.info(f"{len(earthquakes_data)} earthquakes")
            return earthquakes_data
          else:
            logger.info(f"Failed to fetch data: {response.status}")
            return []
    except Exception as e:
      logger.error(f"Error fetching earthquakes: {e}")
      return []

  async def _parse_earthquake_data(self, props, coordinates) -> Dict[str, any]:
    try:
      mag = props.get("mag", 0)
      if mag is None:
        return None

      if len(coordinates) < 2:
        return None
      
      lon, lat = coordinates[0], coordinates[1]

      location_name = await self._reverse_geocode(lat, lon)
      description = f"Magnitude {mag} earthquake occurred in {location_name}"
      if mag >= 6.0:
        description += " - This is considered a strong earthquake"
      elif mag >= 4.0:
        description += " - This is a moderate earthquake"

      severity = "high" if mag >= 6.0 else "medium" if mag >= 4.0 else "low"

      earthquake = Earthquake(
        place=location_name,
        magnitude=mag,
        coordinates=[lon, lat],
        time=props.get("time"),
        description=description,
        severity=severity
      )
      return earthquake
    except Exception as e:
      logger.error(f"Error parsing earthquake data: {e}")
      return None

  async def _reverse_geocode(self, lat: float, lon: float) -> str:
    try:
      location = self.geolocator.reverse(f"{lat}, {lon}", timeout=10)
      if location:
        return location.address
    except Exception as e:
      logger.error(f"Geocoding error: {e}")
    
    return f"Location ({lat}, {lon})"
