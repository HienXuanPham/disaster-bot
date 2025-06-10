import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from config import Config
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.INFO)

async def setup_mongodb_atlas():
  """Setup MongoDB Atlas collections and indexes"""
  
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
    await shelters_collection.create_index([("location", "2dsphere")])
    logger.info("Created geospatial index for shelters")
    
    # Note: Vector search index must be created in MongoDB Atlas UI
    logger.info("Remember to create vector search index in MongoDB Atlas UI with:")
    logger.info({
      "fields": [
        {
          "type": "vector",
          "path": "embedding",
          "numDimensions": 768,
          "similarity": "cosine"
        }
      ]
    })
      
  except Exception as e:
    logger.error(f"Error setting up shelters collection: {e}")

if __name__ == "__main__":
  asyncio.run(setup_mongodb_atlas())