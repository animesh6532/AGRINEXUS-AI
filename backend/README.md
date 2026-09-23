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

## 📜 License
University Educational Use Only.
