# AgriNexus-AI Backend

This is the backend implementation for AgriNexus-AI, integrating 7 Frozen ML Model services, Live OpenCV Computer Vision, Market Intelligence, Weather Intelligence, and Crop Calendar services.

## Overview

The Market Forecast backend provides:
- Retrieval of agricultural market price data from Government of India APIs
- Data validation and storage
- Time-series forecasting of market prices
- Market trend analysis and intelligence
- RESTful API for accessing market data and forecasts

## Features

- Fetches real-time market data from data.gov.in (AGMARKNET API)
- Stores market observations in SQLite database
- Implements multiple forecasting models:
  - Naive (last value)
  - Moving Average
  - Exponential Smoothing (ETS/Holt-Winters)
  - ARIMA
- Provides market trend analysis and signals
- Generates actionable insights for farmers and stakeholders
- Secure API key management using environment variables
- Comprehensive test suite
- Interactive API documentation (Swagger UI)

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── api/
│   │   └── market.py        # Market forecast API endpoints
│   │   ├── weather.py       # Weather intelligence API endpoints
│   │   └── crop_calendar.py # Crop calendar API endpoints
│   ├── services/
│   │   ├── market_service.py# Market data service and API client
│   │   ├── weather_service.py# Weather data service (Open-Meteo)
│   │   ├── crop_calendar_service.py# Crop calendar data service
│   │   └── crop_calendar_reference_data.py# Bundled reference dataset
│   ├── forecasting/
│   │   ├─ forecast_service.py# Forecasting service
│   │   └─ model.py          # Forecasting models
│   ├── intelligence/
│   │   ├── market_intelligence.py# Market intelligence layer
│   │   ├── weather_intelligence.py# Weather intelligence layer
│   │   └── crop_calendar_intelligence.py# Crop calendar intelligence
│   ├── schemas/
│   │   ├── market.py         # Pydantic schemas for API
│   │   ├── weather.py        # Pydantic schemas for API
│   │   └── crop_calendar.py  # Pydantic schemas for API
│   ├── database/
│   │   ├─ connection.py     # Database connection
│   │   ├─ models.py         # SQLAlchemy models
│   │   └─ repository.py     # Data access layer
│   ├── core/
│   │   ├─ config.py         # Application configuration
│   │   ├─ logging.py        # Logging configuration
│   │   └─ dependencies.py   # Dependency injection
│   └── __init__.py
├── data/
│   └── market/              # Market data storage (SQLite)
├── tests/                   # Test suite
├── scripts/
│   └─ collect_market_data.py# Data collection script
├── requirements.txt         # Python dependencies
├── .env.example             # Environment variables template
└── README.md
```

## Setup Instructions

### 1. Prerequisites

- Python 3.11+
- pip (Python package manager)

### 2. Installation

```bash
# Clone the repository
git clone <repository-url>
cd AgriNexus-AI/backend

# Create virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your Government of India API key:
   ```env
   DATA_GOV_API_KEY=your_actual_api_key_here
   ```

   You can obtain an API key from:
   - [data.gov.in](https://data.gov.in/) (recommended for AGMARKNET data)
   - [agmarknet.gov.in](https://agmarknet.gov.in/)

### 4. Database Initialization

The backend uses SQLite by default. Database tables are created automatically on startup.

### 5. Running the Application

```bash
# Start the FastAPI server
uvicorn app.main:app --reload

# The API will be available at:
# - Main endpoint: http://localhost:8000
# - API documentation: http://localhost:8000/docs
# - Alternative docs: http://localhost:8000/redoc
```

### 6. Collecting Market Data

You can manually trigger data collection using the provided script:

```bash
python scripts/collect_market_data.py
```

Options:
- `--commodity`: Filter by commodity (e.g., "Paddy(Common)")
- `--state`: Filter by state (e.g., "Andhra Pradesh")
- `--market`: Filter by market (e.g., "Maddipadu APMC")
- `--limit`: Maximum records to fetch (default: 1000)
- `--verbose`: Enable detailed logging

## API Endpoints

All API endpoints are prefixed with `/api/market`.

### Market Data
- `GET /current` - Get latest price for a commodity
- `GET /history` - Get historical prices for a commodity
- `POST /refresh` - Refresh data from external API

### Forecasting
- `GET /forecast` - Generate price forecast for a commodity

### Analysis
- `GET /trend` - Get market trend analysis
- `GET /signals` - Get comprehensive market signals

### Health Checks
- `GET /health` - Overall application health
- `GET /api/market/health` - Market module health

## Example Usage

### Get Current Price
```bash
curl "http://localhost:8000/api/market/current?commodity=Paddy(Common)&state=Andhra Pradesh"
```

### Generate 7-Day Forecast
```bash
curl "http://localhost:8000/api/market/forecast?commodity=Paddy(Common)&horizon=7&model=ets"
```

### Get Market Signals
```bash
curl "http://localhost:8000/api/market/signals?commodity=Paddy(Common)"
```

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

- **No external crop-calendar API is configured or verified in this
  project.** By default the module serves a small, generalised,
  **non-authoritative reference dataset** bundled at
  `app/services/crop_calendar_reference_data.py`
  (India-generic; crops: rice, wheat, maize, cotton).
- Every response built from it is explicitly labelled with
  `is_reference_data: true`, `data_source: "reference_dataset"` and
  `region_scope: "india_generic"`. **Static reference data is never
  presented as an authoritative or real-time prediction.**
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
# Optional external crop-calendar provider (NO verified provider exists
# in this project; the bundled reference dataset is used by default).
# Set these only after the team verifies a real provider.
CROP_CALENDAR_API_BASE_URL=
CROP_CALENDAR_API_KEY=
```

- The API key is **backend-only**: sent as an `X-API-Key` header, never
  logged, never included in URLs, and never returned by any endpoint
  (health reports only a boolean `external_api_key_configured`).
- When `CROP_CALENDAR_API_BASE_URL` is set, `CROP_CALENDAR_API_KEY`
  becomes required and the external provider replaces the reference
  dataset as the active source.

### Limitations

- The reference dataset is approximate, generalised (India-generic)
  data for demonstration/testing - NOT authoritative agronomy, NOT
  variety-, soil-, or weather-specific.
- Stage dates are deterministic date arithmetic from the supplied
  sowing date; they are not weather-adjusted predictions (weather-aware
  adjustments are intentionally out of scope for now).
- Location is informational only; region-specific calendars require a
  verified external provider.
- The catalogue reflects the bundled dataset even when an external
  provider is configured.

## Contributing

This is a university final-year project. Please consult with the project maintainer before making significant changes.

## License

University Educational Use Only
