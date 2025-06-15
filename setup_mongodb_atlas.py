import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from config import Config
import logging

logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.INFO)

async def setup_mongodb_atlas():
  client = AsyncIOMotorClient(Config.MONGODB_URL)
  db = client[Config.MONGODB_DATABASE]
  
  # Create time series collection for disasters
  try:
    await db.create_collection(
      "disasters",
      timeseries={
        "timeField": "timestamp",
        "metaField": "metadata",
        "granularity": "minutes"
      }
    )
    logger.info("Created disasters time series collection")
  except Exception as e:
    logger.error(f"Disasters collection might already exist: {e}")

  # Create shelters collection
  try:
    shelters_collection = db["shelters"]
    
    # Create geospatial index
    await shelters_collection.create_index([("locations", "2dsphere")])
    logger.info("Created geospatial index for shelters")
  except Exception as e:
    logger.error(f"Error setting up shelters collection: {e}")

if __name__ == "__main__":
  asyncio.run(setup_mongodb_atlas())