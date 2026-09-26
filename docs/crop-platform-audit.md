# AgriNexus-AI Smart Crop Recommendation Platform Audit

**Document Status:** Complete Audit Report  
**Author:** Lead Agricultural Decision-Support Architect  
**System Version:** AgriNexus-AI v2.0  
**Date:** September 2026  

---

## Executive Summary

This document presents a comprehensive, scientific audit of the existing **AgriNexus-AI Crop Recommendation Platform**. The audit evaluates the complete pipeline spanning frontend UI components, API routers, backend service orchestrators, scientific suitability engines, data contexts (location, weather, soil, season), crop requirement profiles, and the frozen Machine Learning model (`Notebook/models/crop_recommendation.pkl`).

The objective is to transform AgriNexus-AI from a black-box crop predictor into a **transparent, explainable, and scientifically defensible agricultural decision-support engine**.

---

## 1. End-to-End System Pipeline & Data Flow Audit

The existing system processes crop recommendations through a multi-stage pipeline:

```
[USER / GEOLOCATION / MAP]
           │
           ▼
 [LocationContext] (lat, lon, displayName, district, state)
           │
           ├──────────────────────────┐
           ▼                          ▼
 [WeatherContextService]    [SoilContextService]
 (Open-Meteo Telemetry)     (Geospatial 250m / Lab Overrides)
           │                          │
           └──────────┬───────────────┘
                      ▼
               [SeasonEngine]
         (Regional Kharif/Rabi/Zaid)
                      │
                      ▼
          [SmartCropRecommender]
                      │
         ┌────────────┴────────────┐
         ▼                         ▼
 [Frozen ML Model]        [CropSuitabilityEngine]
 (ExtraTrees 22 crops)    (26 Catalogue Crop Profiles)
 (Requires: N,P,K,        (LimitationEngine &
  temp, hum, pH, rain)     SowingFeasibilityEngine)
         │                         │
         └────────────┬────────────┘
                      ▼
           [Ranked Recommendations]
                      │
                      ▼
             [POST /crop/recommend-smart]
                      │
                      ▼
         [Frontend CropPage & UI]
     (FieldSnapshotPanel, FeaturedCropCard,
      AlternativeCropCard, CropDetailModal)
```

### Transformation Log:
1. **User Input / Geolocation:** Coordinates (`lat`, `lon`) are retrieved via browser Geolocation API or Map selection.
2. **Weather Retrieval:** `WeatherContextService` fetches current temperature, humidity, 7-day forecast rainfall, max rain probability, and ET0 estimates.
3. **Soil Retrieval:** `SoilContextService` fetches estimated soil pH, N, P, K, and soil texture from regional geospatial grids or accepts lab test overrides.
4. **Season Determination:** `SeasonEngine` identifies active regional agricultural season (Kharif, Rabi, Zaid, Annual) and sowing windows.
5. **ML Incomplete Check:** If N, P, or K is missing, `SmartCropRecommender` skips the frozen ML model, marking ML support as `Unavailable` while allowing the agronomic suitability engine to proceed.
6. **Agronomic Evaluation:** `CropSuitabilityEngine` evaluates each candidate crop profile against environmental limitations (Question A: "Can it grow here?") and sowing timing feasibility (Question B: "Should it be sown now?").
7. **Ranking & Presentation:** Crops are ranked by suitability score and presented in the React UI with clear separation of land suitability, sowing feasibility, ML support, and data completeness.

---

## 2. Comprehensive Audit Findings & Structural Issues

### Issue 1: Crop Image Mismatch & Content Integrity Bug (CRITICAL)
- **Symptom:** When Mango (*Mangifera indica*) is recommended as the top crop, the main image on the `FeaturedCropCard` displays a cereal/wheat/corn field instead of a mango orchard.
- **Root Cause:** Frontend code in `FeaturedCropCard.tsx` (Line 44) attempts to load `/images/crops/mango.webp`. Because the directory `frontend/public/images/crops/` was missing or incomplete, the `onError` handler (Line 59) silently fell back to `/images/crop-intelligence.webp` (a wheat field hero image).
- **Resolution Plan:**
  1. Build a canonical crop image directory (`frontend/public/images/crops/`) populated with accurate, high-resolution imagery for all 26 supported crops.
  2. Implement a strict `cropId -> crop image` verification mapping with descriptive alt text and appropriate license metadata.
  3. Replace generic fallbacks with crop-specific placeholders if an image fails to load, never displaying misleading agricultural species.

---

### Issue 2: Misleading Terminology — "ML Evidence: Catalogue Crop" (CRITICAL)
- **Symptom:** UI displays badges reading `"ML Evidence: Catalogue Crop"` for crops not included in the ML training set (e.g., Mustard, Sugarcane, Potato, Groundnut).
- **Root Cause:** Conflation of ML model classification with agronomic catalogue evaluation. Calling a crop a "Catalogue Crop" under "ML Evidence" is semantically wrong and confusing to agriculturalists.
- **Resolution Plan:**
  - Replace terminology with explicit status indicators:
    - **ML Supported Crop:** `ML SUPPORT: Available (Probability: XX%)`
    - **Catalogue-Only Crop:** `ML SUPPORT: Catalogue-only assessment`
    - **Incomplete Inputs:** `ML SUPPORT: Unavailable (Reason: Soil P/K required for ML model)`
  - Never fabricate ML probabilities or present catalogue evaluation as ML predictions.

---

