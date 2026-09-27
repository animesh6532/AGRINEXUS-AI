"""
Nearby Fertilizer & Agro-Input Shops Service.
Uses Google Places API (New) (searchNearby + searchText fallback)
to locate nearby agricultural fertilizer suppliers, dealers, and input stores around user GPS coordinates.
"""

import os
import math
import requests
from typing import List, Dict, Any, Optional, Tuple
from ..core.config import settings
from ..core.logging import logger


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


# Keywords indicating agricultural/fertilizer relevance
AGRI_KEYWORDS = {
    "fertilizer", "fertiliser", "agro", "agri", "agricultural", "agriculture",
    "farm", "farming", "seed", "seeds", "pesticide", "pesticides", "crop", "crops",
    "krishi", "nursery", "chemical", "chemicals", "khad", "beej", "rasayan",
    "kendra", "bipani", "cooperative", "co-op", "traders", "enterprise", "inputs", "supplies"
}

# Irrelevant place types to filter out unless name explicitly contains agri keywords
EXCLUDED_TYPES = {
    "clothing_store", "shoe_store", "restaurant", "hair_care", "bakery",
    "pharmacy", "atm", "bank", "lodging", "school", "hospital", "bar",
    "cafe", "beauty_salon", "dentist", "doctor", "gas_station", "gym"
}


def is_relevant_supplier(place: Dict[str, Any], query_used: Optional[str] = None) -> bool:
    """
    Evaluate whether a Google Place candidate is relevant for fertilizer/agro-input search.
    Non-restrictive: Accepts stores, wholesalers, establishments if name or types match agricultural terms,
    or if returned via targeted text search.
    """
    # If returned via targeted Text Search like 'fertilizer shop', it's already targeted
    if query_used and any(kw in query_used.lower() for kw in ["fertilizer", "agro", "agricultural"]):
        return True

    name = (place.get("displayName", {}).get("text") or "").lower()
    primary_type = (place.get("primaryType") or "").lower()
    types = [t.lower() for t in place.get("types", [])]

    has_agri_name = any(kw in name for kw in AGRI_KEYWORDS)

    # Reject explicit non-agri types if name has no agri keywords
    if any(ex in primary_type or any(ex in t for t in types) for ex in EXCLUDED_TYPES):
        if not has_agri_name:
            return False

    # Check if name, primary type, or any type contains agricultural keywords
    if has_agri_name:
        return True

    if any(kw in primary_type for kw in AGRI_KEYWORDS):
        return True

    if any(kw in t for t in types for kw in AGRI_KEYWORDS):
        return True

    # General stores, wholesalers, or establishments are accepted as potential suppliers
    generic_types = {"store", "wholesaler", "farm", "point_of_interest", "establishment"}
    if primary_type in generic_types or any(t in generic_types for t in types):
        return True

    return False


