# AgriNexus-AI Backend

This is the FastAPI backend implementation for **AgriNexus-AI**, integrating 7 Frozen Machine Learning model artifacts across 8 inference services, Live OpenCV Computer Vision quality gates, Market Intelligence, Weather Intelligence, and Crop Calendar services.

---

## 🌟 Architecture & Features

### 1. 🤖 ML Models & Inference Services (8 Services across 7 Frozen Artifacts)
1. **Crop Recommendation**: `crop_recommendation.pkl` (ExtraTreesClassifier on raw N, P, K, temp, humidity, pH, rainfall features + IsolationForest anomaly check).
2. **Plant Disease Detection**: `disease_detection.pt` (ResNet18 PyTorch model with optional Grad-CAM visual heatmaps).
3. **Fertilizer Recommendation**: `fertilizer_recommendation.pkl` (scikit-learn pipeline + LightGBM classifier with Western Maharashtra scope warning).
4. **Irrigation Prediction**: `irrigation_prediction.pkl` (Soil Water Content prediction + persistence baseline benchmark comparison).
5. **Visual Pest Classification**: `pest_prediction.pkl` (PyTorch MobileNetV3 Small 102-class single-insect classifier).
6. **Environmental Pest Risk**: `pest_prediction.pkl` (scikit-learn RandomForest environmental outbreak risk model).
7. **Soil Organic Carbon Analysis**: `soil_analysis.pkl` (Soil Organic Carbon prediction with 95% residual confidence intervals).
8. **Crop Yield Prediction**: `yield_prediction.pkl` (XGBoost crop yield model with prediction intervals).

### 2. 📷 Live OpenCV Computer Vision
- Single-frame quality check (blur detection via Laplacian variance, exposure validation via mean brightness).
- Temporal prediction smoothing over rolling frames.
- Frame skipping for blurry / poorly lit frames.
- High-throughput REST & WebSocket endpoints (`/disease/live`, `/pest/live`, `/ws/disease/live`, `/ws/pest/live`).

### 3. 📈 Market Intelligence & Forecasting
- Real-time market observations from Government of India APIs (data.gov.in / AGMARKNET).
- SQLite database storage and time-series forecasting (ETS, ARIMA, Moving Average).
- Actionable market trend signals.

### 4. ☀️ Weather Intelligence
- Open-Meteo current weather and 7-day forecast data.
- Rule-based agricultural disruption signals and actionable insights.

### 5. 📅 Crop Calendar Module
- Sowing windows, crop durations, growth stage schedules, and upcoming field activities.
- Bundled reference dataset with support for external provider integration.

---

## 📁 Project Structure

```
backend/
├── app/
│   ├── main.py                     # FastAPI application entry point & lifespan context manager
│   ├── api/
│   │   ├── market.py               # Market API endpoints
│   │   ├── weather.py              # Weather API endpoints
│   │   ├── crop_calendar.py        # Crop calendar API endpoints
│   │   └── v1/
│   │       ├── router.py           # Unified v1 ML & CV router
│   │       ├── crop.py             # Crop recommendation endpoint
│   │       ├── disease.py          # Disease detection endpoint
│   │       ├── fertilizer.py       # Fertilizer recommendation endpoint
│   │       ├── irrigation.py       # Irrigation prediction endpoint
│   │       ├── pest.py             # Visual pest & environmental risk endpoints
│   │       ├── soil.py             # Soil analysis endpoint
│   │       ├── yield_api.py        # Yield prediction endpoint
│   │       ├── live.py             # OpenCV Live REST & WebSocket endpoints
│   │       └── health.py           # ML Model readiness status endpoint
│   ├── services/
│   │   ├── model_registry.py       # Singleton ML model registry and inference logic
│   │   ├── cv_service.py           # OpenCV frame inspection & PyTorch preprocessing
│   │   ├── gradcam.py              # PyTorch Grad-CAM heatmap generator
│   │   ├── temporal_smoother.py    # Live stream prediction smoother
│   │   ├── market_service.py       # Market API client
│   │   ├── weather_service.py      # Weather API client
│   │   └── crop_calendar_service.py# Crop calendar service
│   ├── database/                   # SQLite database models and repository
│   └── core/                       # Application configuration & logging
├── models/                         # Frozen ML model artifacts directory (.pkl, .pt)
├── tests/                          # Automated PyTest integration test suite
├── requirements.txt                # Python dependencies (scikit-learn 1.7.1, Python 3.13)
└── README.md
```

---

## 🚀 Quick Setup Instructions

### 1. Prerequisites
- Python 3.13
- Virtual Environment (`.venv`)

### 2. Environment Setup & Dependency Installation

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Linux/macOS:
source .venv/bin/activate

# Install compatible dependencies (includes scikit-learn==1.7.1)
pip install -r requirements.txt
```

### 3. Model Placement
Ensure all 7 frozen artifacts exist in `models/` or `Notebook/models/`:
- `crop_recommendation.pkl`
- `disease_detection.pt`
- `fertilizer_recommendation.pkl`
- `irrigation_prediction.pkl`
- `pest_prediction.pkl`
- `soil_analysis.pkl`
- `yield_prediction.pkl`

---

## 🏃 Running the Application

### Development Mode (with Live Reload)
```bash
python -m uvicorn app.main:app --reload
```

### Production Mode
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

## 🔗 Key Endpoints & Swagger UI

- **Interactive Swagger Docs**: `http://127.0.0.1:8000/docs`
- **ReDoc UI**: `http://127.0.0.1:8000/redoc`
- **Process Liveness Health**: `GET http://127.0.0.1:8000/health`
- **ML Model Readiness Health**: `GET http://127.0.0.1:8000/api/v1/models/health`

