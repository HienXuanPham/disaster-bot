from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

class Database:
  def __init__(self):
    self.client = None
    self.db = None
    self.disasters = None

  async def connect(self):
    self.client = AsyncIOMotorClient(os.getenv("MONGODB_URL"))
    self.db = self.client.disaster_db
    self.disasters = self.db.disasters

    try:
      await self.disasters.create_index([
        ("place", "text"),
        ("description", "text")
      ])
      print("Database connected and indexed")
    except Exception as e:
      print(f"Index might already exist: {e}")
    
  async def store_earthquake(self, earthquake_data):
    mag = earthquake_data.get("magnitude", 0)
    place = earthquake_data.get("place", "Unknown location")

    description = f"Magnitude {mag} earthquake occurred in {place}"
    if mag >= 6.0:
      description += " - This is considered a strong earthquake"
    elif mag >= 4.0:
      description += " - This is a moderate earthquake"
    
    earthquake = {
      "place": place,
      "magnitude": mag,
      "coordinates": earthquake_data.get("coordinates", [0, 0]),
      "time": earthquake_data.get("time"),
      "description": description,
      "severity": "high" if mag >= 6.0 else "medium" if mag >= 4.0 else "low",
      "stored_at": datetime.now(),
      "source": "usgs"
    }

    existing = await self.disasters.find_one({
      "time": earthquake_data.get("time"),
      "place": place
    })

    if not existing:
      result = await self.disasters.insert_one(earthquake)
      print(f"Stored earthquake: {place} - Magnitude: {mag}")
      return result
    else:
      print(f"Earthquake data already exist: {place}")
      return None
    
  async def search_disasters(self, query_text, limit=5):
    results = []

    cursor = self.disasters.find(
      {"$text": {"$search": query_text}},
      {"score": {"$meta": "textScore"}}
    ).sort([("score", {"$meta": "textScore"})]).limit(limit)

    async for doc in cursor:
      doc["_id"] = str(doc["_id"])
      results.append(doc)
    
    return results

  async def get_recent_disasters(self, hours=24, limit=10):
    since = datetime.now() - timedelta(hours=hours)

    cursor = self.disasters.find(
      {"stored_at": {"$gte": since}}
    ).sort("stored_at", -1).limit(limit)

    results = []
    async for doc in cursor:
      doc["_id"] = str(doc["_id"])
      results.append(doc)

    return results

db = Database()