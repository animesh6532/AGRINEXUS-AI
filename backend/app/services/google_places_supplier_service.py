"""
Google Places Supplier Provider Implementation.
Wraps NearbyShopsService for Google Places API (New).
"""

from typing import Dict, Any
from .supplier_provider_base import BaseSupplierProvider
from .nearby_shops_service import NearbyShopsService


class GooglePlacesSupplierProvider(BaseSupplierProvider):
    """Google Places API Supplier Provider Implementation."""

    @classmethod
    def find_suppliers(
        cls,
        latitude: float,
        longitude: float,
        radius_km: float = 5.0,
        sort_by: str = "nearest"
    ) -> Dict[str, Any]:
        """Find suppliers using Google Places API (New)."""
        res = NearbyShopsService.find_nearby_shops(
            latitude=latitude,
            longitude=longitude,
            radius_km=radius_km,
            sort_by=sort_by
        )
        res["provider"] = "google"
        res["status"] = "success" if res.get("count", 0) > 0 else ("empty" if not res.get("error_diagnostic") else "error")
        res["suppliers"] = res.get("providers", [])
        return res
