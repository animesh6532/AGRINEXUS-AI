"""
Database models for the AgriNexus-AI backend.
Defines SQLAlchemy models for storing agricultural market data.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    DateTime,
    Float,
    UniqueConstraint,
    Index,
)
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import declarative_base

from ..core.logging import logger


# Create base class for declarative models
Base = declarative_base()


class MarketObservation(Base):
    """
    Model representing a single market price observation.

    Stores data obtained from the AGMARKNET API via data.gov.in.
    """
    __tablename__ = "market_observations"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Location information
    state = Column(String(100), nullable=False, index=True)
    district = Column(String(100), nullable=False, index=True)
    market = Column(String(200), nullable=False, index=True)

    # Commodity information
    commodity = Column(String(100), nullable=False, index=True)
    variety = Column(String(100), nullable=True)
    grade = Column(String(50), nullable=True)

    # Price information
    min_price = Column(Float, nullable=False)
    max_price = Column(Float, nullable=False)
    modal_price = Column(Float, nullable=False)

    # Observation date (when the price was recorded)
    observation_date = Column(Date, nullable=False, index=True)

    # Metadata
    source = Column(String(50), default="data.gov.in", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Ensure we don't store duplicate observations for the same
    # commodity, market, and date combination
    __table_args__ = (
        UniqueConstraint(
            "state",
            "district",
            "market",
            "commodity",
            "variety",
            "grade",
            "observation_date",
            name="uix_market_observation_unique"
        ),
        Index("ix_market_observation_commodity_date", "commodity", "observation_date"),
        Index("ix_market_observation_market_date", "market", "observation_date"),
    )

    def __repr__(self) -> str:
        return (
            f"<MarketObservation("
            f"id={self.id}, "
            f"commodity='{self.commodity}', "
            f"market='{self.market}', "
            f"date='{self.observation_date}', "
            f"modal_price={self.modal_price}"
            f")>"
        )

    def to_dict(self) -> dict:
        """
        Convert model instance to dictionary.

        Returns:
            dict: Dictionary representation of the observation
        """
        return {
            "id": self.id,
            "state": self.state,
            "district": self.district,
            "market": self.market,
            "commodity": self.commodity,
            "variety": self.variety,
            "grade": self.grade,
            "min_price": self.min_price,
            "max_price": self.max_price,
            "modal_price": self.modal_price,
            "observation_date": self.observation_date.isoformat() if self.observation_date else None,
            "source": self.source,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ForecastResult(Base):
    """
    Model storing generated forecast results for caching and historical tracking.
    """
    __tablename__ = "forecast_results"

    id = Column(Integer, primary_key=True, index=True)

    # Forecast parameters
    commodity = Column(String(100), nullable=False, index=True)
    state = Column(String(100), nullable=True, index=True)
    district = Column(String(100), nullable=True, index=True)
    market = Column(String(200), nullable=True, index=True)

    # Forecast details
    forecast_date = Column(Date, nullable=False, index=True)  # Date for which forecast was made
    target_date = Column(Date, nullable=False, index=True)    # Date being forecasted
    horizon_days = Column(Integer, nullable=False)            # Number of days ahead

    # Predicted values
    predicted_min_price = Column(Float, nullable=True)
    predicted_max_price = Column(Float, nullable=True)
    predicted_modal_price = Column(Float, nullable=False)

    # Model information
    model_name = Column(String(100), nullable=False)
    model_version = Column(String(50), nullable=True)

    # Metrics (if available)
    mae = Column(Float, nullable=True)
    rmse = Column(Float, nullable=True)
    mape = Column(Float, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "commodity",
            "state",
            "district",
            "market",
            "forecast_date",
            "target_date",
            "model_name",
            name="uix_forecast_result_unique"
        ),
        Index("ix_forecast_result_commodity_target", "commodity", "target_date"),
    )

    def __repr__(self) -> str:
        return (
            f"<ForecastResult("
            f"id={self.id}, "
            f"commodity='{self.commodity}', "
            f"forecast_date='{self.forecast_date}', "
            f"target_date='{self.target_date}', "
            f"predicted_modal_price={self.predicted_modal_price}"
            f")>"
        )