class NearbyShopsService:
    """Service to search nearby fertilizer suppliers, dealers, and input stores around user coordinates."""

    @classmethod
    def find_nearby_shops(
        cls,
        latitude: float,
        longitude: float,
        radius_km: float = 25.0,
        sort_by: str = "nearest"
    ) -> Dict[str, Any]:
        """
        Find nearby fertilizer suppliers using Google Places API (New).
        Uses exact user lat/lon and progressive radius search (5km -> 10km -> 20km -> 30km).
        Fallback to Google Places Text Search if Nearby Search yields insufficient results.
        """
        if not (-90.0 <= latitude <= 90.0) or not (-180.0 <= longitude <= 180.0):
            raise ValueError("Invalid latitude or longitude coordinates.")

        api_key = (
            getattr(settings, "GOOGLE_MAPS_API_KEY", None)
            or getattr(settings, "GOOGLE_PLACES_API_KEY", None)
            or os.getenv("GOOGLE_MAPS_API_KEY")
            or os.getenv("GOOGLE_PLACES_API_KEY")
        )

        error_diagnostic = None
        if not api_key:
            error_diagnostic = "Google Places API key is unconfigured on backend."
            logger.warning("[FertilizerShopSearch] Google Places API Key is not set in backend settings or environment.")
            return {
                "location": {"latitude": latitude, "longitude": longitude},
                "search_radius_km": radius_km,
                "count": 0,
                "providers": [],
                "shops": [],
                "total_found": 0,
                "radius_km": radius_km,
                "radius_km_searched": radius_km,
                "message": "Google Places API key is unconfigured on backend server.",
                "error_diagnostic": error_diagnostic
            }

        # Progressive radius sequence (up to max supported 30 km)
        max_radius = min(max(radius_km, 5.0), 30.0)
        radii = [5.0, 10.0, 20.0, 30.0]
        search_steps = [r for r in radii if r <= max_radius]
        if not search_steps or search_steps[-1] < max_radius:
            search_steps.append(max_radius)

        collected_places: Dict[str, Dict[str, Any]] = {}
        actual_radius_used = search_steps[0]

        for r_km in search_steps:
            actual_radius_used = r_km
            logger.info(f"[FertilizerShopSearch] Step: searching lat={latitude:.4f}, lon={longitude:.4f}, radius={r_km}km")

            # 1. Nearby Search (New)
            nearby_results, nearby_err = cls._query_google_places_nearby(latitude, longitude, r_km, api_key)
            if nearby_err and not error_diagnostic:
                error_diagnostic = nearby_err

            for p in nearby_results:
                p_id = p.get("id")
                if p_id and p_id not in collected_places:
                    collected_places[p_id] = p

            # 2. Text Search Fallback if under 3 results
            if len(collected_places) < 3:
                text_queries = [
                    "fertilizer shop",
                    "fertilizer supplier",
                    "agro input store",
                    "agricultural supplies"
                ]
                for query in text_queries:
                    if len(collected_places) >= 10:
                        break
                    text_results, text_err = cls._query_google_places_text_search(latitude, longitude, r_km, query, api_key)
                    if text_err and not error_diagnostic:
                        error_diagnostic = text_err
                    for p in text_results:
                        p_id = p.get("id")
                        if p_id and p_id not in collected_places:
                            collected_places[p_id] = p

            logger.info(f"[FertilizerShopSearch] Radius {r_km}km total unique providers found so far: {len(collected_places)}")

            if len(collected_places) >= 3 or r_km == search_steps[-1]:
                break

        # Process providers
        providers: List[Dict[str, Any]] = []
        for p_id, p in collected_places.items():
            loc = p.get("location", {})
            p_lat = loc.get("latitude", latitude)
            p_lon = loc.get("longitude", longitude)
            dist_km = haversine_distance(latitude, longitude, p_lat, p_lon)

            disp_name = p.get("displayName", {}).get("text") or "Agricultural Supplier"
            primary_type = p.get("primaryTypeDisplayName", {}).get("text") or p.get("primaryType") or "Fertilizer Supplier"
            opening_hours = p.get("regularOpeningHours", {})
            open_now = opening_hours.get("openNow") if "openNow" in opening_hours else None

            provider_item = {
                "place_id": p_id,
                "name": disp_name,
                "category": primary_type,
                "address": p.get("formattedAddress", "Local Address"),
                "latitude": p_lat,
                "longitude": p_lon,
                "distance_km": dist_km,
                "rating": float(p["rating"]) if p.get("rating") is not None else None,
                "review_count": int(p["userRatingCount"]) if p.get("userRatingCount") is not None else None,
                "open_now": open_now,
                "phone": p.get("nationalPhoneNumber"),
                "website": p.get("websiteUri"),
                "google_maps_uri": p.get("googleMapsUri") or f"https://www.google.com/maps/search/?api=1&query={p_lat},{p_lon}&query_place_id={p_id}",
                "types": p.get("types", [])
            }
            providers.append(provider_item)

        # Sorting
        if sort_by == "highest_rated":
            providers.sort(key=lambda item: (item["rating"] if item["rating"] is not None else -1.0, -item["distance_km"]), reverse=True)
        elif sort_by == "open_now":
            providers.sort(key=lambda item: (0 if item["open_now"] is True else (1 if item["open_now"] is False else 2), item["distance_km"]))
        else:  # nearest
            providers.sort(key=lambda item: item["distance_km"])

        # Create shop objects for backward compatibility
        shops = []
        for p in providers:
            open_status = "OPEN NOW" if p["open_now"] is True else ("CLOSED NOW" if p["open_now"] is False else "Hours unavailable")
            shops.append({
                "shop_id": p["place_id"],
                "name": p["name"],
                "address": p["address"],
                "latitude": p["latitude"],
                "longitude": p["longitude"],
                "distance": p["distance_km"],
                "phone": p["phone"],
                "website": p["website"],
                "rating": p["rating"] if p["rating"] is not None else 4.5,
                "review_count": p["review_count"] if p["review_count"] is not None else 0,
                "opening_status": open_status,
                "categories": p["types"] or [p["category"]],
                "google_maps_uri": p["google_maps_uri"]
            })

        msg = None
        if len(providers) > 0 and actual_radius_used > 5.0:
            msg = f"Expanded search to {int(actual_radius_used)} km because fewer nearby suppliers were found within 5 km."
        elif len(providers) > 0:
            msg = f"Showing suppliers within {int(actual_radius_used)} km."
        elif len(providers) == 0:
            msg = f"No fertilizer suppliers were found within {int(actual_radius_used)} km."

        return {
            "location": {"latitude": latitude, "longitude": longitude},
            "search_radius_km": actual_radius_used,
            "count": len(providers),
            "providers": providers,
            "shops": shops,
            "total_found": len(providers),
            "radius_km": radius_km,
            "radius_km_searched": actual_radius_used,
            "message": msg,
            "error_diagnostic": error_diagnostic
        }

    @classmethod
    def _query_google_places_nearby(
        cls, lat: float, lon: float, radius_km: float, api_key: str
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """Call Google Places API (New) searchNearby."""
        url = "https://places.googleapis.com/v1/places:searchNearby"
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": api_key,
            "X-Goog-FieldMask": "places.id,places.displayName,places.formattedAddress,places.location,places.primaryType,places.types,places.rating,places.userRatingCount,places.regularOpeningHours,places.nationalPhoneNumber,places.websiteUri,places.googleMapsUri,places.primaryTypeDisplayName"
        }
        payload = {
            "includedTypes": ["store", "wholesaler", "farm", "establishment", "point_of_interest"],
            "maxResultCount": 20,
            "locationRestriction": {
                "circle": {
                    "center": {"latitude": lat, "longitude": lon},
                    "radius": radius_km * 1000.0
                }
            }
        }

        try:
            logger.info(f"[FertilizerShopSearch] Google searchNearby request: lat={lat:.4f}, lon={lon:.4f}, radius={radius_km}km")
            res = requests.post(url, json=payload, headers=headers, timeout=5.0)
            logger.info(f"[FertilizerShopSearch] Google searchNearby HTTP status={res.status_code}")

            if res.status_code == 200:
                data = res.json()
                raw_places = data.get("places", [])
                logger.info(f"[FertilizerShopSearch] Google searchNearby raw count={len(raw_places)}")

                filtered = []
                for p in raw_places:
                    if is_relevant_supplier(p):
                        filtered.append(p)
                logger.info(f"[FertilizerShopSearch] Google searchNearby filtered count={len(filtered)}")
                return filtered, None
            else:
                err_text = res.text[:300]
                logger.warning(f"[FertilizerShopSearch] Google searchNearby error HTTP {res.status_code}: {err_text}")
                return [], f"Google Places API Nearby HTTP {res.status_code}: {err_text}"
        except Exception as e:
            logger.warning(f"[FertilizerShopSearch] Google searchNearby exception: {e}")
            return [], f"Google Places API connection exception: {str(e)}"

    @classmethod
    def _query_google_places_text_search(
        cls, lat: float, lon: float, radius_km: float, query: str, api_key: str
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """Call Google Places API (New) searchText."""
        url = "https://places.googleapis.com/v1/places:searchText"
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": api_key,
            "X-Goog-FieldMask": "places.id,places.displayName,places.formattedAddress,places.location,places.primaryType,places.types,places.rating,places.userRatingCount,places.regularOpeningHours,places.nationalPhoneNumber,places.websiteUri,places.googleMapsUri,places.primaryTypeDisplayName"
        }
        payload = {
            "textQuery": query,
            "maxResultCount": 20,
            "locationRestriction": {
                "circle": {
                    "center": {"latitude": lat, "longitude": lon},
                    "radius": radius_km * 1000.0
                }
            }
        }

        try:
            logger.info(f"[FertilizerShopSearch] Google searchText query='{query}' request: lat={lat:.4f}, lon={lon:.4f}, radius={radius_km}km")
            res = requests.post(url, json=payload, headers=headers, timeout=5.0)
            logger.info(f"[FertilizerShopSearch] Google searchText query='{query}' HTTP status={res.status_code}")

            if res.status_code == 200:
                data = res.json()
                raw_places = data.get("places", [])
                logger.info(f"[FertilizerShopSearch] Google searchText query='{query}' raw count={len(raw_places)}")

                filtered = []
                for p in raw_places:
                    if is_relevant_supplier(p, query_used=query):
                        filtered.append(p)
                logger.info(f"[FertilizerShopSearch] Google searchText query='{query}' filtered count={len(filtered)}")
                return filtered, None
            else:
                err_text = res.text[:300]
                logger.warning(f"[FertilizerShopSearch] Google searchText query='{query}' error HTTP {res.status_code}: {err_text}")
                return [], f"Google Places API Text HTTP {res.status_code}: {err_text}"
        except Exception as e:
            logger.warning(f"[FertilizerShopSearch] Google searchText exception: {e}")
            return [], f"Google Places API Text connection exception: {str(e)}"
