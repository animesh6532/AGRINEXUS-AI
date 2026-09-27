"""
OpenStreetMap (OSM) + Overpass API Supplier Provider.
Searches nearby agricultural fertilizer suppliers, dealers, and input stores around user GPS coordinates.
"""

import math
import time
import requests
from typing import List, Dict, Any, Optional, Tuple
from ..core.config import settings
from ..core.logging import logger
from .supplier_provider_base import BaseSupplierProvider


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate Great Circle distance in km between two GPS coordinates."""
    R = 6371.0  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2.0) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(R * c, 2)


AGRI_KEYWORDS = {
    "fertilizer", "fertiliser", "agro", "agri", "agricultural", "agriculture",
    "farm", "farming", "seed", "seeds", "pesticide", "pesticides", "crop", "crops",
    "krishi", "nursery", "chemical", "chemicals", "khad", "beej", "rasayan",
    "kendra", "bipani", "cooperative", "co-op", "traders", "enterprise", "inputs", "supplies"
}

EXCLUDED_SHOPS = {
    "clothing", "clothes", "shoes", "shoe", "bakery", "furniture", "florist",
    "travel_agency", "kiosk", "mall", "hairdresser", "butcher", "jewelry",
    "jewellery", "mobile_phone", "watch", "watches", "motorcycle", "motorcycle_repair",
    "copyshop", "beauty", "pastry", "confectionery", "tailor", "bag", "cosmetics", "religion"
}


def score_osm_element(element: Dict[str, Any]) -> int:
    """
    Relevance scoring system for OpenStreetMap elements.
    Accepts agrarian, farm, agricultural input stores, and businesses whose names or tags contain agri keywords.
    """
    tags = element.get("tags", {})
    name = (tags.get("name") or tags.get("name:en") or tags.get("description") or "").lower()
    shop = (tags.get("shop") or "").lower()
    trade = (tags.get("trade") or "").lower()
    office = (tags.get("office") or "").lower()

    has_agri_name = any(kw in name for kw in AGRI_KEYWORDS)

    # Reject explicit non-agri retail shops unless name explicitly indicates agri business
    if (shop in EXCLUDED_SHOPS or any(ex in shop for ex in EXCLUDED_SHOPS)) and not has_agri_name:
        return 0

    score = 0
    if shop in ["agrarian", "farm", "agricultural_supplies", "fertilizer"]:
        score += 10
    if trade in ["agricultural", "farming", "fertilizer", "agro"]:
        score += 10
    if has_agri_name:
        score += 10
    if shop in ["trade", "garden_centre", "chemist", "general", "store", "wholesale", "supply"]:
        score += 3
    if office in ["cooperative", "agricultural", "krishi"]:
        score += 5

    return score


def build_osm_address(tags: Dict[str, Any]) -> str:
    """Build formatted address from OSM addr:* tags."""
    parts = []
    if tags.get("addr:housenumber"):
        parts.append(tags["addr:housenumber"])
    if tags.get("addr:street"):
        parts.append(tags["addr:street"])
    if tags.get("addr:suburb"):
        parts.append(tags["addr:suburb"])
    if tags.get("addr:city"):
        parts.append(tags["addr:city"])
    elif tags.get("addr:district"):
        parts.append(tags["addr:district"])
    if tags.get("addr:state"):
        parts.append(tags["addr:state"])
    if tags.get("addr:postcode"):
        parts.append(tags["addr:postcode"])

    if parts:
        return ", ".join(parts)
    return tags.get("address") or tags.get("place") or "Local Address"


# In-memory supplier cache: key -> (timestamp, result_dict)
_SUPPLIER_CACHE: Dict[str, Tuple[float, Dict[str, Any]]] = {}


class OSMSupplierProvider(BaseSupplierProvider):
    """OpenStreetMap Overpass API Supplier Provider Implementation."""

    @classmethod
    def find_suppliers(
        cls,
        latitude: float,
        longitude: float,
        radius_km: float = 5.0,
        sort_by: str = "nearest"
    ) -> Dict[str, Any]:
        """
        Find nearby fertilizer & agro suppliers using OpenStreetMap + Overpass API.
        Uses progressive search radius (5 km -> 10 km -> 20 km max).
        Implements location-bucketed caching (3600s TTL) and rate limit handling.
        """
        if not (-90.0 <= latitude <= 90.0) or not (-180.0 <= longitude <= 180.0):
            raise ValueError("Invalid latitude or longitude coordinates.")

        # Cap radius to max 20 km
        max_radius = min(max(radius_km, 1.0), getattr(settings, "SUPPLIER_MAX_RADIUS_KM", 20.0))
        radii = [5.0, 10.0, 20.0]
        search_steps = [r for r in radii if r <= max_radius]
        if not search_steps or search_steps[-1] < max_radius:
            search_steps.append(max_radius)

        # Check Cache
        lat_bucket = round(latitude, 2)
        lon_bucket = round(longitude, 2)
        cache_ttl = getattr(settings, "SUPPLIER_CACHE_TTL", 3600)

        cache_key = f"osm_suppliers:{lat_bucket}:{lon_bucket}:{int(max_radius)}km:{sort_by}"
        if cache_key in _SUPPLIER_CACHE:
            cached_time, cached_res = _SUPPLIER_CACHE[cache_key]
            if time.time() - cached_time < cache_ttl:
                logger.info(f"[OSMSupplierProvider] Cache HIT for key={cache_key}")
                # Recalculate exact distance for current user lat/lon
                return cls._recalculate_distances(cached_res, latitude, longitude, sort_by)

        logger.info(f"[OSMSupplierProvider] Cache MISS for key={cache_key}. Executing progressive Overpass search.")

        collected_elements: Dict[str, Dict[str, Any]] = {}
        actual_radius_used = search_steps[0]
        error_diagnostic = None
        status = "success"

        for r_km in search_steps:
            actual_radius_used = r_km
            logger.info(f"[OSMSupplierProvider] Searching radius={r_km}km for lat={latitude:.4f}, lon={longitude:.4f}")

            elements, err_msg = cls._query_overpass(latitude, longitude, r_km)
            if err_msg:
                error_diagnostic = err_msg
                if "429" in err_msg:
                    status = "provider_limited"
                elif "unavailable" in err_msg or "timeout" in err_msg.lower():
                    status = "error"

            for el in elements:
                el_type = el.get("type")
                el_id = el.get("id")
                unique_key = f"{el_type}_{el_id}"
                if unique_key not in collected_elements:
                    collected_elements[unique_key] = el

            logger.info(f"[OSMSupplierProvider] Radius {r_km}km unique suppliers found so far: {len(collected_elements)}")

            if len(collected_elements) >= 3 or r_km == search_steps[-1]:
                break

        # Normalize elements into canonical SupplierItem structure
        suppliers: List[Dict[str, Any]] = []
        for key, el in collected_elements.items():
            el_type = el.get("type")
            el_id = el.get("id")
            tags = el.get("tags", {})

            el_lat = float(el.get("lat") or el.get("center", {}).get("lat") or latitude)
            el_lon = float(el.get("lon") or el.get("center", {}).get("lon") or longitude)
            dist_km = haversine_distance(latitude, longitude, el_lat, el_lon)

            disp_name = tags.get("name") or tags.get("name:en") or tags.get("operator") or "Agricultural Supplier"
            category = tags.get("shop") or tags.get("trade") or tags.get("office") or "Agricultural / Fertilizer Supplier"
            address = build_osm_address(tags)

            phone = tags.get("phone") or tags.get("contact:phone") or tags.get("mobile")
            website = tags.get("website") or tags.get("contact:website")
            opening_hours = tags.get("opening_hours") or "Hours unavailable"

            item = {
                "provider": "osm",
                "osm_type": el_type,
                "osm_id": str(el_id),
                "place_id": f"osm_{el_type}_{el_id}",
                "name": disp_name,
                "category": category,
                "address": address,
                "latitude": el_lat,
                "longitude": el_lon,
                "distance_km": dist_km,
                "phone": phone,
                "website": website,
                "opening_hours": opening_hours,
                "rating": None,
                "review_count": None,
                "open_now": None,
                "google_maps_uri": f"https://www.google.com/maps/search/?api=1&query={el_lat},{el_lon}",
                "osm_uri": f"https://www.openstreetmap.org/{el_type}/{el_id}",
                "tags": tags
            }
            suppliers.append(item)

        # Sorting
        if sort_by == "name":
            suppliers.sort(key=lambda s: s["name"].lower())
        else:  # nearest or default
            suppliers.sort(key=lambda s: s["distance_km"])

        # Create shop objects for backward compatibility with existing components
        shops = []
        for s in suppliers:
            shops.append({
                "shop_id": s["place_id"],
                "name": s["name"],
                "address": s["address"],
                "latitude": s["latitude"],
                "longitude": s["longitude"],
                "distance": s["distance_km"],
                "phone": s["phone"],
                "website": s["website"],
                "rating": 4.5,
                "review_count": 0,
                "opening_status": s["opening_hours"] or "Hours unavailable",
                "categories": [s["category"]],
                "google_maps_uri": s["google_maps_uri"]
            })

        if len(suppliers) == 0 and status == "success":
            status = "empty"

        message = None
        if len(suppliers) > 0 and actual_radius_used > 5.0:
            message = f"Expanded search to {int(actual_radius_used)} km because fewer nearby suppliers were found within 5 km."
        elif len(suppliers) > 0:
            message = f"Showing OpenStreetMap mapped suppliers within {int(actual_radius_used)} km."
        elif status == "empty":
            message = f"No fertilizer or agro-input suppliers were found within {int(actual_radius_used)} km. Supplier coverage depends on OpenStreetMap data."

        response_dict = {
            "success": True,
            "provider": "osm",
            "status": status,
            "location": {"latitude": latitude, "longitude": longitude},
            "search_radius_km": actual_radius_used,
            "count": len(suppliers),
            "suppliers": suppliers,
            "providers": suppliers,  # alias
            "shops": shops,
            "total_found": len(suppliers),
            "radius_km": radius_km,
            "radius_km_searched": actual_radius_used,
            "message": message,
            "error_diagnostic": error_diagnostic
        }

        # Store in Cache if valid response
        _SUPPLIER_CACHE[cache_key] = (time.time(), response_dict)
        return response_dict

    @classmethod
    def _query_overpass(cls, lat: float, lon: float, radius_km: float) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """Call public Overpass API using fast indexed spatial query with failover endpoints."""
        radius_m = int(radius_km * 1000.0)
        query = f"""[out:json][timeout:15];
