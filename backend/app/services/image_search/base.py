"""
Base Image Provider module.
Defines normalized ImageCandidate schema and abstract ImageProvider interface.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from ...data.crop_catalogue import CropEntity


class ImageCandidate(BaseModel):
    """Normalized Image Candidate representation across all image providers."""
    url: str
    thumbnail_url: Optional[str] = None
    title: str
    description: Optional[str] = None
    provider: str  # e.g., "Wikimedia Commons", "GBIF", "Pexels", "iNaturalist"
    source_url: str
    author: Optional[str] = None
    license: Optional[str] = None
    license_url: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    tags: List[str] = Field(default_factory=list)
    relevance_score: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ImageProvider(ABC):
    """Abstract Base Class for Image Search Providers."""

    def __init__(self, provider_name: str):
        self.provider_name = provider_name

    @abstractmethod
    async def search(
        self,
        query: str,
        entity: CropEntity,
        max_candidates: int = 10
    ) -> List[ImageCandidate]:
        """Search provider for image candidates given a query and canonical entity."""
        pass

    @abstractmethod
    def is_configured(self) -> bool:
        """Check if provider credentials/dependencies are ready."""
        pass
