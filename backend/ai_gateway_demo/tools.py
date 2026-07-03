"""
Tools the Concierge agent can call. Each is a THIN wrapper over an app capability
(here stubbed with deterministic data so the agent loop stays test-friendly).
In the real app these would call hybrid_search / geocoding / recommendations.

location-first: `locate` establishes the search area, then `search_properties`
only returns places inside that area.
"""
import math
from typing import Any

# stub catalog standing in for hybrid_search over the DB (young-renter listings)
_CATALOG: list[dict[str, Any]] = [
    {"id": 1, "title": "Sunny 1BR near campus", "lat": 40.444, "lng": -79.953, "price": 1200},
    {"id": 2, "title": "Quiet studio, Shadyside", "lat": 40.455, "lng": -79.933, "price": 1100},
    {"id": 3, "title": "3BR house, Oakland", "lat": 40.441, "lng": -79.957, "price": 2400},
    {"id": 4, "title": "Loft downtown", "lat": 40.441, "lng": -80.000, "price": 1800},
]


def locate(place: str) -> dict:
    """Resolve a place/area description to a center point + search radius (km).
    Stub geocoder; a real one calls a geocoding API or PostGIS."""
    known = {
        "cmu": (40.4433, -79.9436),
        "oakland": (40.4415, -79.9573),
        "shadyside": (40.4550, -79.9330),
        "downtown": (40.4410, -80.0000),
    }
    key = place.strip().lower()
    lat, lng = next((coord for name, coord in known.items() if name in key), (40.4433, -79.9436))
    return {"place": place, "lat": lat, "lng": lng, "radius_km": 3.0}


def _haversine_km(a_lat: float, a_lng: float, b_lat: float, b_lng: float) -> float:
    r = 6371.0
    dlat, dlng = math.radians(b_lat - a_lat), math.radians(b_lng - a_lng)
    h = math.sin(dlat / 2) ** 2 + math.cos(math.radians(a_lat)) * math.cos(math.radians(b_lat)) * math.sin(dlng / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def search_properties(lat: float, lng: float, radius_km: float, max_price: int | None = None) -> list[dict[str, Any]]:
    """Return properties within `radius_km` of (lat, lng), optionally under max_price, nearest first."""
    hits: list[dict[str, Any]] = []
    for p in _CATALOG:
        dist = _haversine_km(lat, lng, p["lat"], p["lng"])
        if dist <= radius_km and (max_price is None or p["price"] <= max_price):
            hits.append({**p, "distance_km": round(dist, 2)})
    hits.sort(key=lambda p: p["distance_km"])
    return hits


# registry: tool name -> callable + JSON schema advertised to the LLM
TOOLS: dict[str, dict[str, Any]] = {
    "locate": {
        "fn": locate,
        "schema": {
            "name": "locate",
            "description": "Resolve a place or area description to a center point and search radius.",
            "input_schema": {
                "type": "object",
                "properties": {"place": {"type": "string"}},
                "required": ["place"],
            },
        },
    },
    "search_properties": {
        "fn": search_properties,
        "schema": {
            "name": "search_properties",
            "description": "Find listings within a radius of a lat/lng, optionally under max_price.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "lat": {"type": "number"},
                    "lng": {"type": "number"},
                    "radius_km": {"type": "number"},
                    "max_price": {"type": "integer"},
                },
                "required": ["lat", "lng", "radius_km"],
            },
        },
    },
}
