# AGRINEXUS-AI CROP SUITABILITY & RECOMMENDATION ENGINE
## REPOSITORY AUDIT & ARCHITECTURAL SPECIFICATION

**Document ID:** `docs/crop-engine-architecture.md`  
**Author:** Lead Agricultural Decision-Support Systems Architect & FastAPI/React Architect  
**Version:** 1.0.0 (Architectural Specification)  
**Status:** Approved for Implementation  

---

## 1. CURRENT REPOSITORY AUDIT

### 1.1 Existing Codebase Overview
AgriNexus-AI is a full-stack agricultural decision-support platform built on FastAPI (backend) and React/TypeScript (frontend). The system integrates multiple AI models and telemetry services:

* **Backend Framework:** FastAPI with Pydantic v2 schemas and modular service design (`backend/app/`).
* **Frontend Framework:** Vite + React + TypeScript + Tailwind CSS with Lucide icons (`frontend/src/`).
* **Frozen ML Models:** 7 trained ML artifacts in `Notebook/models/` managed via a singleton `ModelRegistry` (`backend/app/services/model_registry.py`).
  * `crop_recommendation.pkl` — ExtraTreesClassifier champion model + IsolationForest anomaly detector. Trained on `[N, P, K, temperature, humidity, ph, rainfall]`.
* **Location Management:** Global React `LocationContext` (`frontend/src/context/LocationContext.tsx`) with Leaflet interactive map picker (`LocationPicker.tsx`) and reverse geocoding.
* **Weather Service:** Open-Meteo API integrator (`backend/app/services/weather_service.py` & `weather_context.py`) delivering current weather & 7-day forecast.
* **Agriculture Intelligence Package:** Initial prototypes in `backend/app/services/agriculture/`:
  * `crop_profiles.py`: 26 crop profiles (22 ML-supported + 4 catalogue expansion crops).
  * `crop_suitability.py`: Weighted suitability function evaluator.
  * `season_engine.py`: India-aware regional agricultural season identifier.
  * `soil_context.py`: SoilGrids 250m geospatial soil estimator + USDA texture derivation.
  * `weather_context.py`: Multi-window weather telemetry retriever.
  * `smart_crop_recommender.py`: Initial recommendation pipeline orchestrator.

---

## 2. REUSABLE COMPONENTS IDENTIFIED

1. **Frozen ML Artifact:** `Notebook/models/crop_recommendation.pkl` & `ModelRegistry.predict_crop()`. High-accuracy ExtraTrees model, preserved without retraining.
2. **Canonical Location System:** `LocationContext.tsx` on frontend providing global GPS/Map selection coordinates (`latitude`, `longitude`, `district`, `state`, `country`).
3. **Open-Meteo Integration:** `WeatherService` & `WeatherContextService` with 30-minute in-memory caching.
4. **SoilGrids USDA Texture Classifier:** `derive_soil_texture()` logic in `soil_context.py`.
5. **India Agro-Climatic Season Rules:** `SeasonEngine.get_season_info()`.
6. **UI Components:** `AgriculturalPageHero.tsx`, `GlassCard.tsx`, `Input.tsx`, `Button.tsx`, `ConfidenceBar.tsx`, `ScopeWarning.tsx`, `LocationPicker.tsx`.

---

## 3. AUDIT PROBLEMS & DEFICIENCIES IDENTIFIED

1. **Collapsing Suitability into a Single Weighted Mean:** The initial prototype used an ad-hoc weighted average (30% ML, 15% season, 15% temp, 15% rain, 10% pH, 5% texture, 10% region). This allowed a crop with lethal soil pH or severe temperature violation to receive a high recommendation if other factors were high.
2. **Conflating Land Suitability with Sowing Window:** The system did not distinguish "Can grow here generally" from "Is it the right time to sow today?".
3. **Lack of Strict Limitation Analysis:** Missing Liebig's Law of the Minimum logic to penalize hard agronomic constraints.
4. **Simplistic Weather Feature Aggregations:** Weather suitability relied only on single current temperature rather than multi-window aggregations (14-day recent rain, 7-day forecast extremes, ET0).
5. **Absence of Sowing Feasibility Engine:** Sowing windows were checked as static season labels rather than dynamic calendar date ranges.
6. **Frontend Crop Comparison Gap:** Users could not compare multiple crops side-by-side across all agronomic dimensions.