### 🧪 ML & Computer Vision Endpoints (`/api/v1`)
- `POST /api/v1/crop/recommend` — Crop recommendation on raw soil/climate features
- `POST /api/v1/disease/predict` — Image plant disease detection (+ optional Grad-CAM)
- `POST /api/v1/fertilizer/recommend` — Commercial fertilizer formulation recommendation
- `POST /api/v1/irrigation/predict` — Soil Water Content prediction & persistence baseline
- `POST /api/v1/pest/predict` — Visual pest classification
- `POST /api/v1/pest/risk` — Environmental pest outbreak risk level
- `POST /api/v1/soil/analyze` — Soil organic carbon estimation with 95% confidence intervals
- `POST /api/v1/yield/predict` — Crop yield prediction
- `POST /api/v1/disease/live` — Live video frame disease detection
- `POST /api/v1/pest/live` — Live video frame pest recognition
- `WebSocket /ws/disease/live` — Continuous live camera disease stream
- `WebSocket /ws/pest/live` — Continuous live camera pest stream

---

## 🧪 Testing

Run code compilation check:
```bash
python -m compileall -q app tests
```

Run test suite with pytest:
```bash
pytest -q
```

---

## Testing

Run the test suite with pytest:

```bash
pytest tests/ -v
```

To run tests with coverage:
```bash
pytest tests/ --cov=app --cov-report=html
```

## Configuration Options

Edit `.env` to customize:

```env
# API Settings
DATA_GOV_API_KEY=your_api_key_here
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=False

# Forecasting Settings
DEFAULT_FORECAST_HORIZON_DAYS=7
MIN_HISTORICAL_DAYS_REQUIRED=30

# Database Settings
DATABASE_URL=sqlite:///./data/market/market_data.db

# Cache Settings
CACHE_TTL_SECONDS=300
```

## Data Sources

