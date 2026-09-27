"""
Market Commodity Canonicalizer and Catalogue.

Provides canonical normalization for agricultural commodity names,
spacing variants (e.g. 'Paddy(Common)' vs 'Paddy (Common)'), aliases,
and supplies a data-driven supported commodity catalogue.
"""

import re
from datetime import date
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session

from ..database import repository

# Controlled canonical mappings for Agmarknet / data.gov.in commodity dataset
CANONICAL_COMMODITY_MAP: Dict[str, str] = {
    # Paddy / Rice
    "paddy(common)": "Paddy(Common)",
    "paddy (common)": "Paddy(Common)",
    "paddy common": "Paddy(Common)",
    "paddy": "Paddy(Common)",
    "dhan": "Paddy(Common)",
    "rice": "Paddy(Common)",
    "paddy(basmati)": "Paddy(Basmati)",
    "paddy (basmati)": "Paddy(Basmati)",
    "paddy basmati": "Paddy(Basmati)",
    "basmati": "Paddy(Basmati)",

    # Cereals
    "wheat": "Wheat",
    "gehun": "Wheat",
    "maize": "Maize",
    "corn": "Maize",
    "makka": "Maize",
    "sweet corn": "Sweet Corn",
    "baby corn": "Baby Corn",
    "barley": "Barley(Jau)",
    "barley(jau)": "Barley(Jau)",
    "barley (jau)": "Barley(Jau)",
    "jowar": "Jowar(Sorghum)",
    "jowar(sorghum)": "Jowar(Sorghum)",
    "jowar (sorghum)": "Jowar(Sorghum)",
    "bajra": "Bajra(Pearl Millet/Cumbu)",
    "bajra(pearl millet/cumbu)": "Bajra(Pearl Millet/Cumbu)",
    "bajra (pearl millet/cumbu)": "Bajra(Pearl Millet/Cumbu)",
    "ragi": "Ragi (Finger Millet)",
    "ragi (finger millet)": "Ragi (Finger Millet)",
    "ragi(finger millet)": "Ragi (Finger Millet)",

    # Fiber Crops
    "cotton": "Cotton",
    "kapas": "Cotton",
    "jute": "Jute",

    # Pulses
    "masur dal": "Masur Dal",
    "masur dal (lentil)": "Masur Dal",
    "masur dal(lentil)": "Masur Dal",
    "masur": "Masur Dal",
    "lentil": "Masur Dal",
    "lentils": "Masur Dal",
    "bengal gram": "Bengal Gram(Gram)(Whole)",
    "bengal gram(gram)(whole)": "Bengal Gram(Gram)(Whole)",
    "bengal gram (gram) (whole)": "Bengal Gram(Gram)(Whole)",
    "bengal gram (chana)": "Bengal Gram(Gram)(Whole)",
    "bengal gram(chana)": "Bengal Gram(Gram)(Whole)",
    "chana": "Bengal Gram(Gram)(Whole)",
    "gram": "Bengal Gram(Gram)(Whole)",
    "arhar": "Arhar (Tur/Red Gram)(Whole)",
    "arhar (tur / red gram)": "Arhar (Tur/Red Gram)(Whole)",
    "arhar (tur/red gram)": "Arhar (Tur/Red Gram)(Whole)",
    "arhar (tur / red gram)(whole)": "Arhar (Tur/Red Gram)(Whole)",
    "tur": "Arhar (Tur/Red Gram)(Whole)",
    "red gram": "Arhar (Tur/Red Gram)(Whole)",
    "moong": "Green Gram (Moong)(Whole)",
    "green gram": "Green Gram (Moong)(Whole)",
    "green gram (moong)": "Green Gram (Moong)(Whole)",
    "green gram(moong)": "Green Gram (Moong)(Whole)",
    "urad": "Black Gram (Urd Beans)(Whole)",
    "black gram": "Black Gram (Urd Beans)(Whole)",
    "black gram (urad)": "Black Gram (Urd Beans)(Whole)",
    "black gram(urad)": "Black Gram (Urd Beans)(Whole)",

    # Additional display variations
    "bajra (pearl millet)": "Bajra(Pearl Millet/Cumbu)",
    "bajra(pearl millet)": "Bajra(Pearl Millet/Cumbu)",

    # Vegetables
    "potato": "Potato",
    "alu": "Potato",
    "aloo": "Potato",
    "tomato": "Tomato",
    "tamatar": "Tomato",
    "onion": "Onion",
    "pyaz": "Onion",
    "brinjal": "Brinjal",
    "baingan": "Brinjal",
    "eggplant": "Brinjal",
    "green chilli": "Green Chilli",
    "chilli": "Green Chilli",
    "mirchi": "Green Chilli",
    "bhindi(ladies finger)": "Bhindi(Ladies Finger)",
    "bhindi (ladies finger)": "Bhindi(Ladies Finger)",
    "bhindi": "Bhindi(Ladies Finger)",
    "ladies finger": "Bhindi(Ladies Finger)",
    "coriander(leaves)": "Coriander(Leaves)",
    "coriander (leaves)": "Coriander(Leaves)",
    "coriander": "Coriander(Leaves)",
    "dhania": "Coriander(Leaves)",
    "cauliflower": "Cauliflower",
    "gobi": "Cauliflower",
    "cabbage": "Cabbage",
    "raddish": "Raddish",
    "mooli": "Raddish",
    "bottle gourd": "Bottle gourd",
    "lauki": "Bottle gourd",
    "drumstick": "Drumstick",
    "amaranthus": "Amaranthus",

    # Fruits & Cash Crops
    "banana": "Banana",
    "kela": "Banana",
    "apple": "Apple",
    "mango": "Mango",
    "sugarcane": "Sugarcane",
    "gur": "Gur(Jaggery)",
    "gur(jaggery)": "Gur(Jaggery)",
    "gur (jaggery)": "Gur(Jaggery)",
    "jaggery": "Gur(Jaggery)",
    "mustard": "Mustard",
    "sarson": "Mustard",
    "groundnut": "Groundnut",
    "soyabean": "Soyabean",
    "soybean": "Soyabean",
}

