"""
Canonical Crop Catalogue module.
Loads crop_catalogue.json and manages normalized scientific crop entities.
Guarantees:
- Input normalization (e.g., "mango", "Mango", "MANGIFERA INDICA" -> crop_id = "mango")
- Never invents scientific names
- Explicit unresolved state for unknown entities
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from ..core.logging import logger

DATA_DIR = Path(__file__).resolve().parent
CATALOGUE_PATH = DATA_DIR / "crop_catalogue.json"


class CropEntity(BaseModel):
    crop_id: str
    name: str
    scientific_name: Optional[str] = None
    category: str = "General"
    aliases: List[str] = Field(default_factory=list)
    search_terms: List[str] = Field(default_factory=list)
    positive_terms: List[str] = Field(default_factory=list)
    negative_terms: List[str] = Field(default_factory=list)
    is_resolved: bool = True


class CropCatalogue:
    """Manager for canonical crop entities."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CropCatalogue, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.entities: Dict[str, CropEntity] = {}
        self.alias_map: Dict[str, str] = {}
        self.load_catalogue()

    def load_catalogue(self):
        """Load canonical crop entities from JSON."""
        if not CATALOGUE_PATH.exists():
            logger.error(f"Crop catalogue file not found at {CATALOGUE_PATH}")
            return

        try:
            with open(CATALOGUE_PATH, "r", encoding="utf-8") as f:
                raw_data = json.load(f)

            for key, data in raw_data.items():
                entity = CropEntity(**data)
                self.entities[entity.crop_id] = entity

                # Map primary ID, name, scientific name, and aliases to crop_id
                self.alias_map[entity.crop_id.lower()] = entity.crop_id
                self.alias_map[entity.name.lower()] = entity.crop_id
                if entity.scientific_name:
                    self.alias_map[entity.scientific_name.lower()] = entity.crop_id

                for alias in entity.aliases:
                    self.alias_map[alias.lower()] = entity.crop_id

            logger.info(f"Loaded {len(self.entities)} canonical crop entities from catalogue.")
        except Exception as e:
            logger.error(f"Failed loading crop catalogue JSON: {e}")

    def get_entity(self, input_name: str) -> CropEntity:
        """
        Normalize input string to canonical crop entity.
        If unknown, returns an explicit unresolved entity WITHOUT inventing scientific names.
        """
        clean_key = input_name.strip().lower()

        if clean_key in self.alias_map:
            canonical_id = self.alias_map[clean_key]
            return self.entities[canonical_id]

        # Partial matching check
        for alias, cid in self.alias_map.items():
            if alias in clean_key or clean_key in alias:
                return self.entities[cid]

        # Explicit unresolved state (DO NOT invent scientific name)
        logger.warning(f"Crop entity '{input_name}' could not be resolved in canonical catalogue.")
        clean_id = clean_key.replace(" ", "_")
        return CropEntity(
            crop_id=clean_id,
            name=input_name.title(),
            scientific_name=None,  # Do NOT fabricate
            category="Unresolved",
            aliases=[clean_key],
            search_terms=[f"{input_name} crop agriculture", f"{input_name} plant"],
            negative_terms=[],
            is_resolved=False
        )


# Global instance helper
def get_crop_catalogue() -> CropCatalogue:
    return CropCatalogue()