Primary data source: [data.gov.in AGMARKNET resource](https://data.gov.in/catalog/daily-prices-various-commodities-various-markets-mandi)
- Resource ID: `9ef84268-d588-465a-a308-a864a43d0070`
- Provides daily market prices for various commodities across Indian markets
- Includes state, district, market, commodity, variety, grade, and price fields

## Forecasting Models

### Naive Model
- Uses the last observed value for all future predictions
- Simple baseline for comparison

### Moving Average Model
- Average of the last N observations (default N=7)
- Good for smoothing short-term fluctuations

### Exponential Smoothing (ETS)
- Holt-Winters method with trend and optional seasonality
- Handles trends and seasonality in data
- Provides confidence intervals

### ARIMA Model
- AutoRegressive Integrated Moving Average
- Captures autocorrelations in time series
- Good for data with trends and seasonality
- Provides confidence intervals

## Security

- API keys are stored in environment variables, never hardcoded
- `.env` file is included in `.gitignore` to prevent accidental commits
- No sensitive data is returned in API responses
- Error messages don't expose internal details

## Limitations

- Depends on availability and reliability of Government of India APIs
- Historical data availability may be limited by API constraints
- Forecasting accuracy depends on data quality and market stability
- Models are simplified for university project scope
- Real-world deployment would require additional robustness and monitoring

## Crop Calendar Module

The Crop Calendar backend provides agricultural calendar information for
supported crops: sowing windows, crop duration, growth stages with
durations and reference activities, derived stage schedules from a
sowing date, the current growth stage, an approximate harvest window and
upcoming activities.

### Data Source and Provenance

- The verified external crop-calendar provider is **Spora**
  (`SPORA_API_BASE_URL=https://api.spora.engineer`,
  endpoint `GET /harvest/{location}` with a lowercase country slug such
  as `india`, authenticated with the backend-only `X-Api-Key` header).
  When `SPORA_API_KEY` is set, Spora (`data_source: "spora_harvest_api"`,
  `is_reference_data: false`) is the active source.
- When the key is unset - or when the provider is unreachable, errors,
  returns malformed data, or lacks the requested crop - the module serves
  a small, generalised, **non-authoritative reference dataset** bundled at
  `app/services/crop_calendar_reference_data.py`
  (India-generic; crops: rice, wheat, maize, cotton).
- Every response built from it is explicitly labelled with
  `is_reference_data: true`, `data_source: "reference_dataset"` and
  `region_scope: "india_generic"` (plus `fallback_used`/`fallback_reason`
  when it substitutes for a failed provider call). **Static reference data
  is never presented as an authoritative or real-time prediction.**
- A verified external provider can be plugged in through the optional
  client (`ExternalCropCalendarClient`) without changing the API,
  schema, or intelligence layers.

### API Endpoints

All Crop Calendar endpoints are prefixed with `/api/crop-calendar`.

| Endpoint | Description |
| --- | --- |
| `GET /api/crop-calendar` | Crop catalogue (crops, aliases, seasons, durations) |
| `GET /api/crop-calendar/health` | Module health + data-source configuration status |
| `GET /api/crop-calendar/{crop}` | Static/reference calendar for a crop and season |
| `GET /api/crop-calendar/{crop}/schedule` | Stage schedule derived from a sowing date |

### Example Requests

```bash
# Crop catalogue
curl "http://localhost:8000/api/crop-calendar"

# Static calendar (rice, kharif)
curl "http://localhost:8000/api/crop-calendar/rice?season=kharif&location=West%20Bengal"

# Derived schedule from a sowing date
curl "http://localhost:8000/api/crop-calendar/rice/schedule?sowing_date=2026-06-15&as_of_date=2026-07-01"
```

### Parameters

- **Path**: `crop` - crop name or common alias (e.g. `rice`, `paddy`),
  case-insensitive.
- `season` (optional) - `kharif`, `rabi` or `zaid`. On the static
  endpoint it defaults to the crop's primary season; on the schedule
  endpoint it is inferred from the crop's sowing windows and then from
  the sowing month.
- `sowing_date` (required on `/schedule`) - ISO date
  (`YYYY-MM-DD`); malformed or impossible dates return `422`.
- `as_of_date` (optional on `/schedule`) - reference date for
  current-stage determination; defaults to today (server date).
- `location` (optional) - informational label echoed in the response.
  The active data source is region-general, so location is NOT used to
  select or validate data.

### Response Structure (schedule endpoint, abridged)

```json
{
  "crop": "rice",
  "season": "kharif",
  "season_source": "inferred_from_sowing_window",
  "sowing_window": {"start": "06-01", "end": "07-15"},
  "crop_duration_days": 135,
  "growth_stages": [{"stage": "tillering", "duration_days": 30, "activities": ["..."]}],
  "sowing_date": "2026-06-15",
  "as_of_date": "2026-07-01",
  "scheduled_growth_stages": [
    {"stage": "nursery_sowing", "start_date": "2026-06-15", "end_date": "2026-07-09",
     "duration_days": 25, "activities": ["..."], "is_current": true}
  ],
  "current_stage": "nursery_sowing",
  "current_stage_progress_percent": 68.0,
  "next_stage": "transplanting",
  "harvest_window": {"start_date": "2026-10-17", "end_date": "2026-11-06"},
  "upcoming_activities": [{"stage": "nursery_sowing", "activities": ["..."]}],
  "sowing_window_compliant": true,
  "warnings": [],
  "data_source": "reference_dataset",
  "is_reference_data": true,
  "data_timestamp": "2026-09-19T10:30:00+00:00"
}
```

### Error Handling

| Status | Meaning |
| --- | --- |
| 400 | Invalid parameters (unsupported season for the crop, invalid season name, over-long location) |
| 404 | Unsupported crop (see the catalogue for supported crops) |
| 422 | Request validation failures (missing `sowing_date`, malformed dates) |
| 500 | Unexpected internal errors (no stack trace exposed) |
| 502 | External provider failure (only possible when a provider is configured) |

### Environment Variables

```env
# Verified external crop-calendar provider: Spora.
# Docs: https://spora.engineer/docs
#   Base URL: https://api.spora.engineer  (documented default)
#   Auth:     "X-Api-Key" request header (key alone is sufficient)
#   Endpoint: GET /harvest/{location} (lowercase country slug, e.g. india)
# When SPORA_API_KEY is unset the bundled reference dataset is used.
# When it is set, the Spora /harvest calendar is preferred and the
# reference dataset remains as labelled fallback.
SPORA_API_BASE_URL=https://api.spora.engineer
SPORA_API_KEY=your_spora_api_key_here
# CROP_CALENDAR_FALLBACK_TO_REFERENCE_DATA=True
```

- The API key is **backend-only**: sent as an `X-Api-Key` header, never
  logged, never included in URLs, and never returned by any endpoint
  (health reports only booleans `external_provider_configured` /
  `external_api_key_configured` plus optional `external_connectivity`).
- When `SPORA_API_KEY` is set, it becomes required for the external
  provider and Spora (`spora_harvest_api`) replaces the reference
  dataset as the active source, with the reference dataset kept as
  explicitly labelled fallback (`fallback_used`/`fallback_reason`).
- The provider returns one annual planting/harvest window per crop (no
  kharif/rabi/zaid splits, no growth-stage breakdown). Responses carry
  `notes` explaining derivation/provenance; season-specific provider
  data is never fabricated.

### Limitations

- The reference dataset is approximate, generalised (India-generic)
  data for demonstration/testing - NOT authoritative agronomy, NOT
  variety-, soil-, or weather-specific.
- Stage dates are deterministic date arithmetic from the supplied
  sowing date; they are not weather-adjusted predictions (weather-aware
  adjustments are intentionally out of scope for now).
- Location is informational only in reference mode; with Spora active the
  location slug selects the provider calendar (`/harvest/india` by
  default). Region-specific calendars otherwise require a verified
  external provider.
- The catalogue reflects the bundled dataset even when an external
  provider is configured.
- Spora publishes one annual planting/harvest window per crop (no
  kharif/rabi/zaid splits, no stage breakdown); the module reports a
  single aggregate growing-period stage and discloses this in `notes`.

### Testing

- Unit/integration tests use mocks only (`urllib.request.urlopen` is
  patched; fake services stand in for the provider) and never require a
  real `SPORA_API_KEY` or network access:
  `python -m pytest tests/test_crop_calendar_service.py`
  tests/test_crop_calendar_api.py
  tests/test_crop_calendar_intelligence.py -q`.
- Live Spora verification is a separate explicit step using
  `backend/.env` (never printed, logged, or committed).

## Risk & Opportunity Analysis Module

**Risk & Opportunity Analysis is a deterministic decision-intelligence
layer and is not a machine-learning model.** It sits AFTER the Context /
Decision Engine and BEFORE the future Smart Alerts, Personalized Action
Plan and AI Farming Assistant layers. It never trains, replaces or
reimplements any of the project's 7 ML models, introduces no new
external API or API key, and never fabricates weather data, market
prices, crop stages, ML predictions, disease/pest probabilities, yield
values, soil measurements or confidence scores - unavailable inputs are
REPORTED as data-quality notices instead of being substituted.

### Architecture

```text
Weather Intelligence
        \
Market Forecast
         \
Crop Calendar
          \
Farm Context ---------> Decision Engine
          /
Friend's ML outputs /
                    v
        Risk & Opportunity Analysis   (this module)
                    v
              Smart Alerts                (future)
                    v
        Personalized Action Plan          (future)
                    v
          AI Farming Assistant            (future)
```

The module consumes the SAME normalized contracts the project already
exposes (`FarmContext`, `DecisionResponse`, the standardized
`MLPrediction` contract) - it does not duplicate the Decision Engine,
does not redefine upstream schemas, and does not recompute conditions
the Decision Engine already identified (upstream priority/confidence
are reused with attribution).

### Files

| File | Role |
| --- | --- |
| `app/schemas/risk_opportunity.py` | Input context, Risk/Opportunity objects, data-quality/conflict notices, responses |
| `app/intelligence/risk_opportunity.py` | Deterministic rule engine: rules, multi-source consolidation, severity/priority/confidence grading |
| `app/services/risk_opportunity_service.py` | Reusable service layer (validation, health, Decision Engine adapters) |
| `app/api/risk_opportunity.py` | FastAPI router (`/api/risk-opportunity`) |

### Inputs

`RiskOpportunityContext`:

- `farm_context` (required) - normalized farm context: crop, location,
  sowing date, as-of date, weather/market/crop-calendar signals,
  standardized ML predictions (all 7 contracts), optional
  `data_freshness` timestamps.
- `decision_engine_output` (optional) - Decision Engine response for
  the same context; consumed and attributed, never recomputed. When
  absent, the analysis runs on direct signals and reports the absence.
- `source_metadata` (optional) - free-form source metadata.

### Outputs

`RiskOpportunityResponse`:

- `status` - reuses the documented context-status vocabulary
  (`complete_context`, `partial_context`, `insufficient_context`,
  `conflicting_signals`).
- `risks` / `opportunities` - structured, consolidated, sorted
  deterministically (risks by severity then priority; opportunities by
  priority then confidence).
- `data_quality` - deterministic assessment (same completeness/staleness
  methodology as the Decision Engine).
- `data_quality_notices` - what was skipped and why (missing data,
  stale data, unavailable models, missing fields, insufficient
  baseline).
- `conflict_notices` - conflicting upstream signals, never silently
  resolved, with `detected_by` attribution.
- `summary` - counts, per-category counts, highest severity/priority.
- `engine_version`, `ruleset_version`, `analysis_timestamp`,
  `total_risks`, `total_opportunities`.

Each risk carries: `id`, `category`, `title`, `description`,
`severity`, `priority`, `status` (`active`/`monitoring`), `confidence`,
`numerical_confidence`, `confidence_source`, `confidence_rationale`,
`affected_crop`, `affected_stage`, `evidence` (traceable signals),
`contributing_sources`, `contributing_signals`, `reasoning`,
`recommended_follow_up`, `detected_at`, `valid_until`.

Each opportunity carries: `id`, `category`, `title`, `description`,
`priority`, `status`, `confidence` (+ numeric/source/rationale),
`affected_crop`, `affected_stage`, `evidence`,
`contributing_sources`, `contributing_signals`, `reasoning`,
`suggested_action`, `time_window`, `detected_at`.

### Risk categories

`weather`, `irrigation`, `disease`, `pest`, `soil`, `fertilizer`,
`market`, `yield`, `crop_stage`, `data_quality`, `system`.

### Opportunity categories

`weather`, `market`, `irrigation`, `crop_stage`, `disease`, `pest`,
`fertilizer`, `yield`, `harvest`, `data`.

### Severity logic (deterministic, documented - NOT calibrated probabilities)

Inputs: `n` = number of independent corroborating sources (weather,
market, ML models; the crop calendar supplies context and the Decision
Engine supplies attribution, neither counts as corroboration);
`elevated` = a strong single signal (heavy rainfall, extreme heat,
frost, strong wind, severe-weather indicator, model probability >= 0.6,
market move >= 3%); `sensitive` = sensitive growth stage; `ts` =
time-sensitive; `severe` = severe-weather indicator; `upstream` =
priority reported by the Decision Engine for the same condition
(attributed, never recomputed).

1. **CRITICAL**: `n >= 2` and `upstream == critical` (attributed)
2. **CRITICAL**: severe-weather indicator in a sensitive stage
3. **CRITICAL**: `n >= 3` and (`sensitive` or `ts`)
4. **CRITICAL**: `n >= 2` and `elevated` and `ts`
5. **HIGH**: `n >= 2` and (`elevated` or `sensitive` or `ts`)
6. **HIGH**: `n == 1` and `elevated` and `sensitive`
7. **MEDIUM**: `n >= 2`
8. **MEDIUM**: `elevated`
9. **LOW**: otherwise (single, low-impact signal)

These levels are deterministic rules, not statistically calibrated
probabilities.

### Priority logic (deterministic)

Risks:

- **CRITICAL**: severity CRITICAL
- **HIGH**: severity HIGH and (time-sensitive or sensitive stage)
- **MEDIUM**: severity HIGH without urgency, or severity MEDIUM with an
  actionable follow-up
- **LOW**: everything else

Opportunities:

- **HIGH**: `n >= 2` and bound to a specific time window
- **MEDIUM**: `n >= 2`, or bound to a time window
- **LOW**: otherwise

### Confidence handling (never fabricated)

1. A numeric confidence already produced upstream is REUSED verbatim
   with attribution: first the Decision Engine decision confidence for
   the same condition (`confidence_source: decision_engine`), otherwise
   the ML model's own reported probability/confidence when the model is
   the item's only corroborating source (`confidence_source: ml_model`).
2. Otherwise, when `n >= 2` independent sources agree, the documented
   deterministic method (identical to the Decision Engine's) is applied:
   `0.5 + 0.1` per source beyond the second, `+0.1` when an ML model
   reported a probability, capped at `0.9`
   (`confidence_source: risk_opportunity`).
3. Otherwise `confidence = insufficient_evidence` and
   `numerical_confidence = null`.

Category mapping: `>= 0.75` high, `>= 0.50` medium, else low. Every
value carries a `confidence_rationale` explaining the derivation.
Confidence is never invented - "three signals agree" never becomes an
arbitrary percentage.

### Missing-data behavior

Rules only fire on supplied data. When a source is missing the module:

- skips the affected rule groups (no weather data -> no weather risk;
  no market data -> no market risk/opportunity; no disease model ->
  no disease status claimed; no crop stage -> no stage-specific rules),
- emits a `data_quality` notice stating WHAT was skipped and WHY
  (e.g. "Crop calendar data was unavailable; crop-stage-specific risk
  and opportunity analysis was skipped (no stage was assumed)."),
- reports unavailable/errored ML models with an
  `unavailable_model` notice ("its signal was not fabricated").

### Stale-data behavior

Staleness uses the Decision Engine's existing
`STALENESS_DAYS_THRESHOLD` (3 days) applied to caller-provided
`data_freshness` timestamps only. Sources without a timestamp are never
marked stale. When a contributing source is stale: a `stale_data`
notice is emitted, dependent items get `status: monitoring`, and their
confidence category is downgraded one step (the numeric value is not
altered).

### Conflict handling

Conflicts are surfaced explicitly and never silently resolved:

- `rainfall_vs_irrigation_need` - weather forecasts rainfall while the
  irrigation model reports irrigation need for the same window (the
  water-stress rule stays silent and the conflict path reports the
  disagreement instead).
- `market_vs_yield` - the yield model's comparative signal points the
  opposite way from the market trend.

Every conflict becomes ONE consolidated `data_quality` risk
("Conflicting Signals Detected") plus a `conflict_notice` carrying
`conflicting_signals`, `unresolved_reason`, `recommended_action` and
`detected_by` (`risk_opportunity`, or `decision_engine` when the
Decision Engine already reported the same conflict - never duplicated).

### Multi-source correlation & duplicate suppression

Related signals describing the SAME underlying condition are merged
into ONE item with combined evidence/sources (one consolidation key per
condition), e.g. high humidity + rain forecast + elevated disease
model + susceptible stage -> a single "Elevated Disease Pressure" risk
with all evidence attached - not four separate alerts.

### API Endpoints

All Risk & Opportunity endpoints are prefixed with
`/api/risk-opportunity`:

| Endpoint | Description |
| --- | --- |
| `GET /api/risk-opportunity/health` | Service status, version, ruleset version, supported categories, dependency readiness (no secrets) |
| `POST /api/risk-opportunity/analyze` | Run the deterministic analysis over a normalized context |
| `GET /api/risk-opportunity/categories` | Documented vocabulary: categories, severity/priority levels, conflict types, data-quality issue types |

Error handling: `400` invalid request caught at the service layer,
`422` request body validation failures (FastAPI/Pydantic), `500`
unexpected internal errors (no stack trace exposed).

### Example Request

```bash
curl -X POST "http://localhost:8000/api/risk-opportunity/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "farm_context": {
      "crop": "rice",
      "location": "West Bengal",
      "sowing_date": "2026-06-15",
      "as_of_date": "2026-09-19",
      "current_growth_stage": "flowering",
      "weather_context": {
        "is_weather_data_available": true,
        "precipitation_probability": 85.0,
        "forecast_precipitation_sum": 60.0,
        "current_humidity": 90.0,
        "temperature_max_forecast": 30.0,
        "temperature_min_forecast": 20.0,
        "wind_speed_max_forecast": 10.0,
        "forecast_horizon_days": 7
      },
      "ml_predictions": [
        {
          "model_name": "disease_detection",
          "prediction": "rice blast",
          "probability": 0.82,
          "status": "available"
        }
      ]
    }
  }'
