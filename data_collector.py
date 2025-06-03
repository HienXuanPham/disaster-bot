import aiohttp
from database import db

class EarthquakeCollector:
  def __init__(self):
    self.usgs_url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson"

  async def fetch_and_store_earthquakes(self):
    try:
      print("Fetching earthquake data from USGS...")

      async with aiohttp.ClientSession() as session:
        async with session.get(self.usgs_url) as response:
          if response.status == 200:
            data = await response.json()

            earthquake_count = 0
            for feature in data.get("features", []):
              props = feature.get("properties", {})
              geom = feature.get("geometry", {})

              earthquake_data = {
                "place": props.get("place", "Unknown"),
                "magnitude": props.get("mag", 0),
                "time": props.get("time"),
                "coordinates": geom.get("coordinates", [0, 0])
              }

              result = await db.store_earthquake(earthquake_data)
              if result:
                earthquake_count += 1
            print(f"Stored {earthquake_count} new earthquakes")
            return earthquake_count
          else:
            print(f"Failed to fetch data: {response.status}")
            return 0
    except Exception as e:
      print(f"Error fetching earthquakes: {e}")
      return 0

collector = EarthquakeCollector()