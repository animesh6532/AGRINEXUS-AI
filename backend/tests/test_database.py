"""
Test database models and repository.
"""

from datetime import date
from app.database import models, connection, repository
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def test_market_observation_model():
    """Test MarketObservation model creation."""
    # Create in-memory database for testing
    engine = create_engine("sqlite:///:memory:")
    models.Base.metadata.create_all(engine)

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    # Create observation
    obs_data = {
        "state": "Andhra Pradesh",
        "district": "Prakasam",
        "market": "Maddipadu APMC",
        "commodity": "Paddy(Common)",
        "variety": "B P T",
        "grade": "FAQ",
        "min_price": 2800.0,
        "max_price": 2800.0,
        "modal_price": 2800.0,
        "observation_date": date.today(),
        "source": "data.gov.in"
    }

    observation = models.MarketObservation(**obs_data)
    db.add(observation)
    db.commit()
    db.refresh(observation)

    # Verify
    assert observation.id is not None
    assert observation.state == "Andhra Pradesh"
    assert observation.commodity == "Paddy(Common)"
    assert observation.modal_price == 2800.0
    assert observation.observation_date == date.today()

    # Test to_dict method
    obs_dict = observation.to_dict()
    assert obs_dict["state"] == "Andhra Pradesh"
    assert obs_dict["modal_price"] == 2800.0
    assert "id" in obs_dict

    db.close()


def test_forecast_result_model():
    """Test ForecastResult model creation."""
    # Create in-memory database for testing
    engine = create_engine("sqlite:///:memory:")
    models.Base.metadata.create_all(engine)

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    # Create forecast
    forecast_data = {
        "commodity": "Paddy(Common)",
        "state": "Andhra Pradesh",
        "forecast_date": date.today(),
        "target_date": date.today(),
        "horizon_days": 7,
        "predicted_modal_price": 2850.0,
        "model_name": "ETS",
        "mae": 12.5,
        "rmse": 18.2
    }

    forecast = models.ForecastResult(**forecast_data)
    db.add(forecast)
    db.commit()
    db.refresh(forecast)

    # Verify
    assert forecast.id is not None
    assert forecast.commodity == "Paddy(Common)"
    assert forecast.predicted_modal_price == 2850.0
    assert forecast.model_name == "ETS"
    assert forecast.mae == 12.5

    db.close()