---

## 4. MISSING COMPONENTS TO IMPLEMENT

1. **`limitation_engine.py` / FAO Limiting-Factor Logic:** Explicit evaluation of hard vs soft constraints.
2. **`sowing_feasibility.py`:** Dedicated engine comparing current date, regional calendar sowing start/end dates, and recent 14-day rainfall.
3. **`crop_calendar_service.py` Integration:** Deep integration with structured district/state crop calendars.
4. **Multi-Crop Comparison Tool:** Frontend modal/drawer allowing side-by-side matrix comparison of 2–4 crops across Land, Climate, Weather, Season, Sowing, Water, ML Evidence, and Data Completeness.
5. **Agronomic Validation Suite:** Level 1 through Level 10 test coverage producing `docs/agronomic-validation-report.md`.

---

## 5. PROPOSED TARGET ARCHITECTURE

```
                                [ FIELD LOCATION ]
                         (GPS / Map Selection / Search)
                                       │
                    ┌──────────────────┴──────────────────┐
                    ▼                                     ▼
        [ OPEN-METEO API ]                       [ SOIL INTELLIGENCE ]
 (Current, 14d Recent, 7d Forecast)       (Lab Test Override / SoilGrids 250m)
                    │                                     │
                    └──────────────────┬──────────────────┘
                                       ▼
                       [ REGIONAL CROP CALENDAR SERVICE ]
                         (State / District Agro Zones)
                                       │
                                       ▼
                   [ AGRINEXUS SUITABILITY & LIMITATION ENGINE ]
       ┌───────────────────────────────┼───────────────────────────────┐
       ▼                               ▼                               ▼
[ LAND / SOIL ]             [ AGRO-CLIMATE & WEATHER ]      [ SOWING FEASIBILITY ]
(pH, Texture, Depth)        (Temp, Rain, ET0, Season)       (Calendar, 14d Moisture)
       │                               │                               │
       └───────────────────────────────┼───────────────────────────────┘
                                       ▼
                         [ OPTIONAL ML MODEL EVIDENCE ]
                   (Runs ONLY when N,P,K,Temp,Hum,pH,Rain valid)
                                       │
                                       ▼
                      [ PROVENANCE & DATA QUALITY ENGINE ]
                           (Data Completeness Score)
                                       │
                                       ▼
                      [ RANKED DECISION-SUPPORT RESPONSE ]
```

---

## 6. END-TO-END DATA FLOW

1. **User Action:** Farmer selects field location on map or accepts GPS coordinates in React UI.
2. **Frontend Dispatch:** `CropPage` passes canonical `LocationState` to `useSmartCropRecommendation`.
3. **API Request:** Frontend issues `POST /api/v1/crop/recommend-smart` with location, optional soil lab test overrides, and farm management context.
4. **Backend Pipeline Execution:**
   * `WeatherContextService` retrieves current, recent 14d, and 7d forecast weather.
   * `SoilContextService` compiles soil properties (using user lab test if present, or SoilGrids 250m estimate; missing P/K remain `None`).
   * `SeasonEngine` & `CropCalendarService` resolve current agricultural season and district sowing windows.
   * `ModelRegistry.predict_crop()` evaluates frozen ExtraTrees ML model **if and only if** all 7 features (N, P, K, temp, humidity, pH, rainfall) are legitimately available.
   * `CropSuitabilityEngine` evaluates all 26 catalogue crops through `LimitationEngine` and `SowingFeasibilityEngine`.
   * Candidates ranked by agronomic suitability index, annotated with explicit limiting factors, reasons, warnings, and provenance badges.
5. **UI Rendering:** Frontend displays field intelligence status panel, interactive crop cards, detailed modal views, and crop comparison matrix.

---

## 7. API DESIGN SPECIFICATION

### POST `/api/v1/crop/recommend-smart`

#### Request Payload Schema:
```json
{
  "mode": "auto",
  "location": {
    "latitude": 22.72,
    "longitude": 88.48,
    "displayName": "Barasat, North 24 Parganas, West Bengal",
    "district": "North 24 Parganas",
    "state": "West Bengal",
    "country": "India",
    "source": "MAP_SELECTION"
  },
  "soil": {
    "nitrogen": 90.0,
    "phosphorus": null,
    "potassium": null,
    "ph": 6.5
  },
  "farm": {
    "area_acres": 2.5,
    "water_availability": "Irrigated"
  },
  "preferences": {
    "category": "all"
  }
}
```

