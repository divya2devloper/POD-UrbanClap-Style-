from math import atan2, cos, radians, sin, sqrt

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


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    earth_radius_km = 6371.0
    d_lat = radians(lat2 - lat1)
    d_lon = radians(lon2 - lon1)
    lat1_rad = radians(lat1)
    lat2_rad = radians(lat2)

    a = sin(d_lat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(d_lon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return earth_radius_km * c