```

### Example Response (abridged)

```json
{
  "status": "partial_context",
  "risks": [
    {
      "id": "ro-risk-1c8d00b0d9b3",
      "category": "disease",
      "title": "Elevated Disease Pressure",
      "severity": "high",
      "priority": "high",
      "status": "active",
      "confidence": "medium",
      "numerical_confidence": 0.6,
      "confidence_source": "risk_opportunity",
      "confidence_rationale": "2 independent sources agree plus a model-reported probability; deterministic method documented in this module (base 0.5, +0.1 per extra source, cap 0.9).",
      "affected_crop": "rice",
      "affected_stage": "flowering",
      "evidence": [
        {"signal": "disease_model_elevated_probability", "source": "disease_detection", "description": "Disease model reports elevated probability (0.82) for rice blast", "value": 0.82},
        {"signal": "high_humidity", "source": "weather", "description": "Current humidity: 90%", "value": 90.0}
      ],
      "contributing_sources": [
        {"source": "disease_detection", "source_type": "ml_model", "detail": "Disease Detection ML prediction (diagnosis source; friend's ML layer)"},
        {"source": "weather", "source_type": "external_data", "detail": "Weather Intelligence signals (current/forecast)"}
      ],
      "reasoning": "The disease detection model reports elevated probability (0.82) for rice blast and the weather module reports conditions (high_humidity, ...) favourable for disease development. ...",
      "recommended_follow_up": "Increase scouting frequency for disease symptoms during the flowering stage.",
      "detected_at": "2026-09-19T10:30:00+00:00",
      "valid_until": "2026-09-26T10:30:00+00:00"
    }
  ],
  "opportunities": [],
  "data_quality": {"status": "partial_context", "completeness_percent": 30.0, "missing_sources": ["market"], "stale_sources": [], "conflicts": [], "unavailable_ml_models": [], "missing_critical_fields": []},
  "data_quality_notices": [
    {"type": "missing_data", "source": "market", "message": "Market data was unavailable; market risks and opportunities were skipped (no prices were substituted)."}
  ],
  "conflict_notices": [],
  "summary": {"risk_count": 2, "opportunity_count": 0, "data_quality_notice_count": 2, "conflict_notice_count": 0},
  "engine_version": "1.0.0",
  "ruleset_version": "1.0.0",
  "analysis_timestamp": "2026-09-19T10:30:00+00:00",
  "total_risks": 2,
  "total_opportunities": 0
}
```

### Testing

Deterministic unit/API tests with no live external APIs and no ML
model execution:

```bash
python -m pytest tests/test_risk_opportunity.py -q
```

Covers: health/categories/analyze endpoints, empty and complete
inputs, weather/irrigation/disease/pest/market/yield/fertilizer/crop-stage
rules, multi-source correlation, duplicate suppression, conflict
detection, missing/stale data handling, severity/priority/confidence
ladders, evidence traceability, API validation errors and existing
backend regression.



## Smart Alerts Module

**Smart Alerts is a deterministic, explainable alert-intelligence
layer AFTER Risk & Opportunity Analysis and BEFORE the frontend / AI
Farming Assistant.** It converts important risks, opportunities,
conflicts and data-quality conditions from the existing Risk &
Opportunity system into concise, traceable alerts. It is NOT another
ML model: no external API calls, no ML calls, no invented facts,
confidence, recommendations or validity periods.

### Architecture

```text
External Data -> Weather / Market / Crop Calendar
  -> Friend's 7 ML Predictions -> Context/Decision Engine
  -> Risk & Opportunity Analysis -> SMART ALERTS
  -> Frontend / AI Farming Assistant
