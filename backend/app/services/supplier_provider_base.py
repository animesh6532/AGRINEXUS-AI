"""
Abstract Base Class for Supplier Discovery Providers.
Allows seamlessly switching between OpenStreetMap (OSM) and other provider implementations.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseSupplierProvider(ABC):
    """Abstract Base Class for fertilizer & agro-input supplier discovery."""

    @abstractmethod
    def find_suppliers(
        self,
        latitude: float,
        longitude: float,
        radius_km: float = 5.0,
        sort_by: str = "nearest"
    ) -> Dict[str, Any]:
        """
        Find nearby fertilizer and agricultural suppliers around user GPS coordinates.

        :param latitude: User GPS latitude (-90.0 to 90.0)
        :param longitude: User GPS longitude (-180.0 to 180.0)
        :param radius_km: Search radius in kilometers
        :param sort_by: Sorting criterion ('nearest', 'name', 'relevance')
        :return: Standardized dictionary containing status, location, radius, suppliers, count, diagnostic messages.
        """
        pass
