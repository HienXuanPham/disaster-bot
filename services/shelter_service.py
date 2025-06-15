import overpy
from typing import List, Dict
from models.shelter import Shelter
import logging

logger = logging.getLogger(__name__)

class ShelterService:
  def __init__(self):
    self.overpass_api = overpy.Overpass()
    self.shelters_data: List[Shelter] = []

  async def extract_shelters_from_osm(self, bbox: str) -> List[Shelter]:
    query = f"""
      [out:json][timeout:25];
      (
        node["amenity"~"^(community_centre|social_facility|public_building)$"]({bbox});
        node["building"~"^(community_centre|civic|public)$"]({bbox});
        node["emergency"="assembly_point"]({bbox});
        node["leisure"="community_centre"]({bbox});
        way["amenity"~"^(community_centre|social_facility|public_building)$"]({bbox});
        way["building"~"^(community_centre|civic|public)$"]({bbox});
        way["emergency"="assembly_point"]({bbox});
        way["leisure"="community_centre"]({bbox});
      );
      out center meta;
    """
    try:
      result = self.overpass_api.query(query)
      shelters = []

      for element in result.nodes + result.ways:
        shelter_data = self._parse_osm_element(element)
        if shelter_data:
          shelters.append(shelter_data)

      self.shelters_data = shelters

      logger.info(f"Extracted {len(shelters)} potential shelters from OSM")
      return shelters
    except Exception as e:
      logger.error(f"Error querying Overpass API: {e}")
      return []
  
  def _parse_osm_element(self, element) -> Dict[str, any]:
    tags = element.tags or {}

    if hasattr(element, "lat") and hasattr(element, "lon"):
      lat, lon = float(element.lat), float(element.lon)
    elif hasattr(element, "center_lat") and hasattr(element, "center_lon"):
      lat, lon = float(element.center_lat), float(element.center_lon)
    else:
      return None
    
    shelter_type = self._determine_shelter_type(tags)
    if not shelter_type:
      return None

    name = tags.get("name", "Unknown")
    address = self._build_address(tags)
    description = self._build_description(name, tags, shelter_type)

    shelter = Shelter.from_coordinates(
        lat=lat,
        lon=lon,
        id=str(element.id),
        name=name,
        address=address,
        shelter_type=shelter_type,
        capacity=self._extract_capacity(tags),
        amenities=self._extract_amenities(tags),
        contact_info=self._extract_contact(tags),
        description=description,
        embedding=None
    )

    return shelter
  
  def _determine_shelter_type(self, tags: Dict[str, str]) -> str:
    emergency = tags.get("emergency", "")
    amenity = tags.get("amenity", "")
    building = tags.get("building", "")

    if emergency == "assembly_point" or building == "emergency_shelter":
      return "emergency"
    elif amenity in ["community_center", "social_facility"]:
      return "temporary"
    elif building in ["civic", "public"]:
      return "long-term"
    
    return "temporary"
  
  def _build_address(self, tags: Dict[str, str]) -> str:
    address = []

    if "addr:housenumber" in tags and "addr:street" in tags:
      address.append(f"{tags['addr:housenumber']} {tags['addr:street']}")
    elif "addr:street" in tags:
      address.append(tags["addr:street"])

    if "addr:city" in tags:
      address.append(tags["addr:city"])
    if "addr:state" in tags:
      address.append(tags["addr:state"])
    if "addr:postcode" in tags:
      address.append(tags["addr:postcode"])

    return ", ".join(address) if address else None
  
  def _build_description(self, name: str, tags: Dict[str, str], shelter_type: str) -> str:
    description = [f"{name} is a {shelter_type} shelter"]

    if tags.get("amenity"):
      description.append(f"classified as {tags['amenity']}")
    if tags.get("description"):
      description.append(tags["description"])
    if tags.get("opening_hours"):
      description.append(f"Open {tags['opening_hours']}")
    
    return ". ".join(description)

  def _extract_capacity(self, tags: Dict[str, str]) -> int:
      capacity_keys = ['capacity', 'beds', 'seats']
      for key in capacity_keys:
          if key in tags:
              try:
                capacity_str = tags[key].split()[0].split('-')[0]
                return int(capacity_str)
              except ValueError:
                continue
      return None
  
  def _extract_amenities(self, tags: Dict[str, str]) -> List[str]:
      amenities = []
      
      amenity_mapping = {
          'wheelchair': 'wheelchair_accessible',
          'internet_access': 'internet',
          'toilets': 'restrooms',
          'drinking_water': 'water',
          'shower': 'showers'
      }
      
      for tag, amenity in amenity_mapping.items():
          if tags.get(tag) == 'yes':
              amenities.append(amenity)
      
      return amenities
  
  def _extract_contact(self, tags: Dict[str, str]) -> Dict[str, str]:
      contact = {}
      
      if 'phone' in tags:
          contact['phone'] = tags['phone']
      if 'website' in tags:
          contact['website'] = tags['website']
      if 'email' in tags:
          contact['email'] = tags['email']
      
      return contact if contact else None   