# Human-friendly display names for canonical keys
DISPLAY_NAME_OVERRIDES: Dict[str, str] = {
    "Paddy(Common)": "Paddy (Common)",
    "Paddy(Basmati)": "Paddy (Basmati)",
    "Bhindi(Ladies Finger)": "Bhindi (Ladies Finger)",
    "Coriander(Leaves)": "Coriander (Leaves)",
    "Gur(Jaggery)": "Gur (Jaggery)",
    "Barley(Jau)": "Barley (Jau)",
    "Jowar(Sorghum)": "Jowar (Sorghum)",
    "Bajra(Pearl Millet/Cumbu)": "Bajra (Pearl Millet)",
    "Bengal Gram(Gram)(Whole)": "Bengal Gram (Chana)",
    "Arhar (Tur/Red Gram)(Whole)": "Arhar (Tur / Red Gram)",
    "Green Gram (Moong)(Whole)": "Green Gram (Moong)",
    "Black Gram (Urd Beans)(Whole)": "Black Gram (Urad)",
    "Masur Dal": "Masur Dal (Lentil)",
}

# Curated core catalogue of key commodities with categories
CURATED_COMMODITY_METADATA: List[Dict[str, str]] = [
    {"canonical_name": "Paddy(Common)", "category": "Cereals", "display_name": "Paddy (Common)"},
    {"canonical_name": "Wheat", "category": "Cereals", "display_name": "Wheat"},
    {"canonical_name": "Maize", "category": "Cereals", "display_name": "Maize"},
    {"canonical_name": "Cotton", "category": "Fiber Crops", "display_name": "Cotton"},
    {"canonical_name": "Masur Dal", "category": "Pulses", "display_name": "Masur Dal (Lentil)"},
    {"canonical_name": "Potato", "category": "Vegetables", "display_name": "Potato"},
    {"canonical_name": "Tomato", "category": "Vegetables", "display_name": "Tomato"},
    {"canonical_name": "Onion", "category": "Vegetables", "display_name": "Onion"},
    {"canonical_name": "Brinjal", "category": "Vegetables", "display_name": "Brinjal"},
    {"canonical_name": "Green Chilli", "category": "Vegetables", "display_name": "Green Chilli"},
    {"canonical_name": "Banana", "category": "Fruits", "display_name": "Banana"},
    {"canonical_name": "Paddy(Basmati)", "category": "Cereals", "display_name": "Paddy (Basmati)"},
]


