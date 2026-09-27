"""
Geospatial calculation utilities for field boundary polygons, area calculation,
perimeter estimation, and centroid resolution.

Uses standard WGS84 geodesic algorithms to accurately compute total area in square meters.
"""

import math
from typing import List, Tuple, Dict, Any, Optional

EARTH_RADIUS_M = 6378137.0  # WGS84 ellipsoid semi-major axis in meters


def calculate_polygon_area_m2(coordinates: List[List[float]]) -> float:
    """
    Calculate the geodesic surface area of a polygon on Earth in square meters.
    Coordinates format: [[lng, lat], [lng, lat], ...]
    Uses the spherical equal-area formula (Gauss-Bonnet / spherical projection).
    """
    if not coordinates or len(coordinates) < 3:
        return 0.0

    # Ensure coordinates form a closed ring
    ring = list(coordinates)
    if ring[0] != ring[-1]:
        ring.append(ring[0])

    if len(ring) < 4:
        return 0.0

    total = 0.0
    num_points = len(ring)

    for i in range(num_points - 1):
        p1 = ring[i]
        p2 = ring[i + 1]

        lon1, lat1 = math.radians(p1[0]), math.radians(p1[1])
        lon2, lat2 = math.radians(p2[0]), math.radians(p2[1])

        total += (lon2 - lon1) * (2 + math.sin(lat1) + math.sin(lat2))

    area = abs(total * EARTH_RADIUS_M * EARTH_RADIUS_M / 2.0)
    return round(area, 2)


def calculate_polygon_perimeter_m(coordinates: List[List[float]]) -> float:
    """
    Calculate the total perimeter of a polygon in meters using Haversine formula.
    Coordinates format: [[lng, lat], [lng, lat], ...]
    """
    if not coordinates or len(coordinates) < 2:
        return 0.0

    ring = list(coordinates)
    if ring[0] != ring[-1]:
        ring.append(ring[0])

    perimeter = 0.0
    for i in range(len(ring) - 1):
        p1 = ring[i]
        p2 = ring[i + 1]
        perimeter += haversine_distance_m(p1[1], p1[0], p2[1], p2[0])

    return round(perimeter, 2)


def haversine_distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate Haversine distance between two lat/lng coordinates in meters."""
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2.0) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return EARTH_RADIUS_M * c


def calculate_polygon_centroid(coordinates: List[List[float]]) -> Tuple[float, float]:
    """
    Calculate centroid (center of mass) [latitude, longitude] of a polygon ring.
    Coordinates format: [[lng, lat], [lng, lat], ...]
    """
    if not coordinates:
        return 0.0, 0.0

    ring = [c for c in coordinates if len(c) >= 2]
    if not ring:
        return 0.0, 0.0

    # Simple mean of vertices for quick centroid calculation
    avg_lng = sum(pt[0] for pt in ring) / len(ring)
    avg_lat = sum(pt[1] for pt in ring) / len(ring)

    return round(avg_lat, 6), round(avg_lng, 6)


def convert_m2_to_units(area_m2: float) -> Dict[str, float]:
    """Convert square meters to hectare, acre, bigha, and sqm."""
    if not area_m2 or area_m2 < 0:
        return {"acre": 0.0, "hectare": 0.0, "bigha": 0.0, "m2": 0.0}

    return {
        "acre": round(area_m2 / 4046.8564224, 2),
        "hectare": round(area_m2 / 10000.0, 2),
        "bigha": round(area_m2 / 1337.8, 2),
        "m2": round(area_m2, 2),
    }
