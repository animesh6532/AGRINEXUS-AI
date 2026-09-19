"""
Bundled reference crop-calendar dataset for the Crop Calendar module.

IMPORTANT - DATA PROVENANCE AND LIMITATIONS
This dataset is a small, generalised INDIAN reference dataset bundled with
the backend so that the Crop Calendar module is functional and testable
without a verified external provider.

- It is REFERENCE/SAMPLE data, NOT authoritative agronomic data.
- Values are approximate, generalised conventions (typical sowing windows,
  typical crop durations, typical growth-stage breakdowns) and do NOT
  account for variety, soil, local climate, or year-specific conditions.
- Every API response built from this dataset is explicitly labelled with
  ``is_reference_data=True``, ``data_source="reference_dataset"`` and
  ``region_scope="india_generic"`` so it is never presented as an
  authoritative or real-time prediction.

A verified external crop-calendar provider (configured through
CROP_CALENDAR_API_BASE_URL / CROP_CALENDAR_API_KEY) should replace this
dataset as the active source once the team approves one.

All stage durations are in days and are intended to sum exactly to the
crop duration for each season (validated by tests and service checks).
"""

from typing import Any, Dict

# Provenance labels used across the module
REFERENCE_DATA_SOURCE = "reference_dataset"
REGION_SCOPE = "india_generic"

REFERENCE_NOTE = (
    "Bundled reference dataset: approximate, generalised Indian crop "
    "calendar conventions for demonstration and testing. NOT authoritative "
    "agronomic data and NOT a real-time prediction. A verified external "
    "crop-calendar provider should replace this source."
)

