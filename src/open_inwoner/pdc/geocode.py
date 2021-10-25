from typing import Optional

from django.conf import settings
from django.contrib.gis.geos import Point

from geopy.geocoders import Nominatim


def geocode_address(address: str) -> Optional[Point]:
    geolocator = Nominatim(
        user_agent=settings.GEOPY_APP, timeout=settings.GEOPY_TIMEOUT
    )
    location = geolocator.geocode(address)
    if not location:
        return None

    coordinates = (location.longitude, location.latitude)
    return Point(coordinates)