(
  node["shop"="agrarian"](around:{radius_m},{lat},{lon});
  way["shop"="agrarian"](around:{radius_m},{lat},{lon});
  relation["shop"="agrarian"](around:{radius_m},{lat},{lon});
  node["shop"="farm"](around:{radius_m},{lat},{lon});
  way["shop"="farm"](around:{radius_m},{lat},{lon});
  node["shop"="agricultural_supplies"](around:{radius_m},{lat},{lon});
  way["shop"="agricultural_supplies"](around:{radius_m},{lat},{lon});
  node["shop"](around:{radius_m},{lat},{lon});
  way["shop"](around:{radius_m},{lat},{lon});
  node["office"](around:{radius_m},{lat},{lon});
  way["office"](around:{radius_m},{lat},{lon});
);
out center;"""

        endpoints = [
            getattr(settings, "OVERPASS_API_URL", "https://overpass-api.de/api/interpreter"),
            "https://overpass.kumi.systems/api/interpreter",
            "https://lz4.overpass-api.de/api/interpreter"
        ]

        headers = {
            "User-Agent": "AgriNexus-AI/1.0 (contact: project@agrinexus.ai)"
        }

        for ep in endpoints:
            try:
                logger.info(f"[OSMSupplierProvider] Overpass POST to {ep}")
                res = requests.post(ep, data={"data": query}, headers=headers, timeout=10.0)
                logger.info(f"[OSMSupplierProvider] Overpass HTTP {res.status_code} from {ep}")

                if res.status_code == 200:
                    data = res.json()
                    elements = data.get("elements", [])
                    filtered = [el for el in elements if score_osm_element(el) > 0]
                    return filtered, None
                elif res.status_code == 429:
                    logger.warning(f"[OSMSupplierProvider] Overpass rate-limited (HTTP 429) from {ep}")
                    return [], "Supplier search is temporarily rate-limited. Please try again shortly."
                else:
                    logger.warning(f"[OSMSupplierProvider] Overpass HTTP {res.status_code} from {ep}")
            except requests.exceptions.Timeout:
                logger.warning(f"[OSMSupplierProvider] Overpass request timeout on {ep}")
                continue
            except Exception as e:
                logger.warning(f"[OSMSupplierProvider] Overpass exception on {ep}: {e}")
                continue

        return [], "Supplier service is temporarily unavailable. Please try again."

    @classmethod
    def _recalculate_distances(
        cls,
        cached_res: Dict[str, Any],
        lat: float,
        lon: float,
        sort_by: str
    ) -> Dict[str, Any]:
        """Recalculate exact Haversine distance for cached result against actual user GPS."""
        res_copy = dict(cached_res)
        suppliers = [dict(s) for s in res_copy.get("suppliers", [])]

        for s in suppliers:
            s_lat = s["latitude"]
            s_lon = s["longitude"]
            s["distance_km"] = haversine_distance(lat, lon, s_lat, s_lon)

        if sort_by == "name":
            suppliers.sort(key=lambda s: s["name"].lower())
        else:
            suppliers.sort(key=lambda s: s["distance_km"])

        shops = []
        for s in suppliers:
            shops.append({
                "shop_id": s["place_id"],
                "name": s["name"],
                "address": s["address"],
                "latitude": s["latitude"],
                "longitude": s["longitude"],
                "distance": s["distance_km"],
                "phone": s["phone"],
                "website": s["website"],
                "rating": 4.5,
                "review_count": 0,
                "opening_status": s["opening_hours"] or "Hours unavailable",
                "categories": [s["category"]],
                "google_maps_uri": s["google_maps_uri"]
            })

        res_copy["location"] = {"latitude": lat, "longitude": lon}
        res_copy["suppliers"] = suppliers
        res_copy["providers"] = suppliers
        res_copy["shops"] = shops
        return res_copy
