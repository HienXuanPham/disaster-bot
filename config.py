import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    MONGODB_URL = os.getenv("MONGODB_URL")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    
    # Collections
    SHELTERS_COLLECTION = "shelters"
    EARTHQUAKES_COLLECTION = "earthquakes"
