from datetime import datetime, timezone
import os
from typing import Any, Dict, Optional
from fastapi import FastAPI, HTTPException, Request
from contextlib import asynccontextmanager
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from pydantic import BaseModel
import uvicorn
from mongo_database import Database
from data_fetcher import DataFetcher
from services.ai_service import AIService
import logging

logger = logging.getLogger(__name__)

templates = Jinja2Templates(directory="templates")
database = Database()
data_fetcher = DataFetcher()
ai_service = AIService()

class QueryRequest(BaseModel):
  question: str
  latitude: Optional[float] = None
  longitude: Optional[float] = None

class QueryResponse(BaseModel):
  answer: str
  context: Dict[str, Any]
  timestamp: datetime

scheduler = AsyncIOScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
  logger.info("Starting Disaster Bot...")
  await database.connect_to_mongo()

  # logger.info("Fetching initial earthquake data...")
  # earthquakes = await data_fetcher.fetch_earthquakes()

  # if earthquakes:
  #   await database.insert_disaster_data(earthquakes)
  #   logger.info(f"Inserted {len(earthquakes)} earthquakes")

  # scheduler.add_job(
  #   data_fetcher.fetch_earthquakes,
  #   trigger=IntervalTrigger(days=1),
  #   id="earthquake_collector",
  #   name="Collect earthquake data everyday",
  #   replace_existing=True
  # )

  scheduler.start()
  logger.info("Automatic data collection started")
  logger.info("System ready!")

  yield

  logger.info("Shutting down...")
  scheduler.shutdown()
  logger.info("System shutdown complete")

app = FastAPI(lifespan=lifespan)

app.mount("/style", StaticFiles(directory="style"), name="style")

app.mount("/script", StaticFiles(directory="script"), name="script")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
  return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/query", response_model=QueryResponse)
async def query_bot(request:QueryRequest):
  print("Incoming request:", request)
  try:
    recent_disasters = await database.get_recent_disasters(hours=24)

    nearby_shelters = []
    if request.latitude and request.longitude:
      nearby_shelters = await database.find_shelters_near_location(request.latitude, request.longitude, radius_km=50)
    
    if not nearby_shelters:
      query_embedding = await ai_service.generate_embeddings([request.question])
      print(f"query_embedding: {query_embedding}")
      if query_embedding:
        nearby_shelters = await database.vector_search_shelters(query_embedding[0], limit=10)
    print(f"Nearby shelters: {nearby_shelters}")

    context = {
      "recent_disasters": recent_disasters,
      "nearby_shelters": nearby_shelters,
      "query_location":{
        "latitude": request.latitude,
        "longitude": request.longitude
      } if request.latitude and request.longitude else None
    }

    answer = ai_service.query_gemini(request.question, context)

    return QueryResponse(
      answer=answer,
      context=context,
      timestamp=datetime.now(timezone.utc)
    )
  except Exception as e:
    logger.error("Error processing query", exc_info=True)
    raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/disasters")
async def get_recent_disasters():
  disasters = await database.get_recent_disasters(hours=24)
  return {"disasters": disasters, "count": len(disasters)}

@app.get("/api/shelters")
async def get_nearby_shelters(lat: float, lon: float, radius: float = 50):
  shelters = await database.find_shelters_near_location(lat, lon, radius)
  return {"shelters": shelters, "count": len(shelters)}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
