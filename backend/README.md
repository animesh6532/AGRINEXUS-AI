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

## Contributing

This is a university final-year project. Please consult with the project maintainer before making significant changes.

## 📜 License

University Educational Use Only.
