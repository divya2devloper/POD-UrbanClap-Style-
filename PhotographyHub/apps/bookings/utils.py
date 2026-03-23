from math import atan2, cos, radians, sin, sqrt

from geopy.geocoders import Nominatim

AHMEDABAD_GANDHINAGAR_AREAS = {
    "Satellite": (23.0216, 72.5316),
    "Vastrapur": (23.0395, 72.5260),
    "Gota": (23.0964, 72.5417),
    "Sargasan": (23.1928, 72.6280),
    "Bopal": (23.0351, 72.4630),
    "Prahlad Nagar": (23.0120, 72.5108),
    "Navrangpura": (23.0330, 72.5600),
    "Chandkheda": (23.1124, 72.5897),
    "Naranpura": (23.0589, 72.5531),
    "Motera": (23.0927, 72.5970),
}


def area_to_coordinates(area_name: str):
    return AHMEDABAD_GANDHINAGAR_AREAS.get((area_name or "").strip())


def geocode_ahmedabad_address(address: str):
    """
    Geocode only Ahmedabad/Gandhinagar addresses for now.
    This can be extended to other cities in future iterations.
    """
    normalized = (address or "").strip()
    if not normalized:
        return None
    known_area = area_to_coordinates(normalized)
    if known_area:
        return known_area
    geolocator = Nominatim(user_agent="PhotographyHub")
    location = geolocator.geocode(normalized, country_codes="in")
    if not location:
        return None
    if "ahmedabad" not in location.address.lower() and "gandhinagar" not in location.address.lower():
        return None
    return (location.latitude, location.longitude)


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    earth_radius_km = 6371.0
    d_lat = radians(lat2 - lat1)
    d_lon = radians(lon2 - lon1)
    lat1_rad = radians(lat1)
    lat2_rad = radians(lat2)

    a = sin(d_lat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(d_lon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return earth_radius_km * c


import qrcode
import io
import base64
from django.core.signing import Signer
from django.urls import reverse
from django.conf import settings

signer = Signer()

def generate_signed_qr_base64(booking_id, action_type="arrival"):
    """
    Generate a QR code as a base64 string for a signed URL.
    action_type: "arrival" or "completion"
    """
    path = reverse(f"{action_type}_qr_scan", kwargs={"booking_id": booking_id})
    signed_value = signer.sign(f"{booking_id}:{action_type}")
    
    # Base URL should be the actual domain in production
    domain = getattr(settings, "SITE_DOMAIN", "http://localhost:8000")
    full_url = f"{domain}{path}?token={signed_value}"
    
    # Generate QR Code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(full_url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()
