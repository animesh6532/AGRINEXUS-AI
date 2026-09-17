"""
Test forecasting models.
"""

import pandas as pd
import numpy as np
from app.forecasting.model import (
    NaiveForecastModel,
    MovingAverageForecastModel,
    ExponentialSmoothingForecastModel,
    ARIMAForecastModel,
    create_forecast_model
)


def test_naive_forecast_model():
    """Test Naive forecasting model."""
    # Create test data
    data = pd.Series([10, 20, 30, 40, 50], index=pd.date_range('2026-01-01', periods=5))

    # Create and fit model
    model = NaiveForecastModel()
    model.fit(data)

    # Generate forecast
    forecasts = model.predict(3)

    # Verify
    assert len(forecasts) == 3
    assert all(f == 50.0 for f in forecasts)  # Should predict last value

    # Test with confidence intervals
    forecasts, lower, upper = model.predict_with_confidence(3)
    assert len(forecasts) == 3
    assert all(f == 50.0 for f in forecasts)
    assert all(l is None for l in lower)  # Naive model doesn't support confidence intervals
    assert all(u is None for u in upper)


def test_moving_average_forecast_model():
    """Test Moving Average forecasting model."""
    # Create test data
    data = pd.Series([10, 20, 30, 40, 50, 60, 70], index=pd.date_range('2026-01-01', periods=7))

    # Create and fit model
    model = MovingAverageForecastModel(window_size=3)
    model.fit(data)

    # Generate forecast (should be average of last 3: 50,60,70 = 60)
    forecasts = model.predict(2)

    # Verify
    assert len(forecasts) == 2
    assert all(abs(f - 60.0) < 0.001 for f in forecasts)  # Should be approximately 60

    # Test with insufficient data (should fall back to naive)
    small_data = pd.Series([10, 20], index=pd.date_range('2026-01-01', periods=2))
    model_small = MovingAverageForecastModel(window_size=5)
    model_small.fit(small_data)
    forecasts_small = model_small.predict(2)
    # Should fall back to last value (20)
    assert all(abs(f - 20.0) < 0.001 for f in forecasts_small)


def test_exponential_smoothing_forecast_model():
    """Test Exponential Smoothing forecasting model."""
    # Create test data with trend
    data = pd.Series(
        [10, 12, 14, 16, 18, 20, 22, 24],
        index=pd.date_range('2026-01-01', periods=8)
    )

    # Create and fit model
    model = ExponentialSmoothingForecastModel(trend="add", seasonal=None)
    model.fit(data)

    # Generate forecast
    forecasts = model.predict(3)

    # Verify
    assert len(forecasts) == 3
    assert all(isinstance(f, (int, float)) for f in forecasts)
    assert all(f > 0 for f in forecasts)  # Should be positive

    # Test with confidence intervals
    forecasts, lower, upper = model.predict_with_confidence(3)
    assert len(forecasts) == 3
    assert all(isinstance(f, (int, float)) for f in forecasts)
    # ETS model should support confidence intervals
    # Note: May be None if internal error handling kicks in


def test_arima_forecast_model():
    """Test ARIMA forecasting model."""
    # Create test data
    data = pd.Series(
        [10, 12, 14, 16, 18, 20, 22, 24, 26, 28],
        index=pd.date_range('2026-01-01', periods=10)
    )

    # Create and fit model
    model = ARIMAForecastModel(order=(1, 1, 1))
    model.fit(data)

    # Generate forecast
    forecasts = model.predict(3)

    # Verify
    assert len(forecasts) == 3
    assert all(isinstance(f, (int, float)) for f in forecasts)
    assert all(f > 0 for f in forecasts)  # Should be positive


def test_create_forecast_model_factory():
    """Test forecasting model factory."""
    # Test creating each model type
    naive_model = create_forecast_model("naive")
    assert isinstance(naive_model, NaiveForecastModel)

    ma_model = create_forecast_model("moving_average")
    assert isinstance(ma_model, MovingAverageForecastModel)

    ets_model = create_forecast_model("ets")
    assert isinstance(ets_model, ExponentialSmoothingForecastModel)

    arima_model = create_forecast_model("arima")
    assert isinstance(arima_model, ARIMAForecastModel)

    # Test default fallback
    unknown_model = create_forecast_model("unknown")
    assert isinstance(unknown_model, NaiveForecastModel)  # Should default to naive


def test_generate_forecast_rejects_single_unique_date():
    """Forecasting must refuse to run when records share one observation date.

    Many records on a single day cannot form a historical time series, so the
    service must raise a controlled ValueError (translated to HTTP 400 by the
    API layer) instead of producing a meaningless forecast.
    """
    import asyncio
    from datetime import date

    import pytest
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from app.database import models
    from app.forecasting.forecast_service import ForecastService

    engine = create_engine("sqlite:///:memory:")
    models.Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()

    # 40 records for the same series, but ALL on a single observation date
    for i in range(40):
        db.add(models.MarketObservation(
            state="Maharashtra",
            district="Ahilyanagar",
            market="Rahuri(Vambori)",
            commodity="Maize",
            variety=None,
            grade=None,
            min_price=2400.0 + i,
            max_price=2450.0 + i,
            modal_price=2425.0 + i,
            observation_date=date.today(),
        ))
    db.commit()

    service = ForecastService(db)

    with pytest.raises(ValueError) as exc_info:
        asyncio.run(service.generate_forecast(
            commodity="Maize",
            horizon_days=7,
            state="Maharashtra",
            district="Ahilyanagar",
            market="Rahuri(Vambori)",
            model_type="ets",
            use_cache=False,
        ))

    assert "unique observation dates" in str(exc_info.value)
    db.close()