```

### Files

| File | Role |
| --- | --- |
| `app/schemas/smart_alert.py` | Alert/preference/request/response schemas (reuses `SupportingSignal`, `ContributingSource`, `RiskOpportunityResponse`, `DecisionStatus`) |
| `app/intelligence/smart_alert.py` | Deterministic filtering, dedupe, sorting, message generation |
| `app/services/smart_alert_service.py` | DI service (health, generate, rules) |
| `app/api/smart_alert.py` | `POST /api/smart-alerts/generate`, `GET /api/smart-alerts/health`, `GET /api/smart-alerts/rules` |
| `tests/test_smart_alert.py` | 22 deterministic tests, no external/ML calls |

### Alert priority rules (deterministic)

- Risks: CRITICAL/HIGH always alert; MEDIUM alerts only when actionable (recommended follow-up, `valid_until`, or time sensitivity); LOW suppressed.
- Opportunities: HIGH always alert; MEDIUM alerts only with suggested action or time window; LOW suppressed.
- Conflicts: alert when important/unresolved (recommended action or unresolved reason present); empty boilerplate suppressed.
- Data quality: alert when material (`affected_analysis` non-empty or type in missing_data/stale_data/unavailable_model); minor/informational suppressed.
- `min_priority` / `include_*` preferences filter further; `max_alerts` truncation NEVER drops CRITICAL alerts.

### Deduplication

Stable SHA-256 over `alert_type | source_id | category | crop | stage`.
Repeated identical upstream signals share one alert (first wins).
Never uses Python `hash()`.

### Traceability

Every alert preserves `source_id`/`source_type`, evidence,
contributing sources/signals, reasoning, `valid_until`/`time_window`,
recommended action, crop and stage. Messages are concise and derived
only from upstream fields.

### API Endpoints

| Endpoint | Description |
| --- | --- |
| `POST /api/smart-alerts/generate` | Generate alerts from a `RiskOpportunityResponse` + preferences |
| `GET /api/smart-alerts/health` | Service health, version, ruleset version |
| `GET /api/smart-alerts/rules` | Active deterministic rules and ordering |

No new external API key is required; actual notification delivery
(SMS/push/email) is out of scope for this layer.

### Testing

```bash
python -m pytest tests/test_smart_alert.py -q
```

## Personalized Action Plan

```text
External Data -> Weather / Market / Crop Calendar
  -> Friend's 7 ML Predictions -> Context/Decision Engine
  -> Risk & Opportunity Analysis -> Smart Alerts
  -> PERSONALIZED ACTION PLAN -> AI Farming Assistant
