# AgriNexus-AI Market Forecast Backend

This is the backend implementation for the Market Forecast module of the AgriNexus-AI university final-year project.

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
│   ├── services/
│   │   └── market_service.py# Market data service and API client
│   ├── forecasting/
│   │   ├─ forecast_service.py# Forecasting service
│   │   └─ model.py          # Forecasting models
│   ├── intelligence/
│   │   └─ market_intelligence.py# Market intelligence layer
│   ├── schemas/
│   │   └─ market.py         # Pydantic schemas for API
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

## Contributing

This is a university final-year project. Please consult with the project maintainer before making significant changes.

## License

University Educational Use Only