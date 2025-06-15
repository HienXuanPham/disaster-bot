import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    MONGODB_URL = os.getenv("MONGODB_URL")
    MONGODB_DATABASE = os.getenv("MONGODB_DATABASE")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")
    
    # Collections
    SHELTERS_COLLECTION = "shelters"
    EARTHQUAKES_COLLECTION = "earthquakes"
    DISASTERS_COLLECTION = "disasters"
    VECTOR_INDEX_NAME = "shelter_vector_index"

    PORT = int(os.getenv("PORT", 8080))
