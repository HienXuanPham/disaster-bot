import asyncio
from typing import List
import logging
from data_fetcher import DataFetcher
from models.shelter import Shelter
from mongo_database import Database
from services.ai_service import AIService

logger = logging.getLogger(__name__)
database = Database()
data_fetcher = DataFetcher()
ai_service = AIService()

async def fetch_shelters_and_save_to_mongodb() -> List[Shelter]:
  bbox_by_cities = {
    "New York City": "40.4774,-74.2591,40.9176,-73.7004",
    "San Francisco": "37.6398,-123.1738,37.9298,-122.2818",
    "Los Angeles": "33.7037,-118.6682,34.3373,-118.1553",
    "Chicago": "41.6445,-87.9401,42.0230,-87.5237",
    "Miami": "25.7091,-80.4740,25.8557,-80.1391",
    "Las Vegas": "35.9580,-115.3470,36.4253,-114.9817",
    "Seattle": "47.4919,-122.4596,47.7341,-122.2244",
    "Denver": "39.6144,-105.1099,39.9142,-104.6003",
    "Washington, DC": "38.7916,-77.1198,38.9955,-76.9094",
    "Houston": "29.5370,-95.9093,30.1105,-95.0146",
    "Boston": "42.2279,-71.1912,42.3995,-70.9860"
  }

  await database.connect_to_mongo()

  for city, bbox in bbox_by_cities.items():
    try:
      logger.info(f"Fetching shelters for bbox: {bbox}")

      shelters_data = await data_fetcher.fetch_osm_shelters(bbox)
      
      print(f"{city}: Found {len(shelters_data)} shelters")

      if shelters_data:
        shelter_texts = [s.description for s in shelters_data]
        embeddings = await ai_service.generate_embeddings(shelter_texts)

        for shelter, embedding in zip(shelters_data, embeddings):
            shelter.embedding = embedding
        await database.insert_shelter_data(shelters_data)
    except Exception as e:
      logger.error(f"Error fetching OSM shelters: {e}")

    await asyncio.sleep(2)

if __name__ == "__main__":
  asyncio.run(fetch_shelters_and_save_to_mongodb())