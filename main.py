from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
import google.generativeai as genai
from config import Config
from database import db
from data_collector import collector


templates = Jinja2Templates(directory="templates")
genai.configure(api_key=Config.GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")

scheduler = AsyncIOScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting Disaster Bot...")
    await db.connect()

    print("Fetching initial earthquake data...")
    await collector.fetch_and_store_earthquakes()

    scheduler.add_job(
        collector.fetch_and_store_earthquakes,
        trigger=IntervalTrigger(days=1),
        id="earthquake_collector",
        name="Collect earthquake data everyday",
        replace_existing=True
    )

    scheduler.start()
    print("Automatic data collection started")
    print("System ready!")

    yield

    print("Shutting down...")
    scheduler.shutdown()
    print("System shutdown complete")

app = FastAPI(lifespan=lifespan)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/earthquakes")
async def get_earthquakes():
    earthquakes = await db.get_recent_disasters(hours=24, limit=10)
    
    return {"earthquakes": earthquakes, "count": len(earthquakes)}

@app.post("/ask")
async def ask_ai(question: dict):
    user_question = question["question"]
    
    recent_disasters = await db.get_recent_disasters(hours=48, limit=10)

    search_results = await db.search_disasters(user_question, limit=5)

    prompt = f"""
        You are a disaster information assistant with access to real-time data.
        
        RECENT DISASTERS (last 48 hours):
        {recent_disasters}
        
        SEARCH RESULTS for "{user_question}":
        {search_results}
        
        USER QUESTION: {user_question}
        
        Please provide a helpful, accurate answer based on this real disaster data. 
        Include specific details like locations, magnitudes, and times when relevant.
        Focus on safety and practical information.
    """

    try:
        response = model.generate_content(prompt)
        return {
            "answer": response.text,
            "data_sources": f"{len(recent_disasters)} recent disasters, {len(search_results)} search matches"
        }
    except Exception as e:
        return {"answer": f"Sorry, I encountered an error: {str(e)}"}
    
@app.post("/search")
async def search_disaster(query: dict):
    search_term = query["search"]

    results = await db.search_disasters(search_term, limit=10)

    if results:
        prompt = f"""
            Here are disasters matching the search "{search_term}":
            
            {results}
            
            Please provide a clear, helpful summary of these disasters.
            Include key details like locations, magnitudes, and when they occurred.
        """
        
        try:
            ai_response = model.generate_content(prompt)
            return {
                "results": results,
                "summary": ai_response.text,
                "count": len(results)
            }
        except Exception as e:
            return {
                "results": results,
                "summary": f"Found {len(results)} disasters matching your search",
                "count": len(results)
            }
    else:
        return {
            "results": [],
            "summary": "No disasters found matching your search terms",
            "count": 0
        }

@app.get("/system-status")
async def system_status():
    recent_count = len(await db.get_recent_disasters(hours=12))
    total_count = len(await db.get_recent_disasters(hours=24))

    return {
        "status": "running",
        "recent_disasters_12h": recent_count,
        "total_disasters_day": total_count,
        "auto_collection": "active" if scheduler.running else "stopped"
    }
# Run with: uvicorn main:app --reload