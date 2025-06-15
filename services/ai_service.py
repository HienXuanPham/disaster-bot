import re
import google.generativeai as genai
from typing import List, Dict, Any
from config import Config

class AIService:
  def __init__(self):
    # Initialize Gemini
    genai.configure(api_key=Config.GEMINI_API_KEY)
    self.gemini_model = genai.GenerativeModel("gemini-2.0-flash")
    self.embedding_model = genai.GenerativeModel("models/text-embedding-004")
  
  async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
    """Generate embeddings using Vertex AI"""
    embeddings = []

    for text in texts:
      try:
        result = genai.embed_content(
          model="models/text-embedding-004",
          content=text,
          task_type="retrieval_document"
        )
        embeddings.append(result["embedding"]) 
      except Exception as e:
        print(f"Error generating embeddings: {e}")
        embeddings.append([0.0] * 768)
    
    return embeddings

  def query_gemini(self, prompt: str, context: Dict[str, Any]) -> str:
    """Query Gemini AI for natural language responses"""
    try:
      full_prompt = self.build_prompt(prompt, context)
      
      response = self.gemini_model.generate_content(full_prompt)
      return self.clean_response(response.text)
    
    except Exception as e:
      print(f"Error querying Gemini: {e}")
      return "I'm sorry, I'm having trouble processing your request right now. Please try again later."
  
  def build_prompt(self, user_question: str, context: Dict[str, Any]) -> str:
    """Build comprehensive prompt for Gemini"""
    recent_disasters = context.get('recent_disasters', [])
    nearby_shelters = context.get('nearby_shelters', [])
    
    prompt = f"""You are a disaster response assistant helping people find safety and information during emergencies.

    RECENT DISASTERS:
    """
      
    if recent_disasters:
      for disaster in recent_disasters[:5]:  # Limit to recent 5
        prompt += f"- {disaster.get('type', 'Unknown').upper()}: {disaster.get('title', disaster.get('location_name', 'Unknown location'))}"
        if disaster.get('magnitude'):
          prompt += f" (Magnitude: {disaster['magnitude']})"
        prompt += f" at {disaster.get('timestamp', 'Unknown time')}\n"
    else:
      prompt += "No recent disasters in the area.\n"
      
    prompt += f"""
    NEARBY SHELTERS:
    """
      
    if nearby_shelters:
      for shelter in nearby_shelters[:10]:  # Limit to top 10
        prompt += f"- {shelter.get('name', 'Unnamed Shelter')}"
        if shelter.get('capacity'):
          prompt += f" (Capacity: {shelter['capacity']})"
        if shelter.get('amenities'):
          prompt += f" - Amenities: {', '.join(shelter['amenities'])}"
        if shelter.get('contact', {}).get('phone'):
          prompt += f" - Phone: {shelter['contact']['phone']}"
        prompt += "\n"
    else:
      prompt += "No shelters found in the immediate area.\n"
    
    prompt += f"""
      INSTRUCTIONS:
      - Provide accurate, helpful information about disaster response
      - If asked about shelters, refer to the nearby shelters list above
      - If asked about recent disasters, refer to the recent disasters list above
      - Always prioritize safety and official emergency services
      - Keep responses concise but informative
      - If you don't have specific information, direct them to call 911 or local emergency services

      SHELTER-SPECIFIC GUIDANCE:
      - When discussing shelters, always mention the shelter name, address, and key details (capacity, amenities, contact info)
      - If user asks about shelters in a specific city/area, focus only on shelters in that location
      - Provide practical information like:
        * What amenities are available (food, medical care, etc.)
        * Capacity and availability status
        * How to get there or contact information
        * Any special requirements or restrictions
      - If multiple shelters are available, help user choose based on their specific needs
      - If no shelters are found in the requested area, suggest:
        * Expanding search radius to nearby areas
        * Contacting local emergency services for the most current information
        * Checking with local Red Cross or emergency management offices
      - Always remind users to call ahead when possible to confirm availability and requirements
      - If shelters are at capacity or have special requirements, mention this clearly

      LOCATION-SPECIFIC RESPONSES:
      - When user mentions a specific city/area, acknowledge their location in your response
      - If shelter data is available for their city, be specific about which shelters serve that area
      - If user's location doesn't have shelters in our database, be honest about the limitation
      - Suggest nearby areas that might have available shelters
      - I shelters are Unknown, don't mention them
      - Always encourage contacting local authorities for the most up-to-date information

      SAFETY REMINDERS:
      - If you don't have specific information, direct them to call 911 or local emergency services
      - Emphasize the importance of following evacuation orders
      - Mention that official emergency services have the most current information
      - If situation seems urgent, prioritize immediate safety over shelter research

      USER QUESTION: {user_question}

      RESPONSE:"""
    
    return prompt

  def clean_response(self, text):
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # Bold
    text = re.sub(r'__(.*?)__', r'\1', text)       # Bold alt
    text = re.sub(r'\*(.*?)\*', r'\1', text)       # Italic
    text = re.sub(r'_(.*?)_', r'\1', text)         # Italic alt
    
    # Fix escaped underscores in compound words
    text = re.sub(r'(\w)\\?_(\w)', r'\1 \2', text)
    
    # Remove remaining markdown characters
    text = re.sub(r'[*_#\\]', '', text)
    
    # Remove any remaining single * or _
    text = re.sub(r'[*_]', '', text)
    
    return text