def canonicalize_commodity(commodity: str) -> str:
    """
    Map an input commodity string to its canonical database name.

    Handles:
    - Spacing around parentheses: 'Paddy (Common)' -> 'Paddy(Common)'
    - Case insensitivity: 'paddy(common)' -> 'Paddy(Common)'
    - Common aliases: 'rice' -> 'Paddy(Common)', 'corn' -> 'Maize'
    - Retains unrecognized names if already canonical.
    """
    if not commodity:
        return commodity

    cleaned = commodity.strip()
    lower_cleaned = cleaned.lower()

    # 1. Exact alias match
    if lower_cleaned in CANONICAL_COMMODITY_MAP:
        return CANONICAL_COMMODITY_MAP[lower_cleaned]

    # 1b. Check reverse of DISPLAY_NAME_OVERRIDES
    for canon, disp in DISPLAY_NAME_OVERRIDES.items():
        if lower_cleaned == disp.lower():
            return canon

    # 2. Spacing normalization around parentheses:
    # "Paddy (Common)" -> "Paddy(Common)"
    no_space = re.sub(r"\s*\(\s*", "(", cleaned)
    no_space = re.sub(r"\s*\)\s*", ")", no_space)
    if no_space.lower() in CANONICAL_COMMODITY_MAP:
        return CANONICAL_COMMODITY_MAP[no_space.lower()]

    for canon, disp in DISPLAY_NAME_OVERRIDES.items():
        disp_no_space = re.sub(r"\s*\(\s*", "(", disp)
        disp_no_space = re.sub(r"\s*\)\s*", ")", disp_no_space)
        if no_space.lower() == disp_no_space.lower():
            return canon

    return no_space


def get_commodity_display_name(canonical_name: str) -> str:
    """
    Return a farmer-friendly display name for a canonical commodity.
    """
    if not canonical_name:
        return canonical_name

    if canonical_name in DISPLAY_NAME_OVERRIDES:
        return DISPLAY_NAME_OVERRIDES[canonical_name]

    # Insert a space before '(' if missing for cleaner presentation
    spaced = re.sub(r"(\w)\(", r"\1 (", canonical_name)
    return spaced


def get_supported_commodities_catalogue(
    db: Session,
    state: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Build a supported commodity catalogue reflecting real database coverage.

    - Distinguishes whether the commodity is available in the selected state.
    - Automatically surfaces any additional commodities with observations in that state.
    - Available commodities are sorted to the top.
    """
    repo = repository.MarketObservationRepository(db)

    # 1. Distinct commodities in the requested state
    state_commodities = repo.list_distinct_commodities(state=state) if state else []
    state_map: Dict[str, Dict[str, Any]] = {
        row[0]: {"count": row[1], "latest_date": row[2]}
        for row in state_commodities
    }

    # 2. Nationwide distinct commodities
    nationwide_commodities = repo.list_distinct_commodities()
    nationwide_map: Dict[str, Dict[str, Any]] = {
        row[0]: {"count": row[1], "latest_date": row[2]}
        for row in nationwide_commodities
    }

    items: List[Dict[str, Any]] = []
    seen_canonical = set()

    # Add items from curated list
    for entry in CURATED_COMMODITY_METADATA:
        can_name = entry["canonical_name"]
        seen_canonical.add(can_name)

        in_state_info = state_map.get(can_name)
        nationwide_info = nationwide_map.get(can_name)

        if state:
            is_available = in_state_info is not None and in_state_info["count"] > 0
            obs_count = in_state_info["count"] if in_state_info else 0
            latest_date_val = in_state_info["latest_date"] if in_state_info else None
        else:
            is_available = nationwide_info is not None and nationwide_info["count"] > 0
            obs_count = nationwide_info["count"] if nationwide_info else 0
            latest_date_val = nationwide_info["latest_date"] if nationwide_info else None

        items.append({
            "canonical_name": can_name,
            "display_name": entry["display_name"],
            "category": entry["category"],
            "is_available": is_available,
            "observation_count": obs_count,
            "total_nationwide": nationwide_info["count"] if nationwide_info else 0,
            "latest_date": latest_date_val,
        })

    # Add any extra commodities present in this specific state that weren't in the curated list
    for can_name, s_info in state_map.items():
        if can_name not in seen_canonical:
            seen_canonical.add(can_name)
            nationwide_info = nationwide_map.get(can_name)
            items.append({
                "canonical_name": can_name,
                "display_name": get_commodity_display_name(can_name),
                "category": "Other",
                "is_available": True,
                "observation_count": s_info["count"],
                "total_nationwide": nationwide_info["count"] if nationwide_info else s_info["count"],
                "latest_date": s_info["latest_date"],
            })

    # Sort available items first, then by observation count descending, then by name
    items.sort(key=lambda x: (not x["is_available"], -x["observation_count"], x["display_name"]))
    return items
