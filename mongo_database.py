from motor.motor_asyncio import AsyncIOMotorClient
from config import Config
from typing import List, Dict, Any
from pydantic import BaseModel
import logging
from pymongo.errors import BulkWriteError

logger = logging.getLogger(__name__)

class Database:
  def __init__(self):
    self.client: AsyncIOMotorClient = None
    self.database = None

  async def connect_to_mongo(self):
    self.client = AsyncIOMotorClient(Config.MONGODB_URL)
    self.database = self.client[Config.MONGODB_DATABASE]

    try:
      await self.client.admin.command('ping')
      await self.setup_collections()
      logger.info("Successfully connected to MongoDB Atlas")
    except Exception as e:
      logger.error(f"Failed to connect to MongoDB: {e}")
      raise
  
  async def setup_collections(self):
    try:
      await self.database.create_collection(
        Config.DISASTERS_COLLECTION,
        timeseries={
          "timeField": "timestamp",
          "metaField": "metadata",
          "granularity": "minutes"
        }
      )
    except Exception as e:
      logger.error(f"Disasters collection might already exist: {e}")
  
  # TODO: Create vector search index for shelters in MongoDB Atlas

  async def insert_disaster_data(self, data: List[BaseModel]):
    if data:
      collection = self.database[Config.DISASTERS_COLLECTION]
    to_insert = []

    for item in data:
      exists = await collection.find_one({
        "timestamp": item.time,
        "place": item.place
      })
      if not exists:
        doc = item.model_dump()
        doc["timestamp"] = item.time
        to_insert.append(doc)

    if to_insert:
      await collection.insert_many(to_insert)
      print(f"{len(to_insert)} disasters inserted (after deduplication).")
    else:
      print("No new disaster data to insert.")
  
  async def insert_shelter_data(self, data: List[BaseModel]):
    if data:
      collection = self.database[Config.SHELTERS_COLLECTION]
    to_insert = []

    for item in data:
      exists = await collection.find_one({
        "coordinates": item.coordinates
      })
      if not exists:
        to_insert.append(item.model_dump())
      if to_insert:
        await collection.insert_many(to_insert)
        print(f"{len(to_insert)} disasters inserted (after deduplication).")
      else:
        print("No new disaster data to insert.")
      
  async def vector_search_shelters(self, query_embedding: List[float], limit: int = 10):
    collection = self.database[Config.SHELTERS_COLLECTION]
    
    pipeline = [
      {
        "$vectorSearch": {
          "index": Config.VECTOR_INDEX_NAME,
          "path": "embedding",
          "queryVector": query_embedding,
          "numCandidates": 100,
          "limit": limit
        }
      },
      {
        "$project": {
          "name": 1,
          "location": 1,
          "capacity": 1,
          "amenities": 1,
          "contact": 1,
          "score": {"$meta": "vectorSearchScore"}
        }
      }
    ]
    
    results = []
    async for doc in collection.aggregate(pipeline):
      doc["_id"] = str(doc["_id"]) # convert ObjectId to str
      results.append(doc)

    return results
  
  async def get_recent_disasters(self, hours: int = 24):
    from datetime import datetime, timedelta, timezone
    
    collection = self.database[Config.DISASTERS_COLLECTION]
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
    
    query = {"timestamp": {"$gte": cutoff_time}}
    results = []
    async for doc in collection.find(query).sort("timestamp", -1):
      doc["_id"] = str(doc["_id"])
      results.append(doc)

    return results
  
  async def find_shelters_near_location(self, lat: float, lon: float, radius_km: float = 50):
    collection = self.database[Config.SHELTERS_COLLECTION]
    
    query = {
      "locations": {
        "$geoWithin": {
          "$centerSphere": [[lon, lat], radius_km / 6378.1]
        }
      }
    }
    
    results = []
    async for doc in collection.find(query):
      doc["_id"] = str(doc["_id"])
      results.append(doc)

    return results 

