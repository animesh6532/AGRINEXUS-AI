"""
Pydantic schemas for Market Forecast API requests and responses.
"""

from datetime import date, datetime
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field


class MarketObservationBase(BaseModel):
    """Base schema for market observation data."""
    state: str = Field(..., example="Andhra Pradesh")
    district: str = Field(..., example="Prakasam")
    market: str = Field(..., example="Maddipadu APMC")
    commodity: str = Field(..., example="Paddy(Common)")
    variety: Optional[str] = Field(None, example="B P T")
    grade: Optional[str] = Field(None, example="FAQ")
    min_price: float = Field(..., gt=0, example=2800.0)
    max_price: float = Field(..., gt=0, example=2800.0)
    modal_price: float = Field(..., gt=0, example=2800.0)
    observation_date: date = Field(..., example="2026-09-17")

    source: str = Field(default="data.gov.in", example="data.gov.in")


class MarketObservationCreate(MarketObservationBase):
    """Schema for creating new market observations."""
    pass


class MarketObservationResponse(MarketObservationBase):
    """Schema for market observation response."""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ForecastPointBase(BaseModel):
    """Schema for a single forecast point."""
    date: date = Field(..., example="2026-09-24")

    predicted_price: float = Field(..., gt=0, example=2850.0)
    confidence_lower: Optional[float] = Field(None, example=2800.0)
    confidence_upper: Optional[float] = Field(None, example=2900.0)


class ForecastPointResponse(ForecastPointBase):
    """Schema for forecast point response."""
    pass


class MarketForecastResponse(BaseModel):
    """Schema for market forecast response."""
    commodity: str = Field(..., example="Paddy(Common)")
    market: Optional[str] = Field(None, example="Maddipadu APMC")
    state: Optional[str] = Field(None, example="Andhra Pradesh")
    current_price: float = Field(..., ge=0, example=2800.0)
    forecast_horizon_days: int = Field(..., gt=0, example=7)
    forecast: List[ForecastPointResponse]
    trend: str = Field(
        ...,
        pattern="^(increasing|decreasing|stable|insufficient_data)$",
        example="increasing"
    )
    model: str = Field(..., example="ETS_add_none_no")
    metrics: Dict[str, float] = Field(
        ...,
        example={
            "mae": 12.5,
            "rmse": 18.2,
            "mape": 5.8
        }
    )

    class Config:
        json_schema_extra = {
            "example": {
                "commodity": "Paddy(Common)",
                "market": "Maddipadu APMC",
                "state": "Andhra Pradesh",
                "current_price": 2800.0,
                "forecast_horizon_days": 7,
                "forecast": [
                    {
                        "date": "2026-09-18",
                        "predicted_price": 2820.0,
                        "confidence_lower": 2780.0,
                        "confidence_upper": 2860.0
                    },
                    {
                        "date": "2026-09-19",
                        "predicted_price": 2840.0,
                        "confidence_lower": 2800.0,
                        "confidence_upper": 2880.0
                    }
                ],
                "trend": "increasing",
                "model": "ETS_add_none_no",
                "metrics": {
                    "mae": 12.5,
                    "rmse": 18.2,
                    "mape": 5.8
                }
            }
        }


class MarketTrendResponse(BaseModel):
    """Schema for market trend response."""
    commodity: str = Field(..., example="Paddy(Common)")
    market: Optional[str] = Field(None, example="Maddipadu APMC")
    state: Optional[str] = Field(None, example="Andhra Pradesh")
    trend: str = Field(..., pattern="^(increasing|decreasing|stable|insufficient_data)$", example="increasing")
    recent_change_percent: float = Field(..., example=4.2)
    forecast_change_percent: float = Field(..., example=6.1)
    volatility: float = Field(..., example=3.5)
    signal_strength: float = Field(..., ge=0.0, le=1.0, example=0.8)
    data_points: int = Field(..., example=25)
    analysis_period_days: int = Field(..., example=30)
    latest_price: float = Field(..., ge=0, example=2800.0)
    latest_date: Optional[DateType] = Field(None, example="2026-09-17")


class MarketSignalsResponse(BaseModel):
    """Schema for comprehensive market signals response."""
    commodity: str = Field(..., example="Paddy(Common)")
    market: Optional[str] = Field(None, example="Maddipadu APMC")
    state: Optional[str] = Field(None, example="Andhra Pradesh")
    district: Optional[str] = Field(None, example="Prakasam")
    timestamp: str = Field(..., example="2026-09-17T10:30:00Z")
    latest_price: Optional[MarketObservationResponse] = None
    trend_analysis: MarketTrendResponse
    forecast_analysis: MarketForecastResponse
    actionable_signals: List[Dict[str, Any]] = Field(
        ...,
        example=[
            {
                "type": "trend_continuation",
                "direction": "increasing",
                "strength": "medium",
                "description": "Increasing trend expected to continue",
                "confidence": "medium"
            }
        ]
    )
    forecast_horizon_days: int = Field(..., example=7)


class ErrorResponse(BaseModel):
    """Schema for error responses."""
    error: str = Field(..., example="Invalid commodity specified")
    detail: Optional[str] = Field(None, example="Commodity 'InvalidCrop' not found in database")
    status_code: int = Field(..., example=400)


class PaginatedResponse(BaseModel):
    """Schema for paginated responses."""
    items: List[MarketObservationResponse]
    total: int
    page: int
    size: int
    pages: int


# Request parameter schemas
class MarketDataRequest(BaseModel):
    """Request parameters for market data queries."""
    commodity: Optional[str] = Field(None, example="Paddy(Common)")
    state: Optional[str] = Field(None, example="Andhra Pradesh")
    district: Optional[str] = Field(None, example="Prakasam")
    market: Optional[str] = Field(None, example="Maddipadu APMC")
    start_date: Optional[date] = Field(None, example="2026-09-01")
    end_date: Optional[date] = Field(None, example="2026-09-17")
    limit: int = Field(default=100, ge=1, le=1000)


class MarketForecastRequest(BaseModel):
    """Request parameters for market forecast."""
    commodity: str = Field(..., example="Paddy(Common)")
    state: Optional[str] = Field(None, example="Andhra Pradesh")
    district: Optional[str] = Field(None, example="Prakasam")
    market: Optional[str] = Field(None, example="Maddipadu APMC")
    horizon: int = Field(default=7, ge=1, le=30, example=7)
    model: Optional[str] = Field(
        default=None,
        pattern="^(naive|moving_average|ets|arima)$",
        example="ets"
    )
    use_cache: bool = Field(default=True, example=True)


class MarketTrendRequest(BaseModel):
    """Request parameters for market trend analysis."""
    commodity: str = Field(..., example="Paddy(Common)")
    state: Optional[str] = Field(None, example="Andhra Pradesh")
    district: Optional[str] = Field(None, example="Prakasam")
    market: Optional[str] = Field(None, example="Maddipadu APMC")
    lookback_days: int = Field(default=30, ge=7, le=90, example=30)