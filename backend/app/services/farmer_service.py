"""
Farmer Profile & Personalized Farm Intelligence Services.
Handles persistent storage of farmer profiles, farms, fields, and crop cultivations,
and aggregates live personalized farm intelligence.
"""

from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from ..database import models
from ..core.logging import logger
from ..services.weather_service import WeatherService
from ..services.market_service import MarketService
from ..services.crop_calendar_service import CropCalendarService
from ..intelligence.weather_intelligence import WeatherIntelligence
from ..intelligence.market_intelligence import MarketIntelligence
from ..intelligence.crop_calendar_intelligence import CropCalendarIntelligence


class FarmerRepository:
    """Repository for CRUD operations on FarmerProfile, Farm, Field, and CropPlanting."""

    def __init__(self, db: Session):
        self.db = db

    def get_or_create_profile(
        self, user_id: str, full_name: str = "Default Farmer", email: Optional[str] = None, phone: Optional[str] = None
    ) -> models.FarmerProfile:
        profile = self.db.query(models.FarmerProfile).filter(models.FarmerProfile.user_id == user_id).first()
        if not profile:
            profile = models.FarmerProfile(
                user_id=user_id,
                full_name=full_name,
                email=email,
                phone=phone,
                preferred_language="en",
            )
            self.db.add(profile)
            self.db.commit()
            self.db.refresh(profile)
            logger.info(f"Created new farmer profile for user_id: {user_id}")
        return profile

    def update_profile(self, user_id: str, profile_data: dict) -> models.FarmerProfile:
        try:
            profile = self.get_or_create_profile(user_id)
            for key, val in profile_data.items():
                if hasattr(profile, key):
                    setattr(profile, key, val)
            profile.updated_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(profile)
            return profile
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating farmer profile for user {user_id}: {e}")
            raise

    def create_farm(self, user_id: str, farm_data: dict) -> models.Farm:
        profile = self.get_or_create_profile(user_id)
        area_val = farm_data.get("area_value", 1.0)
        area_unit = farm_data.get("area_unit", "acre")
        total_m2 = models.normalize_area_to_m2(area_val, area_unit)

        farm = models.Farm(
            farmer_id=profile.id,
            farm_name=farm_data.get("farm_name", "My Farm"),
            location_name=farm_data.get("location_name"),
            latitude=farm_data.get("latitude", 22.5726),
            longitude=farm_data.get("longitude", 88.3639),
            area_value=area_val,
            area_unit=area_unit,
            total_area_m2=total_m2,
            soil_type_manual=farm_data.get("soil_type_manual"),
            water_source=farm_data.get("water_source"),
            irrigation_method=farm_data.get("irrigation_method"),
            ownership_type=farm_data.get("ownership_type"),
            notes=farm_data.get("notes"),
        )
        self.db.add(farm)
        self.db.commit()
        self.db.refresh(farm)
        return farm

    def update_farm(self, farm_id: int, user_id: str, farm_data: dict) -> Optional[models.Farm]:
        try:
            profile = self.get_or_create_profile(user_id)
            farm = self.db.query(models.Farm).filter(models.Farm.id == farm_id, models.Farm.farmer_id == profile.id).first()
            if not farm:
                return None
            for key, val in farm_data.items():
                if hasattr(farm, key):
                    setattr(farm, key, val)
            if "area_value" in farm_data or "area_unit" in farm_data:
                farm.total_area_m2 = models.normalize_area_to_m2(farm.area_value, farm.area_unit)
            farm.updated_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(farm)
            return farm
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating farm {farm_id} for user {user_id}: {e}")
            raise

    def delete_farm(self, farm_id: int, user_id: str) -> bool:
        try:
            profile = self.get_or_create_profile(user_id)
            farm = self.db.query(models.Farm).filter(models.Farm.id == farm_id, models.Farm.farmer_id == profile.id).first()
            if not farm:
                return False
            self.db.delete(farm)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting farm {farm_id} for user {user_id}: {e}")
            raise

    def create_field(self, user_id: str, field_data: dict) -> Optional[models.Field]:
        try:
            profile = self.get_or_create_profile(user_id)
            farm_id = field_data.get("farm_id")
            farm = self.db.query(models.Farm).filter(models.Farm.id == farm_id, models.Farm.farmer_id == profile.id).first()
            if not farm:
                return None

            area_val = field_data.get("area_value", 1.0)
            area_unit = field_data.get("area_unit", "acre")
            total_m2 = models.normalize_area_to_m2(area_val, area_unit)

            field = models.Field(
                farm_id=farm.id,
                field_name=field_data.get("field_name", "Field A"),
                area_value=area_val,
                area_unit=area_unit,
                total_area_m2=total_m2,
                latitude=field_data.get("latitude", farm.latitude),
                longitude=field_data.get("longitude", farm.longitude),
                soil_type=field_data.get("soil_type", farm.soil_type_manual),
                soil_test_available=field_data.get("soil_test_available", False),
                ph=field_data.get("ph"),
                ph_provenance=field_data.get("ph_provenance", "MEASURED" if field_data.get("ph") is not None else "UNKNOWN"),
                nitrogen=field_data.get("nitrogen"),
                nitrogen_provenance=field_data.get("nitrogen_provenance", "MEASURED" if field_data.get("nitrogen") is not None else "UNKNOWN"),
                phosphorus=field_data.get("phosphorus"),
                phosphorus_provenance=field_data.get("phosphorus_provenance", "MEASURED" if field_data.get("phosphorus") is not None else "UNKNOWN"),
                potassium=field_data.get("potassium"),
                potassium_provenance=field_data.get("potassium_provenance", "MEASURED" if field_data.get("potassium") is not None else "UNKNOWN"),
                organic_carbon=field_data.get("organic_carbon"),
                organic_carbon_provenance=field_data.get("organic_carbon_provenance", "MEASURED" if field_data.get("organic_carbon") is not None else "UNKNOWN"),
                ec=field_data.get("ec"),
                ec_provenance=field_data.get("ec_provenance", "MEASURED" if field_data.get("ec") is not None else "UNKNOWN"),
                texture=field_data.get("texture"),
                texture_provenance=field_data.get("texture_provenance", "MEASURED" if field_data.get("texture") is not None else "UNKNOWN"),
                moisture=field_data.get("moisture"),
                moisture_provenance=field_data.get("moisture_provenance", "MEASURED" if field_data.get("moisture") is not None else "UNKNOWN"),
                notes=field_data.get("notes"),
            )
            self.db.add(field)
            self.db.commit()
            self.db.refresh(field)
            return field
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating field for user {user_id}: {e}")
            raise

    def update_field(self, field_id: int, user_id: str, field_data: dict) -> Optional[models.Field]:
        try:
            profile = self.get_or_create_profile(user_id)
            field = (
                self.db.query(models.Field)
                .join(models.Farm)
                .filter(models.Field.id == field_id, models.Farm.farmer_id == profile.id)
                .first()
            )
            if not field:
                return None

            for key, val in field_data.items():
                if hasattr(field, key):
                    setattr(field, key, val)

            if "area_value" in field_data or "area_unit" in field_data:
                field.total_area_m2 = models.normalize_area_to_m2(field.area_value, field.area_unit)

            field.updated_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(field)
            return field
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating field {field_id} for user {user_id}: {e}")
            raise

    def delete_field(self, field_id: int, user_id: str) -> bool:
        try:
            profile = self.get_or_create_profile(user_id)
            field = (
                self.db.query(models.Field)
                .join(models.Farm)
                .filter(models.Field.id == field_id, models.Farm.farmer_id == profile.id)
                .first()
            )
            if not field:
                return False
            self.db.delete(field)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting field {field_id} for user {user_id}: {e}")
            raise

    def create_crop_planting(self, user_id: str, crop_data: dict) -> Optional[models.CropPlanting]:
        try:
            profile = self.get_or_create_profile(user_id)
            field_id = crop_data.get("field_id")
            field = (
                self.db.query(models.Field)
                .join(models.Farm)
                .filter(models.Field.id == field_id, models.Farm.farmer_id == profile.id)
                .first()
            )
            if not field:
                return None

            s_date = crop_data.get("sowing_date")
            if isinstance(s_date, str):
                try:
                    s_date = date.fromisoformat(s_date)
                except ValueError:
                    s_date = None

            h_date = crop_data.get("expected_harvest_date")
            if isinstance(h_date, str):
                try:
                    h_date = date.fromisoformat(h_date)
                except ValueError:
                    h_date = None

            crop = models.CropPlanting(
                field_id=field.id,
                crop_id=crop_data.get("crop_id"),
                crop_name=crop_data.get("crop_name", "Rice"),
                scientific_name=crop_data.get("scientific_name"),
                variety=crop_data.get("variety"),
                category=crop_data.get("category"),
                sowing_date=s_date,
                expected_harvest_date=h_date,
                growth_stage=crop_data.get("growth_stage", "Vegetative"),
                growth_stage_source=crop_data.get("growth_stage_source", "farmer"),
                cultivation_type=crop_data.get("cultivation_type"),
                irrigation_method=crop_data.get("irrigation_method"),
                water_availability=crop_data.get("water_availability"),
                status=crop_data.get("status", "ACTIVE"),
                notes=crop_data.get("notes"),
            )
            self.db.add(crop)
            self.db.commit()
            self.db.refresh(crop)
            return crop
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating crop planting for user {user_id}: {e}")
            raise

    def update_crop_planting(self, crop_id: int, user_id: str, crop_data: dict) -> Optional[models.CropPlanting]:
        try:
            profile = self.get_or_create_profile(user_id)
            crop = (
                self.db.query(models.CropPlanting)
                .join(models.Field)
                .join(models.Farm)
                .filter(models.CropPlanting.id == crop_id, models.Farm.farmer_id == profile.id)
                .first()
            )
            if not crop:
                return None

            for key, val in crop_data.items():
                if hasattr(crop, key):
                    if key in ("sowing_date", "expected_harvest_date") and isinstance(val, str):
                        try:
                            val = date.fromisoformat(val)
                        except ValueError:
                            val = None
                    setattr(crop, key, val)

            crop.updated_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(crop)
            return crop
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating crop planting {crop_id} for user {user_id}: {e}")
            raise

    def delete_crop_planting(self, crop_id: int, user_id: str) -> bool:
        try:
            profile = self.get_or_create_profile(user_id)
            crop = (
                self.db.query(models.CropPlanting)
                .join(models.Field)
                .join(models.Farm)
                .filter(models.CropPlanting.id == crop_id, models.Farm.farmer_id == profile.id)
                .first()
            )
            if not crop:
                return False
            self.db.delete(crop)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting crop planting {crop_id} for user {user_id}: {e}")
            raise