```

Purpose: convert current farm intelligence (Decision Engine output, Risk &
Opportunity analysis, Smart Alerts) plus FarmContext/farmer context into a
prioritized, explainable, farmer-specific sequence of concrete actions.

| File | Role |
| --- | --- |
| `app/schemas/action_plan.py` | Action/preference/request/response schemas (reuses FarmContext, DecisionResponse, RiskOpportunityResponse, SmartAlertResponse, SupportingSignal, ContributingSource) |
| `app/intelligence/action_plan.py` | Deterministic conversion, personalization, dedupe, sorting |
| `app/services/action_plan_service.py` | DI service (health, generate, rules) |
| `app/api/action_plan.py` | `POST /api/action-plan/generate`, `GET /api/action-plan/health`, `GET /api/action-plan/categories` |
| `tests/test_action_plan.py` | 13 deterministic tests, no external/ML calls |

Rules: NOT an ML model; no external/weather/market/ML calls; never
fabricates facts, confidence, dosages, or validity. CRITICAL/HIGH always
act; MEDIUM acts only when actionable; LOW suppressed; CRITICAL never
removed by `max_actions`. Conflicts give `needs_review` actions (never
silently resolved); data-quality notices preserved verbatim, never
actionized; expired items never produce active actions. Every action keeps
`source_id`/`source_type`, evidence, contributing sources/signals,
reasoning, `valid_until`/`time_window`. Dedupe key is stable SHA-256 over
`action_type|category|event|crop|stage`.

| Endpoint | Description |
| --- | --- |
| `POST /api/action-plan/generate` | Generate plan from farm/decision/risk/alert context + preferences |
| `GET /api/action-plan/health` | Service health, version, ruleset version |
| `GET /api/action-plan/categories` | Action-type vocabulary and ordering |

```bash
python -m pytest tests/test_action_plan.py -q -p no:warnings
```

Limitations: orchestrates existing intelligence only; cannot invent
agronomic facts. Time windows reuse upstream values or documented coarse
buckets (immediately/within 6 hours/today/within 24 hours/next 2 days).

---

## 🌾 AI Farming Assistant / Farming Chatbot

```text
External Data -> Weather / Market / Crop Calendar
  -> Friend's 7 ML Predictions -> Decision Engine
  -> Risk & Opportunity Analysis -> Smart Alerts
  -> Personalized Action Plan
  -> AI FARMING ASSISTANT
  -> Farmer
