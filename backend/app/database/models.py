"""
Database models for the AgriNexus-AI backend.
Defines SQLAlchemy models for storing agricultural market data, farmer profiles,
fields, crop plantings, and farming knowledge records.
"""

from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
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

    # Boundary geometry & geospatial fields
    boundary_geojson = Column(Text, nullable=True)
    perimeter_m = Column(Float, nullable=True)
    centroid_lat = Column(Float, nullable=True)
    centroid_lng = Column(Float, nullable=True)
    geometry_source = Column(String(30), default="MANUAL", nullable=False)  # GEOMETRIC or MANUAL
    geometry_updated_at = Column(DateTime, nullable=True)

    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    farm = relationship("Farm", back_populates="fields")
    plantings = relationship("CropPlanting", back_populates="field", cascade="all, delete-orphan")
    observations = relationship("PlantObservation", back_populates="field", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Field(id={self.id}, name='{self.field_name}', farm_id={self.farm_id})>"

    def to_dict(self) -> dict:
        import json
        boundary = None
        if self.boundary_geojson:
            try:
                boundary = json.loads(self.boundary_geojson)
            except Exception:
                boundary = None

        return {
            "id": self.id,
            "farm_id": self.farm_id,
            "field_name": self.field_name,
            "area_value": self.area_value,
            "area_unit": self.area_unit,
            "total_area_m2": self.total_area_m2,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "boundary_geojson": boundary,
            "perimeter_m": self.perimeter_m,
            "centroid_lat": self.centroid_lat,
            "centroid_lng": self.centroid_lng,
            "geometry_source": self.geometry_source,
            "geometry_updated_at": self.geometry_updated_at.isoformat() if self.geometry_updated_at else None,
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


class PlantObservation(Base):
    """
    Model representing a field/plant-level observation or scouting record.
    Supports attached photo analysis via existing CV disease/pest models.
    """
    __tablename__ = "plant_observations"

    id = Column(Integer, primary_key=True, index=True)
    field_id = Column(Integer, ForeignKey("fields.id", ondelete="CASCADE"), nullable=False, index=True)
    crop_planting_id = Column(Integer, ForeignKey("crop_plantings.id", ondelete="SET NULL"), nullable=True, index=True)
    observation_date = Column(Date, default=date.today, nullable=False)
    image_url = Column(String(500), nullable=True)
    disease_result = Column(String(200), nullable=True)
    pest_result = Column(String(200), nullable=True)
    severity = Column(String(50), default="INFO", nullable=False)
    notes = Column(Text, nullable=True)
    location_in_field = Column(String(150), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    field = relationship("Field", back_populates="observations")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "field_id": self.field_id,
            "crop_planting_id": self.crop_planting_id,
            "observation_date": self.observation_date.isoformat() if self.observation_date else None,
            "image_url": self.image_url,
            "disease_result": self.disease_result,
            "pest_result": self.pest_result,
            "severity": self.severity,
            "notes": self.notes,
            "location_in_field": self.location_in_field,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ActionItemRecord(Base):
    """
    Model storing personalized action items and farmer completion state.
    """
    __tablename__ = "action_item_records"

    id = Column(String(100), primary_key=True, index=True)
    farmer_id = Column(Integer, ForeignKey("farmer_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    field_id = Column(Integer, ForeignKey("fields.id", ondelete="SET NULL"), nullable=True, index=True)
    crop_id = Column(Integer, ForeignKey("crop_plantings.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String(250), nullable=False)
    action_text = Column(Text, nullable=False)
    reason = Column(Text, nullable=False)
    action_type = Column(String(50), default="general", nullable=False)
    priority = Column(String(30), default="MEDIUM", nullable=False)  # CRITICAL, HIGH, MEDIUM, LOW
    time_window = Column(String(30), default="TODAY", nullable=False)  # TODAY, TOMORROW, THIS_WEEK, NEXT_WEEK, UPCOMING
    status = Column(String(30), default="TODO", nullable=False)  # TODO, IN_PROGRESS, DONE, DISMISSED, EXPIRED
    source = Column(String(100), default="RiskEngine", nullable=False)
    due_date = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    completed_by = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "farmer_id": self.farmer_id,
            "field_id": self.field_id,
            "crop_id": self.crop_id,
            "title": self.title,
            "action_text": self.action_text,
            "reason": self.reason,
            "action_type": self.action_type,
            "priority": self.priority,
            "time_window": self.time_window,
            "status": self.status,
            "source": self.source,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "completed_by": self.completed_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class AlertNotificationRecord(Base):
    """
    Model storing persistent smart farm alerts and delivery state.
    """
    __tablename__ = "alert_notification_records"

    id = Column(String(100), primary_key=True, index=True)
    farmer_id = Column(Integer, ForeignKey("farmer_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    field_id = Column(Integer, ForeignKey("fields.id", ondelete="SET NULL"), nullable=True)
    crop_id = Column(Integer, ForeignKey("crop_plantings.id", ondelete="SET NULL"), nullable=True)
    category = Column(String(50), nullable=False)  # Weather, Irrigation, Pest, Soil, Market, Calendar, Action
    severity = Column(String(30), default="INFO", nullable=False)  # CRITICAL, HIGH, MEDIUM, LOW, INFO
    title = Column(String(250), nullable=False)
    description = Column(Text, nullable=False)
    trigger_evidence = Column(Text, nullable=True)
    potential_impact = Column(Text, nullable=True)
    recommended_action = Column(Text, nullable=True)
    status = Column(String(30), default="UNREAD", nullable=False)  # UNREAD, READ, DISMISSED, RESOLVED
    fingerprint = Column(String(200), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)

    deliveries = relationship("NotificationDeliveryRecord", back_populates="alert", cascade="all, delete-orphan")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "farmer_id": self.farmer_id,
            "field_id": self.field_id,
            "crop_id": self.crop_id,
            "category": self.category,
            "severity": self.severity,
            "title": self.title,
            "description": self.description,
            "trigger_evidence": self.trigger_evidence,
            "potential_impact": self.potential_impact,
            "recommended_action": self.recommended_action,
            "status": self.status,
            "fingerprint": self.fingerprint,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }


class NotificationPreferenceRecord(Base):
    """
    Model storing farmer notification channel & category preferences.
    """
    __tablename__ = "notification_preference_records"

    id = Column(Integer, primary_key=True, index=True)
    farmer_id = Column(Integer, ForeignKey("farmer_profiles.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    # Channels
    channel_in_app = Column(Boolean, default=True, nullable=False)
    channel_email = Column(Boolean, default=True, nullable=False)
    channel_sms = Column(Boolean, default=False, nullable=False)
    channel_whatsapp = Column(Boolean, default=False, nullable=False)

    # Categories
    cat_critical_risks = Column(Boolean, default=True, nullable=False)
    cat_weather = Column(Boolean, default=True, nullable=False)
    cat_crop_health = Column(Boolean, default=True, nullable=False)
    cat_irrigation = Column(Boolean, default=True, nullable=False)
    cat_market = Column(Boolean, default=True, nullable=False)
    cat_calendar = Column(Boolean, default=True, nullable=False)
    cat_action_reminders = Column(Boolean, default=True, nullable=False)

    # Quiet hours
    quiet_hours_enabled = Column(Boolean, default=False, nullable=False)
    quiet_hours_start = Column(String(10), default="22:00", nullable=False)
    quiet_hours_end = Column(String(10), default="06:00", nullable=False)
    critical_override = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def to_dict(self) -> dict:
        return {
            "farmer_id": self.farmer_id,
            "channels": {
                "in_app": self.channel_in_app,
                "email": self.channel_email,
                "sms": self.channel_sms,
                "whatsapp": self.channel_whatsapp,
            },
            "categories": {
                "critical_risks": self.cat_critical_risks,
                "weather": self.cat_weather,
                "crop_health": self.cat_crop_health,
                "irrigation": self.cat_irrigation,
                "market": self.cat_market,
                "calendar": self.cat_calendar,
                "action_reminders": self.cat_action_reminders,
            },
            "quiet_hours": {
                "enabled": self.quiet_hours_enabled,
                "start": self.quiet_hours_start,
                "end": self.quiet_hours_end,
                "critical_override": self.critical_override,
            },
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class NotificationDeliveryRecord(Base):
    """
    Model logging delivery attempts across Email, SMS, WhatsApp providers.
    """
    __tablename__ = "notification_delivery_records"

    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(String(100), ForeignKey("alert_notification_records.id", ondelete="CASCADE"), nullable=False, index=True)
    channel = Column(String(30), nullable=False)  # EMAIL, SMS, WHATSAPP, IN_APP
    recipient = Column(String(200), nullable=False)
    provider_message_id = Column(String(200), nullable=True)
    status = Column(String(30), default="PENDING", nullable=False)  # PENDING, SENT, DELIVERED, FAILED
    sent_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    delivered_at = Column(DateTime, nullable=True)
    failure_reason = Column(Text, nullable=True)

    alert = relationship("AlertNotificationRecord", back_populates="deliveries")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "alert_id": self.alert_id,
            "channel": self.channel,
            "recipient": self.recipient,
            "provider_message_id": self.provider_message_id,
            "status": self.status,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
            "failure_reason": self.failure_reason,
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
        nullable=False,
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
            name="uix_market_observation_unique",
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
            name="uix_forecast_result_unique",
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


class IrrigationLog(Base):
    """
    Model representing historical/logged irrigation events for a field.
    Enables water budget calculations, season totals, and historical tracking.
    """
    __tablename__ = "irrigation_logs"

    id = Column(Integer, primary_key=True, index=True)
    field_id = Column(Integer, ForeignKey("fields.id", ondelete="CASCADE"), nullable=False, index=True)
    farmer_id = Column(Integer, ForeignKey("farmer_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    water_amount_mm = Column(Float, nullable=False)
    water_amount_liters = Column(Float, nullable=True)
    method = Column(String(100), nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)
    logged_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    field = relationship("Field")
    farmer = relationship("FarmerProfile")

    def __repr__(self) -> str:
        return f"<IrrigationLog(id={self.id}, field_id={self.field_id}, mm={self.water_amount_mm}, logged_at='{self.logged_at}')>"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "field_id": self.field_id,
            "farmer_id": self.farmer_id,
            "water_amount_mm": self.water_amount_mm,
            "water_amount_liters": self.water_amount_liters,
            "method": self.method,
            "duration_minutes": self.duration_minutes,
            "notes": self.notes,
            "logged_at": self.logged_at.isoformat() if self.logged_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class FarmingKnowledgeRecord(Base):
    """
    Model representing a validated agricultural Question & Answer knowledge record.
    Preserves source traceability, agronomic context, and precomputed vector embeddings.
    """
    __tablename__ = "farming_knowledge_records"

    id = Column(Integer, primary_key=True, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    crop = Column(String(100), nullable=True, index=True)
    crop_stage = Column(String(100), nullable=True, index=True)
    topic = Column(String(100), nullable=False, index=True)
    subtopic = Column(String(100), nullable=True)
    keywords = Column(String(500), nullable=True)
    language = Column(String(20), default="en", nullable=False)
    region = Column(String(100), nullable=True)
    source = Column(String(200), default="AGRINEXUS Farming Knowledge Base", nullable=False)
    source_url = Column(String(500), nullable=True)
    verified = Column(Boolean, default=True, nullable=False)
    embedding = Column(LargeBinary, nullable=True)
    embedding_dim = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_fkr_crop_topic", "crop", "topic"),
    )

    def to_dict(self) -> dict:
        """Convert model instance to dictionary without binary embedding blob."""
        return {
            "id": self.id,
            "question": self.question,
            "answer": self.answer,
            "crop": self.crop,
            "crop_stage": self.crop_stage,
            "topic": self.topic,
            "subtopic": self.subtopic,
            "keywords": self.keywords,
            "language": self.language,
            "region": self.region,
            "source": self.source,
            "source_url": self.source_url,
            "verified": self.verified,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Conversation(Base):
    """
    Model representing a persistent AI Farming Assistant conversation session.
    """
    __tablename__ = "conversations"

    id = Column(String(50), primary_key=True, index=True)
    user_id = Column(String(100), nullable=False, index=True)
    title = Column(String(200), nullable=False, default="New Conversation")
    active_field_id = Column(Integer, nullable=True)
    active_crop_id = Column(Integer, nullable=True)
    page_context = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_message_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "active_field_id": self.active_field_id,
            "active_crop_id": self.active_crop_id,
            "page_context": self.page_context,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_message_at": self.last_message_at.isoformat() if self.last_message_at else None,
            "message_count": len(self.messages) if self.messages else 0,
        }


class Message(Base):
    """
    Model representing a single message within a conversation.
    """
    __tablename__ = "messages"

    id = Column(String(50), primary_key=True, index=True)
    conversation_id = Column(String(50), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # "user", "assistant", "system"
    content = Column(Text, nullable=False)
    tool_calls = Column(Text, nullable=True)
    actions = Column(Text, nullable=True)
    sources = Column(Text, nullable=True)
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    conversation = relationship("Conversation", back_populates="messages")

    def to_dict(self) -> dict:
        import json
        return {
            "id": self.id,
            "conversation_id": self.conversation_id,
            "role": self.role,
            "content": self.content,
            "tool_calls": json.loads(self.tool_calls) if self.tool_calls else [],
            "actions": json.loads(self.actions) if self.actions else [],
            "sources": json.loads(self.sources) if self.sources else [],
            "metadata": json.loads(self.metadata_json) if self.metadata_json else {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