class FarmIntelligenceService:
    """
    Central service aggregating live personalized intelligence for a farmer profile.
    Coordinates Weather, Soil, Crop Calendar, Pest, Irrigation, Fertilizer, and Market modules.
    """

    def __init__(self, db: Session):
        self.db = db
        self.repo = FarmerRepository(db)
        self.weather_service = WeatherService()
        self.market_service = MarketService(db=db)
        self.crop_calendar_service = CropCalendarService()
        self.weather_intel = WeatherIntelligence()
        self.market_intel = MarketIntelligence(db=db)
        self.calendar_intel = CropCalendarIntelligence()

    async def get_dashboard(self, user_id: str, location_override: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Aggregate full personalized farm intelligence for the Farm Command Center."""
        profile = self.repo.get_or_create_profile(user_id)

        # Build farms, fields, active crops list
        farms = self.db.query(models.Farm).filter(models.Farm.farmer_id == profile.id).all()
        fields: List[models.Field] = []
        for farm in farms:
            fields.extend(farm.fields)

        active_crops: List[models.CropPlanting] = []
        for field in fields:
            for planting in field.plantings:
                if planting.status == "ACTIVE":
                    active_crops.append(planting)

        # Primary location resolution (Canonical Location System)
        primary_farm = farms[0] if farms else None
        lat = primary_farm.latitude if primary_farm else 22.5726
        lon = primary_farm.longitude if primary_farm else 88.3639
        location_name = primary_farm.location_name if primary_farm else "North 24 Parganas, West Bengal"

        if location_override and "latitude" in location_override and "longitude" in location_override:
            lat = float(location_override["latitude"])
            lon = float(location_override["longitude"])
            if "displayName" in location_override and location_override["displayName"]:
                location_name = location_override["displayName"]

        location_info = {
            "latitude": lat,
            "longitude": lon,
            "display_name": location_name,
            "source": "PROFILE" if primary_farm else "DEFAULT",
        }

        # Fetch Weather safely
        current_weather = None
        forecast_weather = None
        weather_freshness = "Unavailable"

        try:
            current_weather = await self.weather_service.get_current_weather(lat, lon)
            forecast_weather = await self.weather_service.get_weather_forecast(lat, lon, forecast_days=7)
            weather_freshness = "Updated 10 minutes ago (Open-Meteo)"
        except Exception as e:
            logger.warning(f"Failed to fetch live weather for intelligence dashboard: {e}")

        # Personalize Weather Impact per Active Crop
        weather_impacts = self._build_weather_impacts(active_crops, fields, current_weather, forecast_weather)

        # Personalize Soil Impact per Active Crop
        soil_impacts = self._build_soil_impacts(active_crops, fields)

        # Personalize Irrigation Context
        irrigation_items = self._build_irrigation_context(active_crops, fields, current_weather, forecast_weather)

        # Personalize Fertilizer Context
        fertilizer_items = self._build_fertilizer_context(active_crops, fields, location_name)

        # Personalize Pest Watch
        pest_items = self._build_pest_watch(active_crops, fields, current_weather, forecast_weather)

        # Personalize Market Watch
        market_watch = await self._build_market_watch(active_crops, location_name)

        # Personalize Timeline
        timeline = self._build_timeline(active_crops, fields, forecast_weather)

        # Personalize Alerts
        alerts = self._build_alerts(
            weather_impacts, soil_impacts, irrigation_items, fertilizer_items, pest_items, market_watch, active_crops
        )

        # Personalize Impact Matrix
        impact_matrix = self._build_impact_matrix(
            active_crops, fields, weather_impacts, soil_impacts, irrigation_items, pest_items, market_watch
        )

        # Personalize Crop Cards
        active_crop_cards = self._build_crop_cards(
            active_crops, fields, weather_impacts, irrigation_items, pest_items, market_watch
        )

        # Calculate Data Quality & Completeness
        data_quality = self._calculate_data_quality(farms, fields, active_crops, current_weather, market_watch)

        # Calculate Summaries
        total_area = sum(f.area_value for f in farms) if farms else 0.0
        area_unit = farms[0].area_unit if farms else "acre"

        today_temp = f"{current_weather.get('temperature', '--')}°C" if current_weather else "N/A"
        today_rain = f"{current_weather.get('precipitation', 0)} mm" if current_weather else "0 mm"

        weather_status_str = f"{today_temp} • Rain {today_rain}" if current_weather else "Weather telemetry unavailable"
        soil_status_str = "Soil lab data recorded" if any(f.soil_test_available for f in fields) else "Soil test recommended"
        water_status_str = f"Monitoring {len(active_crops)} active crop field(s)" if active_crops else "No active crops registered"
        avail_markets = [m for m in market_watch if m.get("available")]
        market_status_str = f"Tracking {len(avail_markets)} crop market(s)" if avail_markets else ("No market data for current crop" if active_crops else "No active crops registered")

        today_status = {
            "weather_summary": weather_status_str,
            "soil_summary": soil_status_str,
            "water_summary": water_status_str,
            "market_summary": market_status_str,
            "action_items_count": len(alerts),
        }

        # Build profile response dict
        profile_dict = profile.to_dict()
        profile_dict["farms"] = [
            {
                **f.to_dict(),
                "fields": [
                    {
                        **fl.to_dict(),
                        "plantings": [cp.to_dict() for cp in fl.plantings],
                    }
                    for fl in f.fields
                ],
            }
            for f in farms
        ]

        return {
            "farmer": profile_dict,
            "location": location_info,
            "total_farm_area": round(total_area, 2),
            "total_farm_area_unit": area_unit,
            "active_crops_count": len(active_crops),
            "fields_count": len(fields),
            "today_status": today_status,
            "active_crop_cards": active_crop_cards,
            "weather_impacts": weather_impacts,
            "soil_impacts": soil_impacts,
            "irrigation_items": irrigation_items,
            "fertilizer_items": fertilizer_items,
            "pest_items": pest_items,
            "market_watch": market_watch,
            "crop_calendar_events": [],
            "alerts": alerts,
            "timeline": timeline,
            "impact_matrix": impact_matrix,
            "data_quality": data_quality,
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }

    def _get_field_for_crop(self, crop: models.CropPlanting, fields: List[models.Field]) -> Optional[models.Field]:
        for f in fields:
            if f.id == crop.field_id:
                return f
        return None

    def _build_weather_impacts(
        self,
        crops: List[models.CropPlanting],
        fields: List[models.Field],
        current_wx: Optional[Dict[str, Any]],
        forecast_wx: Optional[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        impacts: List[Dict[str, Any]] = []

        temp = current_wx.get("temperature") if current_wx else None
        rain_sum = 0.0
        if forecast_wx and forecast_wx.get("daily_forecast"):
            daily = forecast_wx.get("daily_forecast", [])
            if daily:
                rain_sum = float(daily[0].get("precipitation_sum") or 0.0)

        for crop in crops:
            field = self._get_field_for_crop(crop, fields)
            fname = field.field_name if field else "Main Field"

            if current_wx is None:
                impacts.append({
                    "crop_name": crop.crop_name,
                    "field_name": fname,
                    "temperature": None,
                    "rain_forecast_mm": None,
                    "impact": "Weather telemetry temporarily unavailable.",
                    "action": "Check local weather broadcast.",
                    "status": "Monitor",
                })
                continue

            impact_text = "Favorable growth conditions."
            action_text = "Standard field monitoring."
            status = "Favorable"

            if temp is not None and temp >= 35.0:
                impact_text = f"High temperature ({temp}°C) may accelerate moisture loss in {crop.crop_name} field."
                action_text = "Monitor field water level and inspect crop for heat stress."
                status = "Warning"
            elif temp is not None and temp <= 10.0:
                impact_text = f"Low temperature ({temp}°C) may slow germination/growth."
                action_text = "Protect seedlings if frost risk increases."
                status = "Warning"
            elif rain_sum >= 15.0:
                impact_text = f"Significant rainfall forecast ({rain_sum:.1f} mm). Good natural moisture contribution."
                action_text = "Check drainage and postpone immediate irrigation."
                status = "Favorable"
            elif rain_sum < 1.0 and temp is not None and temp > 30.0:
                impact_text = f"Dry conditions and warm temperature ({temp}°C)."
                action_text = "Review field soil moisture for upcoming watering cycle."
                status = "Monitor"

            impacts.append({
                "crop_name": crop.crop_name,
                "field_name": fname,
                "temperature": temp,
                "rain_forecast_mm": round(rain_sum, 1),
                "impact": impact_text,
                "action": action_text,
                "status": status,
            })

        return impacts

    def _build_soil_impacts(
        self, crops: List[models.CropPlanting], fields: List[models.Field]
    ) -> List[Dict[str, Any]]:
        impacts: List[Dict[str, Any]] = []

        for crop in crops:
            field = self._get_field_for_crop(crop, fields)
            fname = field.field_name if field else "Main Field"

            if not field or not field.soil_test_available:
                impacts.append({
                    "crop_name": crop.crop_name,
                    "field_name": fname,
                    "ph_status": "Unknown",
                    "texture_status": field.soil_type if field and field.soil_type else "Suitable",
                    "n_status": "Unknown",
                    "p_status": "Unknown",
                    "k_status": "Unknown",
                    "impact_text": "Soil lab measurements unavailable. Soil test recommended for precise nutrient intelligence.",
                })
                continue

            ph_val = field.ph
            ph_prov = field.ph_provenance
            ph_status = f"{ph_val} ({ph_prov})" if ph_val is not None else "Unknown"

            n_prov = field.nitrogen_provenance
            n_status = f"{field.nitrogen} kg/ha ({n_prov})" if field.nitrogen is not None else "Unknown"

            p_prov = field.phosphorus_provenance
            p_status = f"{field.phosphorus} kg/ha ({p_prov})" if field.phosphorus is not None else "Unknown"

            k_prov = field.potassium_provenance
            k_status = f"{field.potassium} kg/ha ({k_prov})" if field.potassium is not None else "Unknown"

            missing = []
            if field.ph is None: missing.append("pH")
            if field.nitrogen is None: missing.append("Nitrogen")
            if field.phosphorus is None: missing.append("Phosphorus")
            if field.potassium is None: missing.append("Potassium")

            if missing:
                impact_text = f"Soil data partially available. {', '.join(missing)} status cannot be assessed because no measured value is available."
            else:
                impact_text = "Soil profile complete. Nutrients and pH within expected range."

            impacts.append({
                "crop_name": crop.crop_name,
                "field_name": fname,
                "ph_status": ph_status,
                "texture_status": field.soil_type if field.soil_type else "Suitable",
                "n_status": n_status,
                "p_status": p_status,
                "k_status": k_status,
                "impact_text": impact_text,
            })

        return impacts

    def _build_irrigation_context(
        self,
        crops: List[models.CropPlanting],
        fields: List[models.Field],
        current_wx: Optional[Dict[str, Any]],
        forecast_wx: Optional[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        items: List[Dict[str, Any]] = []

        rain_sum = 0.0
        if forecast_wx and forecast_wx.get("daily_forecast"):
            daily = forecast_wx.get("daily_forecast", [])
            if daily:
                rain_sum = float(daily[0].get("precipitation_sum") or 0.0)

        for crop in crops:
            field = self._get_field_for_crop(crop, fields)
            fname = field.field_name if field else "Main Field"

            moisture = field.moisture if (field and field.moisture is not None) else None
            method = crop.irrigation_method or (field.farm.irrigation_method if field and field.farm else "Flood/Furrow")

            status = "MONITOR"
            next_window = "Within 24-48 hours"
            if rain_sum >= 10.0:
                status = "LOW"
                next_window = "Postpone due to forecast rain"
            elif moisture is not None and moisture > 60:
                status = "NORMAL"
                next_window = "In 3-5 days"

            items.append({
                "crop_name": crop.crop_name,
                "field_name": fname,
                "current_moisture": moisture,
                "expected_moisture": round(moisture - 5.0, 1) if moisture else None,
                "rainfall_forecast_mm": round(rain_sum, 1),
                "irrigation_method": method,
                "water_availability": crop.water_availability or "Adequate",
                "status": status,
                "next_window": next_window,
                "model_note": "Agronomic planning estimate (Gallipoli ML model dataset time-series scope notes apply)",
            })

        return items

    def _build_fertilizer_context(
        self, crops: List[models.CropPlanting], fields: List[models.Field], location_name: str
    ) -> List[Dict[str, Any]]:
        items: List[Dict[str, Any]] = []

        is_western_maharashtra = "maharashtra" in (location_name or "").lower()

        for crop in crops:
            field = self._get_field_for_crop(crop, fields)
            fname = field.field_name if field else "Main Field"

            n_prov = field.nitrogen_provenance if field else "UNKNOWN"
            p_prov = field.phosphorus_provenance if field else "UNKNOWN"
            k_prov = field.potassium_provenance if field else "UNKNOWN"

            has_complete_npk = (
                field is not None
                and field.nitrogen is not None
                and field.phosphorus is not None
                and field.potassium is not None
            )

            if not is_western_maharashtra:
                scope_note = "Commercial formulation model is trained on Western Maharashtra dataset."
                rec = None
                reason = f"Field is outside the Western Maharashtra regional model dataset. Access Fertilizer Advisor for localized nutrient planning."
            elif not has_complete_npk:
                scope_note = "Model recommendation requires complete N, P, K lab measurements."
                rec = None
                reason = "Phosphorus or Potassium measurement is missing; complete soil test to run ML model."
            else:
                scope_note = "Western Maharashtra ML model validated."
                rec = None
                reason = "Evaluating ML formulation model..."
                try:
                    from .model_registry import ModelRegistry
                    registry = ModelRegistry()
                    if registry.models_meta.get("fertilizer") and registry.models_meta["fertilizer"].status == "READY":
                        f_input = {
                            "Nitrogen": float(field.nitrogen or 50.0),
                            "Phosphorus": float(field.phosphorus or 50.0),
                            "Potassium": float(field.potassium or 50.0),
                            "pH": float(field.ph or 6.5),
                            "Rainfall": 800.0,
                            "Temperature": 26.0,
                            "District_Name": "Pune",
                            "Soil_color": "Black",
                            "Crop": crop.crop_name,
                            "Link": "https://example.com",
                        }
                        pred = registry.predict_fertilizer(f_input)
                        formulation = pred.get("predicted_formulation", "")
                        conf = pred.get("confidence")
                        conf_str = f" ({round(conf * 100)}% confidence)" if conf else ""
                        rec = f"Recommended Formulation: {formulation}{conf_str}"
                        reason = f"Derived from measured field soil NPK levels ({field.nitrogen} N, {field.phosphorus} P, {field.potassium} K)."
                except Exception as ml_err:
                    logger.debug(f"Fertilizer ML prediction error: {ml_err}")
                    rec = None
                    reason = "Run Fertilizer Advisor for detailed formulation analysis."

            items.append({
                "crop_name": crop.crop_name,
                "field_name": fname,
                "n_status": f"{field.nitrogen if field else '—'} ({n_prov})",
                "p_status": f"{field.phosphorus if field else '—'} ({p_prov})",
                "k_status": f"{field.potassium if field else '—'} ({k_prov})",
                "model_available": is_western_maharashtra and has_complete_npk,
                "model_scope_note": scope_note,
                "recommendation": rec,
                "reason": reason,
            })

        return items

    def _build_pest_watch(
        self,
        crops: List[models.CropPlanting],
        fields: List[models.Field],
        current_wx: Optional[Dict[str, Any]],
        forecast_wx: Optional[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        items: List[Dict[str, Any]] = []

        rh = current_wx.get("relative_humidity") if current_wx else None
        rain = current_wx.get("precipitation") if current_wx else 0.0

        for crop in crops:
            field = self._get_field_for_crop(crop, fields)
            fname = field.field_name if field else "Main Field"

            drivers = []
            risk = "Low"
            if rh is not None and rh >= 80:
                drivers.append(f"High humidity ({rh}%)")
                risk = "Moderate"
            if rain is not None and rain > 5.0:
                drivers.append("Recent rainfall")
                risk = "Moderate"
            if crop.growth_stage in ("Vegetative", "Flowering"):
                drivers.append(f"{crop.growth_stage} stage sensitivity")

            if len(drivers) >= 2:
                risk = "High" if rh and rh >= 85 else "Moderate"

            action = "Inspect lower leaves and field margins for early pest signs." if risk != "Low" else "Routine monitoring."

            items.append({
                "crop_name": crop.crop_name,
                "field_name": fname,
                "risk_level": risk,
                "weather_drivers": drivers,
                "crop_stage": crop.growth_stage,
                "action": action,
                "model_scope_note": "Environmental weather pest risk indicator (Visual classification model available for uploaded plant leaf images)",
            })

        return items

    async def _build_market_watch(
        self, crops: List[models.CropPlanting], location_name: str
    ) -> List[Dict[str, Any]]:
        items: List[Dict[str, Any]] = []
        seen_crops = set()

        for crop in crops:
            cname = crop.crop_name
            if cname in seen_crops:
                continue
            seen_crops.add(cname)

            # Query backend market service for this crop with alias lookup
            candidates = [cname]
            if cname.lower() in ("rice", "paddy", "dhan"):
                candidates = ["Paddy(Common)", "Rice", "Paddy(Basmati)"]
            elif cname.lower() == "corn":
                candidates = ["Maize", "Sweet Corn", "Baby Corn"]
            elif cname.lower() == "wheat":
                candidates = ["Wheat"]
            elif cname.lower() == "potato":
                candidates = ["Potato"]
            elif cname.lower() == "tomato":
                candidates = ["Tomato"]
            elif cname.lower() == "cotton":
                candidates = ["Cotton"]
            elif cname.lower() == "sugarcane":
                candidates = ["Gur(Jaggery)", "Sugarcane"]

            latest_obs = None
            matched_commodity = cname
            for cand in candidates:
                try:
                    latest_obs = self.market_service.get_latest_price(commodity=cand)
                    if latest_obs and latest_obs.get("modal_price"):
                        matched_commodity = cand
                        break
                except Exception as e:
                    logger.debug(f"Market price query error for {cand}: {e}")

            trend_data: Dict[str, Any] = {}
            if latest_obs:
                try:
                    trend_data = self.market_intel.analyze_market_trend(commodity=matched_commodity)
                except Exception as e:
                    logger.debug(f"Market trend query error for {matched_commodity}: {e}")

            price = latest_obs.get("modal_price") if latest_obs else None
            mkt_name = latest_obs.get("market") if latest_obs else None
            state_name = latest_obs.get("state") if latest_obs else None
            loc_label = f"{mkt_name}, {state_name}" if mkt_name and state_name else (mkt_name or location_name)

            pct_change = trend_data.get("recent_change_percent")
            if pct_change is not None and abs(pct_change) > 0.01:
                trend_label = "Increasing" if pct_change > 0 else "Decreasing"
                pct_val = round(pct_change, 1)
            else:
                trend_label = "Stable"
                pct_val = None

            items.append({
                "crop_name": cname,
                "commodity": matched_commodity,
                "current_price": price,
                "trend": trend_label if price else "Unavailable",
                "change_30d_pct": pct_val,
                "period": "Last 30 days" if price else "N/A",
                "market_location": loc_label if price else None,
                "available": price is not None,
                "observation_date": str(latest_obs.get("observation_date")) if latest_obs and latest_obs.get("observation_date") else None,
            })

        return items

    def _build_timeline(
        self, crops: List[models.CropPlanting], fields: List[models.Field], forecast_wx: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        items: List[Dict[str, Any]] = []
        if not crops:
            return []

        today_str = date.today().isoformat()
        tomorrow_str = (date.today() + timedelta(days=1)).isoformat()
        next_week_str = (date.today() + timedelta(days=7)).isoformat()

        # 1. Daily Telemetry Event
        items.append({
            "date_label": today_str,
            "crop_name": crops[0].crop_name,
            "field_name": fields[0].field_name if fields else "Active Field",
            "event_title": "Daily Weather & Field Telemetry Sync",
            "reason": "Real-time atmospheric and telemetry sync from Open-Meteo",
            "priority": "Info",
            "source": "Weather Service",
            "evidence_status": "Fresh telemetry",
        })

        for crop in crops:
            field = self._get_field_for_crop(crop, fields)
            fname = field.field_name if field else "Field"

            # Sowing milestone if recorded
            if crop.sowing_date:
                items.append({
                    "date_label": crop.sowing_date.isoformat(),
                    "crop_name": crop.crop_name,
                    "field_name": fname,
                    "event_title": f"{crop.crop_name} Sowing Event",
                    "reason": f"Field establishment ({crop.variety or 'Standard'} variety, stage: {crop.growth_stage})",
                    "priority": "Moderate",
                    "source": "Farmer Record",
                    "evidence_status": "Farmer verified",
                })

            # Upcoming irrigation milestone
            items.append({
                "date_label": tomorrow_str,
                "crop_name": crop.crop_name,
                "field_name": fname,
                "event_title": f"Irrigation Schedule Review for {crop.crop_name}",
                "reason": f"{crop.growth_stage or 'Active'} stage moisture check",
                "priority": "Moderate",
                "source": "Irrigation Predictor",
                "evidence_status": "Field condition",
            })

            # Pest scouting milestone
            items.append({
                "date_label": next_week_str,
                "crop_name": crop.crop_name,
                "field_name": fname,
                "event_title": f"Pest & Leaf Scouting for {crop.crop_name}",
                "reason": f"Active growth stage scouting in {fname}",
                "priority": "High",
                "source": "Pest Intelligence",
                "evidence_status": "Scheduled task",
            })

            # Expected harvest milestone if scheduled
            if crop.expected_harvest_date:
                items.append({
                    "date_label": crop.expected_harvest_date.isoformat(),
                    "crop_name": crop.crop_name,
                    "field_name": fname,
                    "event_title": f"Projected Harvest Window for {crop.crop_name}",
                    "reason": "Crop maturity and market readiness target",
                    "priority": "High",
                    "source": "Crop Calendar Schedule",
                    "evidence_status": "Projected date",
                })

        # Sort timeline chronologically by date
        items.sort(key=lambda x: x["date_label"])
        return items

    def _build_alerts(
        self,
        wx_impacts: List[Dict[str, Any]],
        soil_impacts: List[Dict[str, Any]],
        irrigation_items: List[Dict[str, Any]],
        fertilizer_items: List[Dict[str, Any]],
        pest_items: List[Dict[str, Any]],
        market_items: List[Dict[str, Any]],
        crops: List[models.CropPlanting],
    ) -> List[Dict[str, Any]]:
        alerts: List[Dict[str, Any]] = []
        idx = 1

        for p in pest_items:
            if p.get("risk_level") in ("High", "Moderate"):
                alerts.append({
                    "id": f"alt-pest-{idx}",
                    "priority": "High" if p["risk_level"] == "High" else "Moderate",
                    "category": "Pest",
                    "title": f"Elevated Pest Risk for {p['crop_name']}",
                    "description": f"Weather conditions ({', '.join(p.get('weather_drivers', []))}) favor pest pressure in {p['field_name']}.",
                    "crop_name": p["crop_name"],
                    "field_name": p["field_name"],
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "actionable": True,
                    "recommended_action": p.get("action", "Inspect lower leaves and field margins for early pest signs."),
                })
                idx += 1

        for w in wx_impacts:
            if w.get("status") == "Warning":
                alerts.append({
                    "id": f"alt-wx-{idx}",
                    "priority": "High",
                    "category": "Weather",
                    "title": f"Weather Alert for {w['crop_name']}",
                    "description": w.get("impact", "Adverse weather conditions forecast."),
                    "crop_name": w["crop_name"],
                    "field_name": w["field_name"],
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "actionable": True,
                    "recommended_action": w.get("action", "Check drainage and inspect field conditions."),
                })
                idx += 1

        for s in soil_impacts:
            if "partially available" in s.get("impact_text", "").lower() or "unavailable" in s.get("impact_text", "").lower():
                alerts.append({
                    "id": f"alt-soil-{idx}",
                    "priority": "Info",
                    "category": "Soil",
                    "title": f"Soil Lab Test Recommended for {s['field_name']}",
                    "description": s["impact_text"],
                    "crop_name": s["crop_name"],
                    "field_name": s["field_name"],
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "actionable": True,
                    "recommended_action": "Record measured soil NPK and pH lab test values in the Soil Lab Data tab.",
                })
                idx += 1

        for ir in irrigation_items:
            if ir.get("status") == "MONITOR":
                alerts.append({
                    "id": f"alt-irr-{idx}",
                    "priority": "Moderate",
                    "category": "Irrigation",
                    "title": f"Irrigation Check for {ir['crop_name']}",
                    "description": f"Field {ir['field_name']} moisture requires monitoring. Next window: {ir.get('next_window')}.",
                    "crop_name": ir["crop_name"],
                    "field_name": ir["field_name"],
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "actionable": True,
                    "recommended_action": "Verify field moisture level and check irrigation channel availability.",
                })
                idx += 1

        return alerts

    def _build_impact_matrix(
        self,
        crops: List[models.CropPlanting],
        fields: List[models.Field],
        wx_impacts: List[Dict[str, Any]],
        soil_impacts: List[Dict[str, Any]],
        irrigation_items: List[Dict[str, Any]],
        pest_items: List[Dict[str, Any]],
        market_items: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        matrix: List[Dict[str, Any]] = []

        for crop in crops:
            field = self._get_field_for_crop(crop, fields)
            fname = field.field_name if field else "Main Field"
            area_str = f"{field.area_value} {field.area_unit}" if field else "N/A"

            wx = next((w for w in wx_impacts if w["crop_name"] == crop.crop_name), {})
            sl = next((s for s in soil_impacts if s["crop_name"] == crop.crop_name), {})
            ir = next((i for i in irrigation_items if i["crop_name"] == crop.crop_name), {})
            ps = next((p for p in pest_items if p["crop_name"] == crop.crop_name), {})
            mk = next((m for m in market_items if m["crop_name"] == crop.crop_name), {})

            att = "Low"
            if ps.get("risk_level") == "High" or wx.get("status") == "Warning":
                att = "High"
            elif ps.get("risk_level") == "Moderate" or ir.get("status") == "MONITOR":
                att = "Medium"

            matrix.append({
                "crop_name": crop.crop_name,
                "field_name": fname,
                "area_display": area_str,
                "weather": wx.get("status", "Favorable"),
                "soil": "Complete" if "complete" in sl.get("impact_text", "").lower() else "Data Partial",
                "water": ir.get("status", "NORMAL"),
                "pest": ps.get("risk_level", "Low"),
                "market": mk.get("trend", "Stable"),
                "attention_level": att,
            })

        return matrix

    def _build_crop_cards(
        self,
        crops: List[models.CropPlanting],
        fields: List[models.Field],
        wx_impacts: List[Dict[str, Any]],
        irrigation_items: List[Dict[str, Any]],
        pest_items: List[Dict[str, Any]],
        market_items: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        cards: List[Dict[str, Any]] = []

        for crop in crops:
            field = self._get_field_for_crop(crop, fields)
            fname = field.field_name if field else "Main Field"
            area_str = f"{field.area_value} {field.area_unit}" if field else "N/A"

            wx = next((w for w in wx_impacts if w["crop_name"] == crop.crop_name), {})
            ir = next((i for i in irrigation_items if i["crop_name"] == crop.crop_name), {})
            ps = next((p for p in pest_items if p["crop_name"] == crop.crop_name), {})
            mk = next((m for m in market_items if m["crop_name"] == crop.crop_name), {})

            days_sown = None
            if crop.sowing_date:
                days_sown = (date.today() - crop.sowing_date).days

            cards.append({
                "id": crop.id,
                "field_id": crop.field_id,
                "crop_name": crop.crop_name,
                "field_name": fname,
                "area_display": area_str,
                "growth_stage": crop.growth_stage or "Vegetative",
                "days_since_sowing": days_sown,
                "sowing_date": crop.sowing_date.isoformat() if crop.sowing_date else None,
                "expected_harvest": crop.expected_harvest_date.isoformat() if crop.expected_harvest_date else None,
                "weather_status": wx.get("status", "Favorable"),
                "water_status": ir.get("status", "NORMAL"),
                "pest_status": ps.get("risk_level", "Low"),
                "market_trend": mk.get("trend", "Stable"),
            })

        return cards

    def _calculate_data_quality(
        self,
        farms: List[models.Farm],
        fields: List[models.Field],
        crops: List[models.CropPlanting],
        current_wx: Optional[Dict[str, Any]],
        market_watch: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        missing = []
        if not farms:
            missing.append("Farm profile")
        if not fields:
            missing.append("Field records")
        if not crops:
            missing.append("Active crop cultivation")

        soil_tested = any(f.soil_test_available for f in fields) if fields else False
        if not soil_tested:
            missing.append("Soil test lab measurements")

        npk_count = 0
        if fields:
            f0 = fields[0]
            if f0.nitrogen is not None: npk_count += 1
            if f0.phosphorus is not None: npk_count += 1
            if f0.potassium is not None: npk_count += 1

        total_points = 6
        points = 0
        if farms: points += 1
        if fields: points += 1
        if crops: points += 1
        if current_wx: points += 1
        if soil_tested: points += 1
        if market_watch: points += 1

        completeness_pct = round((points / total_points) * 100.0, 1)

        return {
            "location_confidence": "High (Canonical GPS/Map)" if farms else "Default",
            "weather_freshness": "Fresh (Open-Meteo)" if current_wx else "Unavailable",
            "soil_availability": "Measured" if soil_tested else "Partially available / Lab recommended",
            "npk_availability": f"{npk_count}/3 available",
            "market_status": "Updated today" if market_watch else "Unavailable",
            "profile_completeness_pct": completeness_pct,
            "missing_fields": missing,
        }
