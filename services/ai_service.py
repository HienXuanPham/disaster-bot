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
      return response.text
    
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

      USER QUESTION: {user_question}

      RESPONSE:"""
    
    return prompt