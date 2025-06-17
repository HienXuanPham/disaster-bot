# Disaster Bot

A real-time disaster response system using FastAPI, MongoDB Atlas, and Google AI.

## Features

- Real-time earthquake data from USGS
- Emergency shelter information from OpenStreetMap
- Vector search for relevant shelters
- Natural language Q&A with Gemini AI
- Interactive web interface with live map
- Time series data storage for disasters

## Setup Instructions

### 1. Prerequisites

- Python 3.10+
- MongoDB Atlas account
- Google Cloud Project with Vertex AI enabled
- Gemini API key

### 2. Environment Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd disaster-bot

# Create virtual environment
python -m venv venv

# On Mac:
source venv/bin/activate

# On Windows:
. venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

```bash
# Create .env with your credentials
MONGODB_URL=mongodb+srv://<username>:<password>@cluster.mongodb.net
GEMINI_API_KEY=your-gemini-api-key
GOOGLE_CLOUD_PROJECT=your-project-id
MONGODB_DATABASE="disaster_bot"
```

### 4. MongoDB Atlas Setup

1. Create a MongoDB Atlas cluster
2. Create a database called "disaster_bot"
3. Set up collections using the setup script:

```bash
python setup_mongodb_atlas.py
```

4. Create a vector search index in Atlas UI:
   - Go to Atlas → Search → Create Vector Search Index
   - Choose JSON Editor
   - Fill out the configuration:
```bash
{
  "fields": [
    {
      "type": "vector",
      "path": "embedding",
      "numDimensions": 768,
      "similarity": "cosine"
    }
  ]
}
```

5. Pre-process shelters data into MongoDB:
```bash
python fetch_shelters_to_db.py
```

### 5. Google Cloud Setup

1. Create a Google Cloud Project
2. Enable Vertex AI API
3. Create a service account and download JSON key
4. Set Google credentials in .env

### 6. Run the Application

```bash
# Development
uvicorn main:app --reload

```

The application will be available at http://localhost:8000

### 7. Deployment
#### Using the Cloud Console:
1. Go to: https://console.cloud.google.com/run

2. Click **Create Service**

3. Select:

    - Source: "Deploy from source"
    
    - Repository: Connect your GitHub repo (authorize if needed)
    
    - Branch: main
    
    - Build config: Dockerfile

4. Set the region (e.g., us-central1)

5. Allow unauthenticated access (so the public can access your API/UI)

6. Click **Deploy**

**NOTE**: If you're getting an SSL handshake error, you should check Network Access in Atlas. Go to `MongoDB Atlas > Network Access > IP Access List`, modify the IP address to `0.0.0.0/0`