#### Response Payload Schema:
```json
{
  "success": true,
  "engine_version": "1.0.0",
  "mode": "hybrid",
  "data_completeness": 0.82,
  "location": {
    "latitude": 22.72,
    "longitude": 88.48,
    "display_name": "Barasat, North 24 Parganas, West Bengal",
    "district": "North 24 Parganas",
    "state": "West Bengal",
    "country": "India"
  },
  "season": {
    "season": "Kharif",
    "regional_season": "Aman (Main Monsoon Rice Season - West Bengal)",
    "sowing_window": "June - July",
    "harvest_window": "November - December",
    "current_month": "September",
    "state": "West Bengal"
  },
  "weather": { ... },
  "soil": { ... },
  "ml_status": {
    "available": false,
    "anomaly_status": "Inputs incomplete (Missing P, K) — ML model prediction unavailable"
  },
  "recommendations": [
    {
      "crop": "rice",
      "display_name": "Rice (Paddy)",
      "scientific_name": "Oryza sativa",
      "ml_supported": true,
      "category": "cereal",
      "suitability_score": 91,
      "suitability_level": "Highly Suitable",
      "sowing_feasibility": "GOOD_WINDOW",
      "land_suitability": "Suitable",
      "climate_suitability": "Highly Suitable",
      "ml_prediction": { "supported": true, "probability": null },
      "limiting_factors": [],
      "reasons": [
        "✓ Temperature (28.0°C) is optimal (20-35°C)",
        "✓ Current season (Kharif) matches optimal growing window",
        "✓ Soil pH (6.5) is optimal (5.5-7.0)"
      ],
      "warnings": [
        "⚠ Phosphorus (P) and Potassium (K) missing from soil test — verify with lab test"
      ],
      "missing_data": ["phosphorus", "potassium"],
      "data_sources": [
        { "domain": "Weather", "source": "Open-Meteo Weather API" },
        { "domain": "Soil", "source": "SoilGrids 250m Geospatial Estimate" }
      ]
    }
  ]
}
```

---

## 8. FAILURE MODES & GRACEFUL DEGRADATION

1. **Weather API Offline / Timeout:** Set `weather.data_available = false`. Fall back to seasonal climatological normals for the state/district. Post warning: `"Weather API unavailable. Evaluated using regional climatological averages."`
2. **Geospatial Soil Estimate Failure:** Default soil pH to neutral ($6.5$) and texture to Loam. Post warning: `"Geospatial soil estimation unavailable. Defaulted to regional average."`
3. **Missing P & K Nutrients:** Set ML status to `available = false`. DO NOT FABRICATE P or K as 0. Ecological suitability engine continues normally.
4. **Crop Calendar Missing for Region:** Fall back to national standard Kharif/Rabi/Zaid season definitions.

---

## 9. COMPREHENSIVE TEST PLAN

* **Level 1 — Unit Tests:** Test individual suitability piecewise functions, USDA texture derivation, and score calculations.
* **Level 2 — Boundary Tests:** Test inputs at exact optimal/acceptable thresholds ($T=15^\circ\text{C}, 25^\circ\text{C}, 38^\circ\text{C}$, $\text{pH}=5.5, 7.0, 8.0$).
* **Level 3 — Missing Data Tests:** Verify graceful behavior when weather, soil, or NPK are partially/fully missing.
* **Level 4 — Regional Scenarios:** Test Punjab (Rabi Wheat), West Bengal (Kharif Rice), Rajasthan (Mothbean/Mustard), Tamil Nadu (Kuruvai Rice).
* **Level 5 — Seasonal Tests:** Run same location across Kharif (July), Rabi (December), and Zaid (April).
* **Level 6 — Location Tests:** Run same crop across different Indian states.
* **Level 7 — Source Validation:** Ensure all crop profiles contain source URL, geographic scope, and citations.
* **Level 8 — ML Regression:** Verify `POST /api/v1/crop/recommend` legacy endpoint returns identical response for standard inputs.
* **Level 9 — End-to-End Tests:** Verify map coordinate selection updates backend recommendations seamlessly.
* **Level 10 — Agronomic Review Report:** Generate `docs/agronomic-validation-report.md`.

---
*Architectural specification approved for implementation by AgriNexus-AI Lead Architect.*