CROP_CALENDAR_REFERENCE_DATA: Dict[str, Dict[str, Any]] = {
    "rice": {
        "aliases": ["paddy", "dhan"],
        "seasons": {
            "kharif": {
                "sowing_window": {"start": "06-01", "end": "07-15"},
                "crop_duration_days": 135,
                "growth_stages": [
                    {
                        "stage": "nursery_sowing",
                        "duration_days": 25,
                        "activities": [
                            "Prepare nursery seedbed",
                            "Treat seeds before sowing (reference practice)",
                            "Prepare main field (puddling/land preparation)",
                        ],
                    },
                    {
                        "stage": "transplanting",
                        "duration_days": 10,
                        "activities": [
                            "Transplant seedlings to the main field",
                            "Maintain baseline standing water (reference practice)",
                        ],
                    },
                    {
                        "stage": "tillering",
                        "duration_days": 30,
                        "activities": [
                            "Weed control",
                            "Nitrogen top dressing (reference practice)",
                            "Maintain standing water",
                        ],
                    },
                    {
                        "stage": "panicle_initiation",
                        "duration_days": 25,
                        "activities": [
                            "Fertiliser top dressing (reference practice)",
                            "Pest and disease scouting",
                        ],
                    },
                    {
                        "stage": "flowering",
                        "duration_days": 15,
                        "activities": [
                            "Maintain standing water; avoid moisture stress",
                            "Avoid pesticide spraying during peak flowering (reference practice)",
                        ],
                    },
                    {
                        "stage": "grain_filling_maturity",
                        "duration_days": 30,
                        "activities": [
                            "Drain field towards maturity (reference practice)",
                            "Monitor grain moisture for harvest timing",
                        ],
                    },
                ],
                "notes": [
                    "Duration assumes a typical medium-duration transplanted kharif rice.",
                    "Irrigation continuity is critical from tillering to grain filling.",
                ],
            },
            "rabi": {
                "sowing_window": {"start": "11-15", "end": "01-15"},
                "crop_duration_days": 130,
                "growth_stages": [
                    {
                        "stage": "nursery_sowing",
                        "duration_days": 25,
                        "activities": [
                            "Prepare nursery seedbed",
                            "Treat seeds before sowing (reference practice)",
                            "Prepare main field",
                        ],
                    },
                    {
                        "stage": "transplanting",
                        "duration_days": 10,
                        "activities": [
                            "Transplant seedlings to the main field",
                            "Maintain baseline standing water (reference practice)",
                        ],
                    },
                    {
                        "stage": "tillering",
                        "duration_days": 25,
                        "activities": [
                            "Weed control",
                            "Nitrogen top dressing (reference practice)",
                        ],
                    },
                    {
                        "stage": "panicle_initiation",
                        "duration_days": 25,
                        "activities": [
                            "Fertiliser top dressing (reference practice)",
                            "Pest and disease scouting",
                        ],
                    },
                    {
                        "stage": "flowering",
                        "duration_days": 15,
                        "activities": [
                            "Maintain standing water; avoid moisture stress",
                        ],
                    },
                    {
                        "stage": "grain_filling_maturity",
                        "duration_days": 30,
                        "activities": [
                            "Drain field towards maturity (reference practice)",
                            "Monitor grain moisture for harvest timing",
                        ],
                    },
                ],
                "notes": [
                    "Rabi rice requires assured irrigation; cooler temperatures "
                    "lengthen the early stages.",
                ],
            },
        },
    },
    "wheat": {
        "aliases": ["gehun", "gandum"],
        "seasons": {
            "rabi": {
                "sowing_window": {"start": "11-01", "end": "12-15"},
                "crop_duration_days": 130,
                "growth_stages": [
                    {
                        "stage": "sowing_emergence",
                        "duration_days": 20,
                        "activities": [
                            "Seed treatment and sowing (reference practice)",
                            "Apply basal fertiliser (reference practice)",
                            "First irrigation around crown-root initiation",
                        ],
                    },
                    {
                        "stage": "tillering",
                        "duration_days": 30,
                        "activities": [
                            "Weed control",
                            "Nitrogen top dressing (reference practice)",
                        ],
                    },
                    {
                        "stage": "jointing",
                        "duration_days": 25,
                        "activities": [
                            "Irrigation as required (reference practice)",
                            "Pest scouting (e.g., aphids)",
                        ],
                    },
                    {
                        "stage": "flowering_anthesis",
                        "duration_days": 15,
                        "activities": [
                            "Avoid moisture stress",
                            "Monitor for rust diseases (reference practice)",
                        ],
                    },
                    {
                        "stage": "grain_filling",
                        "duration_days": 25,
                        "activities": [
                            "Last irrigation as required (reference practice)",
                            "Monitor grain moisture",
                        ],
                    },
                    {
                        "stage": "maturity",
                        "duration_days": 15,
                        "activities": [
                            "Prepare for harvest; monitor grain moisture",
                        ],
                    },
                ],
                "notes": [
                    "Duration assumes a typical medium-duration wheat variety.",
                    "Timely sowing within the window avoids terminal heat stress.",
                ],
            },
        },
    },
    "maize": {
        "aliases": ["makka", "corn"],
        "seasons": {
            "kharif": {
                "sowing_window": {"start": "06-15", "end": "07-15"},
                "crop_duration_days": 100,
                "growth_stages": [
                    {
                        "stage": "emergence",
                        "duration_days": 10,
                        "activities": [
                            "Seed treatment and sowing (reference practice)",
                            "Gap filling after emergence",
                        ],
                    },
                    {
                        "stage": "vegetative",
                        "duration_days": 30,
                        "activities": [
                            "Weed control",
                            "Nitrogen top dressing (reference practice)",
                        ],
                    },
                    {
                        "stage": "tasseling",
                        "duration_days": 15,
                        "activities": [
                            "Avoid moisture stress",
                            "Pest scouting (e.g., stem borer, fall armyworm)",
                        ],
                    },
                    {
                        "stage": "silking",
                        "duration_days": 10,
                        "activities": [
                            "Avoid moisture stress during silking",
                        ],
                    },
                    {
                        "stage": "grain_filling",
                        "duration_days": 25,
                        "activities": [
                            "Irrigation as required (reference practice)",
                        ],
                    },
                    {
                        "stage": "maturity",
                        "duration_days": 10,
                        "activities": [
                            "Monitor grain moisture; prepare for harvest",
                        ],
                    },
                ],
                "notes": [
                    "Duration assumes a typical medium-duration kharif maize hybrid.",
                ],
            },
        },
    },
    "cotton": {
        "aliases": ["kapas"],
        "seasons": {
            "kharif": {
                "sowing_window": {"start": "05-15", "end": "06-30"},
                "crop_duration_days": 170,
                "growth_stages": [
                    {
                        "stage": "emergence",
                        "duration_days": 15,
                        "activities": [
                            "Seed treatment and sowing (reference practice)",
                            "Gap filling and thinning",
                        ],
                    },
                    {
                        "stage": "vegetative",
                        "duration_days": 40,
                        "activities": [
                            "Weed control",
                            "Irrigation as required (reference practice)",
                        ],
                    },
                    {
                        "stage": "squaring",
                        "duration_days": 30,
                        "activities": [
                            "Pest scouting (e.g., sucking pests)",
                            "Nutrient top dressing (reference practice)",
                        ],
                    },
                    {
                        "stage": "flowering_boll_formation",
                        "duration_days": 45,
                        "activities": [
                            "Pest scouting (e.g., bollworms)",
                            "Avoid moisture stress",
                        ],
                    },
                    {
                        "stage": "boll_maturation_opening",
                        "duration_days": 40,
                        "activities": [
                            "Pick opened bolls in multiple rounds (reference practice)",
                            "Avoid premature termination of irrigation",
                        ],
                    },
                ],
                "notes": [
                    "Duration assumes a typical medium-duration kharif cotton hybrid.",
                    "Cotton is picked in multiple flushes; the harvest window is wide.",
                ],
            },
        },
    },
}


def get_reference_dataset() -> Dict[str, Dict[str, Any]]:
    """Return the bundled reference crop-calendar dataset."""
    return CROP_CALENDAR_REFERENCE_DATA
