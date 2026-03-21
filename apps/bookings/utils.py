import math
import json
import os
from django.conf import settings


def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate the great-circle distance between two points on Earth using Haversine formula. Returns distance in km."""
    R = 6371.0  # Earth radius in km
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def get_area_coordinates():
    """Load Ahmedabad/Gandhinagar area coordinates from JSON file."""
    data_path = os.path.join(settings.BASE_DIR, 'data', 'ahmedabad_areas.json')
    with open(data_path, 'r') as f:
        return json.load(f)


def get_coordinates_for_area(area_name):
    """Return (latitude, longitude) for a given area name. Returns None if not found."""
    areas = get_area_coordinates()
    area_lower = area_name.lower().strip()
    for area in areas:
        if area['name'].lower() == area_lower:
            return area['latitude'], area['longitude']
    return None