### Issue 3: Overconfident 97/100 Suitability Score Audit (CRITICAL)
- **Symptom:** Screenshot shows a 97/100 "Highly Suitable" score for Mango when Phosphorus (P) and Potassium (K) are unmeasured, soil pH is estimated, and ML model support is unavailable.
- **Root Cause:**
  1. Missing parameters (P/K) were silently excluded from the average calculation without penalizing the evidence quality or score confidence.
  2. Dynamic weight re-allocation redistributed 20% ML weight onto land suitability without accounting for data uncertainty.
  3. Conflation of **Environmental Suitability** with **Data Completeness**.
- **Resolution Plan:**
  - Implement a transparent, reproducible **Suitability Index (0–100)** based on strict limiting-factor scoring.
  - Explicitly decouple **Agronomic Suitability** (e.g., "Highly Suitable") from **Data Completeness** (e.g., "60% Complete - Field Soil Test Recommended").
  - Ensure missing critical inputs trigger explicit warnings and prevent artificial score inflation.

---

### Issue 4: Location Inconsistency & Stale Context Risks (HIGH)
- **Symptom:** Potential mismatch between header location display, map coordinates, weather context, soil context, and crop calendar region during rapid location updates or async race conditions.
- **Root Cause:** Asynchronous state propagation where weather and soil contexts resolve independently without invalidating existing recommendation results.
- **Resolution Plan:**
  - Enforce `LocationContext` as the single canonical source of truth (`lat`, `lon`, `district`, `state`).
  - Implement strict context invalidation: whenever location changes, immediately invalidate cached weather, soil, season, and recommendation results.
  - Add location hash verification across header, panel, and API requests.

---

### Issue 5: Frozen ML Model Contract & Missing Nutrients (HIGH)
- **Symptom:** If user phosphorus/potassium data is missing, attempting to feed defaults (e.g., 0.0 or estimated SoilGrids total N) into the frozen ML model corrupts prediction accuracy.
- **Root Cause:** `crop_recommendation.pkl` is an `ExtraTreesClassifier` trained strictly on unscaled feature vectors `[N, P, K, temperature, humidity, pH, rainfall]`.
- **Resolution Plan:**
  - Maintain the frozen model contract without modification.
  - If N, P, or K is missing, gracefully mark `ML_UNAVAILABLE` rather than inventing synthetic soil nutrient values.
  - Allow the agronomic suitability engine to continue evaluating temperature, rainfall, soil pH, texture, season, and sowing feasibility.

---

### Issue 6: Measured Data Override Priority (HIGH)
- **Symptom:** User-entered lab test results were not clearly prioritized over coarse 250m geospatial soil estimates.
- **Root Cause:** Lack of strict provenance hierarchy in soil data merging.
- **Resolution Plan:**
  - Enforce data priority:  
    `LAB/FIELD MEASURED > USER-PROVIDED VERIFIED > LOCAL AUTHORITATIVE > GEOSPATIAL ESTIMATE (SoilGrids) > UNKNOWN`.
  - Label every displayed parameter with its exact provenance type (`MEASURED` vs `ESTIMATED`).

---

### Issue 7: Weather Telemetry vs Agro-Climatic Context (MEDIUM)
- **Symptom:** Short-term 7-day weather forecasts were treated as long-term climate suitability.
- **Root Cause:** Lack of explicit separation between 30-year agro-climatic normals and real-time/forecast weather telemetry.
- **Resolution Plan:**
  - Explicitly separate long-term agro-climatic thermal/rainfall suitability from short-term weather window feasibility.

---

### Issue 8: UI Hierarchy & Visual Noise (MEDIUM)
- **Symptom:** Excessive card stacking on the recommendation page created visual noise and equalized important recommendations with minor telemetry items.
- **Root Cause:** Overuse of nested cards without clear visual hierarchy.
- **Resolution Plan:**
  - Redesign layout with a clean top-to-bottom decision hierarchy:
    1. **Page Hero & Mode Switcher** (Smart Auto / Hybrid / Manual)
    2. **Field Intelligence Snapshot** (Unified Location, Weather, Soil, Season)
    3. **Featured Top Recommendation** (#1 Suited Crop with rich details)
    4. **Other Suitable Options** (Compact cards for alternative crops)
    5. **Multi-Crop Comparison Bar**
    6. **Transparent Data Provenance & Sources**

---

## 3. Summary of Action Items

| Component | Audit Finding | Required Action |
| :--- | :--- | :--- |
| **Frontend Images** | Missing crop images causing wheat field fallback for Mango | Create canonical crop image asset library & strict image validation |
| **Terminology** | "Catalogue Crop" displayed under ML Evidence | Update labels to "ML SUPPORT: Catalogue-only assessment" |
| **Suitability Score** | 97/100 score inflated despite missing P/K | Decouple Suitability Index from Data Completeness; fix limiting-factor score math |
| **Location Engine** | Async race condition & stale location state | Enforce canonical state & invalidation on location change |
| **ML Engine** | Missing P/K synthetic value creation | Mark ML as `Unavailable` when nutrients missing; do not invent values |
| **Soil Engine** | SoilGrids estimates shown as measured data | Implement strict provenance tracking (`MEASURED` vs `ESTIMATED`) |
| **UI/UX Layout** | Card-heavy layout with poor visual hierarchy | Reconstruct page around Field Intelligence -> Featured Crop -> Alternatives |

---
*Audit Document Approved for Implementation.*