```

### Purpose & Scope
The **AI Farming Assistant** is the final conversational layer of AgriNexus-AI. It enables farmers to communicate naturally with the platform, ask general agricultural questions, and inquire about their dynamic farm situation without requiring an external LLM API in V1.

- **Farming-Only Scope**: Handles crops, soil, fertilizer, irrigation, pests, diseases, farm operations, harvest, and agro-markets. Non-agricultural inquiries ("tell me a joke") are politely redirected.
- **Not an ML Model**: Does not retrain or replace any ML model, nor duplicate decision engine logic.
- **Zero Hallucination**: Never fabricates pesticide dosages, fertilizer quantities, weather, or market prices. Returns a grounded fallback when knowledge is insufficient.

### Hybrid Routing Architecture
Incoming queries are classified into two distinct operational flows:

```text
                        FARMER
                           │
                           ▼
                ┌────────────────────┐
                │ AI FARMING         │
                │ ASSISTANT          │
                └─────────┬──────────┘
                          │
                    Question Router
                          │
              ┌───────────┴────────────┐
              │                        │
              ▼                        ▼
      STATIC KNOWLEDGE          DYNAMIC FARM QUERY
              │                        │
              ▼                        ▼
       Embedding Search          AGRINEXUS DATA
              │                  (Action Plan / Alerts /
              ▼                   Risks / Decisions /
       10,000+ Q&A                Weather / Markets)
              │                        │
              └───────────┬────────────┘
                          ▼
                    Grounded Answer
                          │
                          ▼
                       FARMER
