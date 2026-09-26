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
    Boolean,
    Text,
    ForeignKey,
    UniqueConstraint,
    Index,
)
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import declarative_base, relationship

from ..core.logging import logger


# Create base class for declarative models
Base = declarative_base()


def normalize_area_to_m2(value: float, unit: str) -> float:
    """Normalize land area to square meters based on unit."""
    if not value or value < 0:
        return 0.0
    u = (unit or "").lower().strip()
    if u in ("acre", "acres"):
        return value * 4046.86
    elif u in ("hectare", "hectares", "ha"):
        return value * 10000.0
    elif u in ("bigha", "bighas"):
        return value * 1337.8
    elif u in ("sqm", "m2", "square meter", "square meters"):
        return value
    return value * 4046.86  # default to acre conversion


class FarmerProfile(Base):
    """
    Model representing a persistent farmer profile.
    Central source of truth for the farmer's account and personal details.
    """
    __tablename__ = "farmer_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), nullable=False, unique=True, index=True)
    full_name = Column(String(150), nullable=False)
    phone = Column(String(30), nullable=True)
    email = Column(String(150), nullable=True)
    preferred_language = Column(String(20), default="en", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    farms = relationship("Farm", back_populates="farmer", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<FarmerProfile(id={self.id}, user_id='{self.user_id}', full_name='{self.full_name}')>"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "full_name": self.full_name,
            "phone": self.phone,
            "email": self.email,
            "preferred_language": self.preferred_language,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Farm(Base):
    """
    Model representing a farm owned/managed by a farmer.
    Can contain multiple fields.
    """
    __tablename__ = "farms"

    id = Column(Integer, primary_key=True, index=True)
    farmer_id = Column(Integer, ForeignKey("farmer_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    farm_name = Column(String(150), nullable=False)
    location_name = Column(String(250), nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    area_value = Column(Float, nullable=False)
    area_unit = Column(String(30), default="acre", nullable=False)
    total_area_m2 = Column(Float, nullable=False)
    soil_type_manual = Column(String(100), nullable=True)
    water_source = Column(String(100), nullable=True)
    irrigation_method = Column(String(100), nullable=True)
    ownership_type = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    farmer = relationship("FarmerProfile", back_populates="farms")
    fields = relationship("Field", back_populates="farm", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Farm(id={self.id}, name='{self.farm_name}', area={self.area_value} {self.area_unit})>"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "farmer_id": self.farmer_id,
            "farm_name": self.farm_name,
            "location_name": self.location_name,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "area_value": self.area_value,
            "area_unit": self.area_unit,
            "total_area_m2": self.total_area_m2,
            "soil_type_manual": self.soil_type_manual,
            "water_source": self.water_source,
            "irrigation_method": self.irrigation_method,
            "ownership_type": self.ownership_type,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Field(Base):
    """
    Model representing a specific field within a farm.
    Stores field boundary/area and soil telemetry/test results.
    """
    __tablename__ = "fields"

    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, ForeignKey("farms.id", ondelete="CASCADE"), nullable=False, index=True)
    field_name = Column(String(150), nullable=False)
    area_value = Column(Float, nullable=False)
    area_unit = Column(String(30), default="acre", nullable=False)
    total_area_m2 = Column(Float, nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    soil_type = Column(String(100), nullable=True)
    soil_test_available = Column(Boolean, default=False, nullable=False)

    # Soil parameters & provenance (MEASURED / ESTIMATED / UNKNOWN)
    ph = Column(Float, nullable=True)
    ph_provenance = Column(String(30), default="UNKNOWN", nullable=False)

    nitrogen = Column(Float, nullable=True)
    nitrogen_provenance = Column(String(30), default="UNKNOWN", nullable=False)

    phosphorus = Column(Float, nullable=True)
    phosphorus_provenance = Column(String(30), default="UNKNOWN", nullable=False)

    potassium = Column(Float, nullable=True)
    potassium_provenance = Column(String(30), default="UNKNOWN", nullable=False)

    organic_carbon = Column(Float, nullable=True)
    organic_carbon_provenance = Column(String(30), default="UNKNOWN", nullable=False)

    ec = Column(Float, nullable=True)
    ec_provenance = Column(String(30), default="UNKNOWN", nullable=False)

    texture = Column(String(50), nullable=True)
    texture_provenance = Column(String(30), default="UNKNOWN", nullable=False)

    moisture = Column(Float, nullable=True)
    moisture_provenance = Column(String(30), default="UNKNOWN", nullable=False)

    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    farm = relationship("Farm", back_populates="fields")
    plantings = relationship("CropPlanting", back_populates="field", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Field(id={self.id}, name='{self.field_name}', farm_id={self.farm_id})>"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "farm_id": self.farm_id,
            "field_name": self.field_name,
            "area_value": self.area_value,
            "area_unit": self.area_unit,
            "total_area_m2": self.total_area_m2,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "soil_type": self.soil_type,
            "soil_test_available": self.soil_test_available,
            "soil_data": {
                "ph": {"value": self.ph, "provenance": self.ph_provenance},
                "nitrogen": {"value": self.nitrogen, "provenance": self.nitrogen_provenance},
                "phosphorus": {"value": self.phosphorus, "provenance": self.phosphorus_provenance},
                "potassium": {"value": self.potassium, "provenance": self.potassium_provenance},
                "organic_carbon": {"value": self.organic_carbon, "provenance": self.organic_carbon_provenance},
                "ec": {"value": self.ec, "provenance": self.ec_provenance},
                "texture": {"value": self.texture, "provenance": self.texture_provenance},
                "moisture": {"value": self.moisture, "provenance": self.moisture_provenance},
            },
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class CropPlanting(Base):
    """
    Model representing an active or planned crop cultivation on a field.
    """
    __tablename__ = "crop_plantings"

    id = Column(Integer, primary_key=True, index=True)
    field_id = Column(Integer, ForeignKey("fields.id", ondelete="CASCADE"), nullable=False, index=True)
    crop_id = Column(String(100), nullable=True)
    crop_name = Column(String(100), nullable=False, index=True)
    scientific_name = Column(String(150), nullable=True)
    variety = Column(String(100), nullable=True)
    category = Column(String(100), nullable=True)
    sowing_date = Column(Date, nullable=True)
    expected_harvest_date = Column(Date, nullable=True)
    growth_stage = Column(String(100), nullable=True)
    growth_stage_source = Column(String(50), default="farmer", nullable=False)
    cultivation_type = Column(String(100), nullable=True)
    irrigation_method = Column(String(100), nullable=True)
    water_availability = Column(String(100), nullable=True)
    status = Column(String(50), default="ACTIVE", nullable=False, index=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    field = relationship("Field", back_populates="plantings")

    def __repr__(self) -> str:
        return f"<CropPlanting(id={self.id}, crop='{self.crop_name}', field_id={self.field_id})>"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "field_id": self.field_id,
            "crop_id": self.crop_id,
            "crop_name": self.crop_name,
            "scientific_name": self.scientific_name,
            "variety": self.variety,
            "category": self.category,
            "sowing_date": self.sowing_date.isoformat() if self.sowing_date else None,
            "expected_harvest_date": self.expected_harvest_date.isoformat() if self.expected_harvest_date else None,
            "growth_stage": self.growth_stage,
            "growth_stage_source": self.growth_stage_source,
            "cultivation_type": self.cultivation_type,
            "irrigation_method": self.irrigation_method,
            "water_availability": self.water_availability,
            "status": self.status,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


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