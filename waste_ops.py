from math import asin, cos, radians, sin, sqrt
from typing import Iterable, Mapping


MATERIAL_RULES = {
    "Hazardous": ("battery", "batteries", "paint", "chemical", "pesticide", "motor oil", "medicine", "medication", "bulb", "fluorescent"),
    "Electronic": ("phone", "laptop", "computer", "charger", "cable", "tablet", "keyboard", "electronics", "e-waste"),
    "Organic": ("food", "fruit", "vegetable", "coffee grounds", "tea leaves", "yard waste", "leaves", "garden waste", "compost"),
    "Recyclable": ("paper", "cardboard", "newspaper", "glass", "bottle", "can", "aluminum", "aluminium", "plastic", "carton", "jar"),
    "General waste": ("tissue", "napkin", "diaper", "ceramic", "styrofoam", "polystyrene"),
}


def classify_material(item: str) -> str | None:
    """Return a best-effort sorting category for a common waste item."""
    normalized = " ".join(item.casefold().split())
    if not normalized:
        return None
    for category, keywords in MATERIAL_RULES.items():
        if any(keyword in normalized for keyword in keywords):
            return category
    return None


def priority_score(fill_percent: float, days_since_collection: float) -> float:
    """Score collection urgency from 0 to 100 using fullness and time."""
    fill_component = min(max(fill_percent, 0), 100) * 0.75
    time_component = min(max(days_since_collection, 0) / 7, 1) * 25
    return round(min(fill_component + time_component, 100), 1)


def priority_label(score: float) -> str:
    if score >= 75:
        return "Urgent"
    if score >= 45:
        return "Soon"
    return "On track"


def _distance_km(first: Mapping, second: Mapping) -> float:
    latitude_one, latitude_two = radians(first["lat"]), radians(second["lat"])
    latitude_delta = latitude_two - latitude_one
    longitude_delta = radians(second["lon"] - first["lon"])
    haversine = sin(latitude_delta / 2) ** 2 + cos(latitude_one) * cos(latitude_two) * sin(longitude_delta / 2) ** 2
    return 6371 * 2 * asin(sqrt(haversine))


def order_stops_nearest_neighbor(stops: Iterable[Mapping], start: Mapping) -> list[Mapping]:
    """Order collection stops by repeatedly choosing the nearest remaining stop."""
    remaining = list(stops)
    ordered = []
    current = start
    while remaining:
        nearest = min(remaining, key=lambda stop: _distance_km(current, stop))
        ordered.append(nearest)
        remaining.remove(nearest)
        current = nearest
    return ordered
