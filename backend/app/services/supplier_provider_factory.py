"""
Factory for instantiating the configured Supplier Discovery Provider.
Supports switching between 'osm' (OpenStreetMap + Overpass) and 'google' (Google Places API).
"""

from ..core.config import settings
from .supplier_provider_base import BaseSupplierProvider
from .osm_supplier_service import OSMSupplierProvider
from .google_places_supplier_service import GooglePlacesSupplierProvider


class SupplierProviderFactory:
    """Factory to get active supplier provider."""

    @classmethod
    def get_provider(cls) -> type[BaseSupplierProvider]:
        """Return provider class based on settings.SUPPLIER_PROVIDER."""
        provider_name = (getattr(settings, "SUPPLIER_PROVIDER", "osm") or "osm").lower()
        if provider_name == "google":
            return GooglePlacesSupplierProvider
        return OSMSupplierProvider
