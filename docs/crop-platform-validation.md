# AgriNexus-AI Crop Platform Validation & Verification Framework

**Document Status:** Complete Test Strategy & Quality Assurance Specification  
**Author:** QA Lead & Agricultural Software Verification Engineer  
**System Version:** AgriNexus-AI v2.0  
**Date:** September 2026  

---

## 1. Overview & Verification Strategy

The **AgriNexus-AI Crop Platform Validation Framework** defines the quantitative and automated test suites required to guarantee scientific accuracy, data consistency, architectural reliability, and UI robustness across all 20 critical agricultural decision scenarios.

Every modification to backend endpoints, suitability algorithms, context providers, or frontend UI components must pass all tests in this specification before deployment.

---

## 2. Test Suite Specifications (20 Critical Scenarios)

### Scenario 1: Missing Phosphorus (P) & Potassium (K)
- **Input Condition:** `user_n = 90.0`, `user_p = None`, `user_k = None`.
- **Expected Engine Behavior:**
  - Frozen ML Model status becomes `ML_UNAVAILABLE`.
  - ML probability is not computed or combined into score.
  - Agronomic suitability engine proceeds evaluating temperature, rainfall, soil pH, texture, season.
  - UI displays: `ML SUPPORT: Unavailable (Reason: Required soil NPK nutrients incomplete)`.
  - Data completeness score reflects missing nutrient parameters.
  - Warning generated: `⚠ Phosphorus and Potassium missing — verify with lab soil test`.

---

### Scenario 2: Missing Weather Telemetry
- **Input Condition:** External weather API fails or returns null telemetry.
- **Expected Engine Behavior:**
  - Fallback seasonal normal climate values used with explicit source labeling (`GEOSPATIAL_CLIMATE_NORMAL`).
  - Warning generated: `⚠ Real-time weather telemetry unavailable; regional climate normals applied`.
  - Data completeness score decremented by 20%.

---

### Scenario 3: Missing Soil pH Data
- **Input Condition:** Soil pH is unavailable from both user input and geospatial lookup (`soil.ph = None`).
- **Expected Engine Behavior:**
  - Neutral pH assumption (6.5) applied for preliminary evaluation.
  - Status marked as `UNKNOWN`.
  - Warning generated: `⚠ Soil pH unknown; neutral pH assumed`.

---

### Scenario 4: Missing Season Information
- **Input Condition:** Date or region lookup fails to return explicit season.
- **Expected Engine Behavior:**
  - Defaults to location-based agro-climatic zone default season.
  - Sowing window marked as `UNKNOWN`.

---

### Scenario 5 & 6: Location Change & Stale Location Invalidation
- **Test Sequence:**
  1. Select Location A (e.g., Tamluk, West Bengal: 22.28° N, 87.92° E). Record weather, soil, season, and top crop (e.g., Rice).
  2. Select Location B (e.g., Shimla, Himachal Pradesh: 31.10° N, 77.17° E).
- **Expected Engine Behavior:**
  - All Location A cached telemetry immediately invalidated.
  - Weather, soil, season, and crop recommendations recomputed for Location B.
  - Top crop changes appropriately (e.g., Apple / Kidneybeans for Shimla).
  - No residual Location A data remains in state or UI.

---

### Scenario 7 & 8: Measured Soil Overrides vs Estimated Soil
- **Test Case A (Geospatial Estimate):** SoilGrids estimates pH = 6.0.
  - UI displays: `Soil pH: 6.0 (Estimated from SoilGrids 250m)`.
- **Test Case B (Farmer Lab Override):** Farmer inputs lab result pH = 5.6.
  - Engine uses `5.6`.
  - UI displays: `Soil pH: 5.6 (Measured - Lab Test)`.
  - Estimated value (6.0) is overridden cleanly.

---

### Scenario 9: Unknown Soil Attributes
- **Expected Engine Behavior:** Unknown soil depth or texture is marked as `UNKNOWN`, not treated as `0` or `UNSUITABLE`.

---

### Scenario 10: Outside Recommended Sowing Window
- **Input Condition:** Rice evaluated in December in West Bengal (Outside Kharif window).
- **Expected Engine Behavior:**
  - Land Suitability: `Suitable` (or `Highly Suitable`).
  - Current Sowing Feasibility: `OUTSIDE_WINDOW`.
  - Overall Recommendation: Qualified badge `Outside Sowing Window`, preventing misleading recommendation to sow immediately.

---

### Scenario 11: Severe Temperature Constraint (Hard Limitation)
- **Input Condition:** Mango evaluated in winter temperature of 2°C (Lethal frost boundary).
- **Expected Engine Behavior:**
  - Limitation Engine flags `HARD_CONSTRAINT` on temperature.
  - Suitability Index capped to `< 10/100`.
  - Suitability Level: `Not Suitable`.
  - Explanation explicitly states: `Lethal low temperature constraint (2.0°C below minimum absolute threshold 18.0°C)`.

---

### Scenario 12: High ML Probability + Severe Agronomic Constraint
- **Input Condition:** Synthetic input where ML model outputs 98% probability for Rice, but field temperature is 45°C (Lethal heat stress).
- **Expected Engine Behavior:**
  - Land Suitability: `Not Suitable`.
  - ML Evidence: `98% Probability`.
  - Explanation states: `ML model identifies learned feature pattern match (98%), but current environmental temperature violates absolute agronomic survival limit.`
  - Severe agronomic constraint overrides ML ranking.

---

### Scenario 13 & 14: Catalogue-Only vs ML-Supported Crops
- **Catalogue-Only Crop (e.g., Mustard):**
  - UI displays: `ML SUPPORT: Catalogue-only assessment`.
  - No synthetic ML probability generated.
- **ML-Supported Crop (e.g., Rice):**
  - UI displays: `ML SUPPORT: Available (Probability: 94%)`.

---

### Scenario 15 & 16: Empty Results & API Failure Handling
- **API Failure (HTTP 500 / 503):** Frontend catches error cleanly, renders user-friendly error banner with `Retry Analysis` action.
- **Empty Recommendations:** Controlled empty state rendered explaining no crops met filter criteria.

---

### Scenario 17 & 18: Partial API Response & Schema Validation
- Pydantic response schema enforces strict structure.
- TypeScript interfaces enforce runtime validation.

---

### Scenario 19: Crop Image Identity & Consistency Test
- Automated test verifies that every crop profile (`cropId`) resolves to a valid, existing image asset matching the crop identity:
  - `mango` -> Mango orchard image (NOT cereal field).
  - `rice` -> Rice paddy image.
  - `maize` -> Maize field image.
  - `wheat` -> Wheat field image.
  - `cotton` -> Cotton field image.

---

### Scenario 20: Frontend Null Value Safety (.toFixed Protection)
- All numeric formatting wrapped in safe helper functions (`safeFormatScore`, `safeFormatTemp`, etc.).
- Never renders `undefined.toFixed()`, `null.toFixed()`, or `NaN`.
- Missing values render explicit placeholders (`—` or `Needs test`) rather than defaulting to `0`.

---

## 3. Automated Test Execution Commands

Backend Pytest suite:
```bash
pytest backend/tests/test_crop_recommendation.py -v
```

Frontend TypeScript build & lint check:
```bash
cd frontend && npm run build
```

---
*Validation Specification Approved for AgriNexus-AI Test Infrastructure.*