```

1. **Static Knowledge Routing**: Questions such as *"What is crop rotation?"*, *"What is NPK?"*, *"Why are rice leaves yellow?"*, or *"What causes brown spot in rice?"* route to the semantic vector search engine over the knowledge base.
2. **Dynamic Farm Query Routing**: Questions such as *"What should I do today?"*, *"What are my biggest farm risks?"*, *"Why did I receive this alert?"*, or *"Why should I irrigate today?"* route directly to upstream AGRINEXUS intelligence outputs (Personalized Action Plan, Smart Alerts, Risk & Opportunity, Decision Engine, Weather, Market).

### Farming Assistant Agricultural Knowledge Base & 10,000+ Audit Status

The Farming Assistant utilizes a local, traceable, semantically searchable agricultural knowledge base.

#### 1. Primary Ingested Dataset
- **Dataset Name**: KisanVaani Agriculture Q&A
- **Dataset Source URL**: [https://huggingface.co/datasets/KisanVaani/agriculture-qa-english-only](https://huggingface.co/datasets/KisanVaani/agriculture-qa-english-only)
- **Dataset License**: Apache 2.0 (confirmed from HuggingFace dataset card)
- **Original Source File**: `backend/data/knowledge_base/kisanvaani_agriculture_qa.parquet`
- **Original Row Count**: 22,615 rows
- **Usable Unique Q&A Count**: 2,331 unique records
- **Invalid / Empty Rows**: 0 (all 22,615 rows contained non-empty questions and answers)
- **Duplicate Rows Removed**: 20,284 exact question+answer duplicates removed (the HuggingFace release repeats ~2,225 unique questions across ~10 iterations).
- **Questions with Multiple Distinct Answers**: 110 questions have multiple distinct valid answers in the dataset, all of which are preserved as distinct source records.

#### 2. Normalization & Metadata Policy
- **Normalization**: Handled via `backend/scripts/prepare_kisanvaani_kb.py`. Strips redundant whitespace, collapses tabs/newlines, handles array/list responses by concatenating elements without rewriting or paraphrasing text, preserving exact agronomic terminology.
- **Deduplication Rule**: Exact duplicate pairs `(normalized_question, normalized_answer)` are deduplicated. Different answers to the same question are preserved as separate knowledge entries.
- **Metadata Assignment**:
  - `crop`: Deterministically detected from standard crop ontology (e.g., rice, wheat, maize, cassava, banana, tomato, etc.), else `null`.
  - `crop_stage`: Deterministically detected from standard growth stages (germination, flowering, tillering, etc.), else `null`.
  - `topic`: Deterministically categorized across 17 agronomic topics (`disease_management`, `soil_management`, `pest_management`, `fertilizer`, `irrigation`, `harvesting`, `planting`, `sustainable_agriculture`, etc.) using explicit keyword rules; defaults to `general_farming`.
  - `keywords`: Deterministically derived from text tokens excluding stopwords.
  - `language`: `"en"`
  - `region`: `"global"`
  - `source`: `"KisanVaani Agriculture Q&A"`
  - `source_url`: `"https://huggingface.co/datasets/KisanVaani/agriculture-qa-english-only"`
  - `verified`: `false` (Never marked as verified because AGRINEXUS human agronomic experts have not individually certified each record).

#### 3. Ingestion & Conversion Pipeline
1. **Preparation / Audit**:
   ```bash
   python backend/scripts/prepare_kisanvaani_kb.py
   ```
   Outputs: `backend/data/knowledge_base/kisanvaani_agriculture_qa_agrinexus.json`
2. **Database Ingestion & Vector Indexing**:
   ```bash
   python backend/scripts/ingest_farming_kb.py --file backend/data/knowledge_base/kisanvaani_agriculture_qa_agrinexus.json
   ```

#### 4. Actual Final Database Count & 10,000+ Target Status
- **Current Database Record Count**: 2,340 records (11 sample/expert-verified reference records + 2,329 newly ingested KisanVaani records).
- **10,000+ Target Status**: **NOT MET** (2,340 / 10,000 records).
- **Transparency Statement**: The 10,000+ target is **NOT MET** because the available legitimate source dataset produced only 2,331 usable unique records. In accordance with AGRINEXUS integrity principles, synthetic questions, duplicated records, or artificial modifications were **NOT** fabricated merely to inflate the record count.
- **Recommended Additional Sources to Reach 10,000+**:
  1. `talhakk/agriculture-qa` (HuggingFace: 25,410 rows: 15,000 general agriculture + 10,410 crop-specific QA across 10 major crops).
  2. `liaad/agricultural-data` (HuggingFace: 17,715 agricultural rows).
  The existing ingestion pipeline (`ingest_farming_kb.py`) is modular and ready to ingest either dataset as soon as downloaded.
- **API Status Verification**: Reported transparently by `GET /api/farming-assistant/kb-status` (`is_target_met: false`, `record_count: 2340`, `target_count: 10000`).

### Semantic Search & Local Vector Storage
- **Local Embedding Model**: Uses `sentence-transformers/all-MiniLM-L6-v2` (384-dimensional dense vectors), cached locally. No OpenAI, Gemini, or Ollama API key is required.
- **Fallback Embedder**: If SentenceTransformers cannot be initialized, seamlessly falls back to a Scikit-Learn TF-IDF semantic vectorizer with L2 normalization.
- **Vector Storage**: SQLite persistence (`farming_knowledge_records` table) coupled with an in-memory normalized NumPy matrix for sub-millisecond cosine similarity search (`q_vec @ matrix.T`).
- **Traceability**: Every response includes `sources` with record ID, source organization, topic, crop, and cosine relevance score.
- **Conversation Memory**: Maintains bounded, privacy-conscious session history (default: 10 turns).

### API Endpoints

| Method | Endpoint | Description |
| --- | --- | --- |
| `POST` | `/api/farming-assistant/chat` | Conversational query endpoint with intent routing and grounded answers |
| `GET` | `/api/farming-assistant/health` | Service health, local embedding status, and record count |
| `GET` | `/api/farming-assistant/capabilities` | Supported crops, topics, routing modes, and similarity thresholds |
| `GET` | `/api/farming-assistant/kb-status` | Record count and verification against the 10,000+ requirement |
| `POST` | `/api/farming-assistant/ingest` | Ingest and index a validated Q&A record |

### Configuration (`backend/app/core/config.py`)

| Setting | Default | Description |
| --- | --- | --- |
| `FARMING_ASSISTANT_TOP_K` | `3` | Maximum relevant Q&A records retrieved per query |
| `FARMING_ASSISTANT_SIMILARITY_THRESHOLD` | `0.55` | Minimum cosine similarity required to accept a match |
| `FARMING_ASSISTANT_MAX_CONTEXT` | `5` | Maximum dynamic context items included |
| `FARMING_ASSISTANT_MAX_HISTORY` | `10` | Maximum messages stored per conversation session |
| `FARMING_EMBEDDING_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | Local HuggingFace embedding model |
| `FARMING_KB_PATH` | `data/knowledge_base/farming_kb.db` | Knowledge base storage path |

### Future Optional LLM Integration
For future iterations beyond V1, an LLM (Ollama, Gemini, OpenAI) may be added as an optional presentation layer. If enabled:
- The LLM receives retrieved knowledge and AGRINEXUS structured outputs as strict context.
- The LLM never acts as the source of truth for weather, prices, risks, alerts, or ML predictions.
- No external LLM key is needed for V1.

---

## Contributing

This is a university final-year project. Please consult with the project maintainer before making significant changes.

## 📜 License

University Educational Use Only.
