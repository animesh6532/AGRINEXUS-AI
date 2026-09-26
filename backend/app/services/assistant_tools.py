"""
Assistant Tools Layer for AgriNexus-AI Farm AI Copilot.

Provides a controlled, safe adapter layer between the AI Copilot and existing
AgriNexus-AI backend services and database models.
"""

import logging
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.database.connection import SessionLocal
from app.database.models import FarmerProfile, Farm, Field, CropPlanting
from app.services.farmer_service import FarmIntelligenceService
from app.services.weather_service import WeatherService
from app.services.irrigation_intelligence import IrrigationIntelligenceService
from app.services.model_registry import ModelRegistry

logger = logging.getLogger(__name__)



class AssistantTools:
    """Central registry of backend tool functions for the AI Copilot."""

    @staticmethod
    def get_farmer_profile(user_id: str, db: Optional[Session] = None) -> Dict[str, Any]:
        """Fetch authenticated farmer profile."""
        session = db or SessionLocal()
        try:
            profile = session.query(FarmerProfile).filter(FarmerProfile.user_id == user_id).first()
            if not profile:
                return {"status": "not_found", "message": "No farmer profile configured yet."}
            return {"status": "success", "profile": profile.to_dict()}
        except Exception as e:
            logger.error("Error fetching farmer profile for user %s: %s", user_id, e)
            return {"status": "error", "message": str(e)}
        finally:
            if not db:
                session.close()

    @staticmethod
    def get_farm_summary(user_id: str, db: Optional[Session] = None) -> Dict[str, Any]:
        """Fetch summary of user's farms, fields, and active crops."""
        session = db or SessionLocal()
        try:
            profile = session.query(FarmerProfile).filter(FarmerProfile.user_id == user_id).first()
            if not profile:
                return {"status": "not_found", "farms": [], "total_fields": 0, "active_crops": []}

            farms = session.query(Farm).filter(Farm.farmer_id == profile.id).all()
            farm_list = []
            all_fields = []
            active_crops = []

            for f in farms:
                fields = session.query(Field).filter(Field.farm_id == f.id).all()
                all_fields.extend(fields)
                for fld in fields:
                    plantings = session.query(CropPlanting).filter(
                        CropPlanting.field_id == fld.id, CropPlanting.status == "ACTIVE"
                    ).all()
                    for p in plantings:
                        active_crops.append({
                            "id": p.id,
                            "crop_name": p.crop_name,
                            "variety": p.variety,
                            "growth_stage": p.growth_stage,
                            "field_id": fld.id,
                            "field_name": fld.field_name,
                            "farm_name": f.farm_name,
                        })

                farm_list.append({
                    "id": f.id,
                    "name": f.farm_name,
                    "location": f.location_name,
                    "latitude": f.latitude,
                    "longitude": f.longitude,
                    "area": f"{f.area_value} {f.area_unit}",
                    "water_source": f.water_source,
                    "field_count": len(fields),
                })

            return {
                "status": "success",
                "farmer_name": profile.full_name,
                "preferred_language": profile.preferred_language,
                "farm_count": len(farm_list),
                "farms": farm_list,
                "total_fields": len(all_fields),
                "active_crops": active_crops,
            }
        except Exception as e:
            logger.error("Error in get_farm_summary for %s: %s", user_id, e)
            return {"status": "error", "message": str(e)}
        finally:
            if not db:
                session.close()

    @staticmethod
    def get_field_details(user_id: str, field_id: int, db: Optional[Session] = None) -> Dict[str, Any]:
        """Fetch details and soil telemetry for a specific field owned by the user."""
        session = db or SessionLocal()
        try:
            profile = session.query(FarmerProfile).filter(FarmerProfile.user_id == user_id).first()
            if not profile:
                return {"status": "error", "message": "Unauthorized or no profile."}

            field = session.query(Field).join(Farm).filter(Field.id == field_id, Farm.farmer_id == profile.id).first()
            if not field:
                return {"status": "not_found", "message": f"Field #{field_id} not found."}

            active_crop = session.query(CropPlanting).filter(
                CropPlanting.field_id == field.id, CropPlanting.status == "ACTIVE"
            ).first()

            return {
                "status": "success",
                "field": field.to_dict(),
                "active_crop": active_crop.to_dict() if active_crop else None,
            }
        except Exception as e:
            logger.error("Error in get_field_details for field %d: %s", field_id, e)
            return {"status": "error", "message": str(e)}
        finally:
            if not db:
                session.close()

    @staticmethod
    def get_active_crops(user_id: str, db: Optional[Session] = None) -> Dict[str, Any]:
        """Fetch list of all currently active crops across fields."""
        summary = AssistantTools.get_farm_summary(user_id, db=db)
        return {"status": "success", "active_crops": summary.get("active_crops", [])}

    @staticmethod
    def get_farm_dashboard(user_id: str, lat: Optional[float] = None, lon: Optional[float] = None) -> Dict[str, Any]:
        """Fetch aggregated Farm Command Center dashboard data."""
        session = SessionLocal()
        try:
            intel_service = FarmIntelligenceService(db=session)
            summary = AssistantTools.get_farm_summary(user_id, db=session)
            return {"status": "success", "dashboard": summary}
        except Exception as e:
            logger.error("Error fetching farm dashboard for user %s: %s", user_id, e)
            return {"status": "error", "message": str(e)}
        finally:
            session.close()


    @staticmethod
    def get_weather_current(lat: float, lon: float) -> Dict[str, Any]:
        """Fetch current weather for coordinates."""
        try:
            from app.services.async_bridge import run_async
            ws = WeatherService()
            w = run_async(ws.get_current_weather(latitude=lat, longitude=lon))
            return {"status": "success", "data": w}
        except Exception as e:
            logger.error("Error fetching current weather: %s", e)
            return {"status": "error", "message": str(e)}

    @staticmethod
    def get_weather_forecast(lat: float, lon: float, days: int = 7) -> Dict[str, Any]:
        """Fetch 7-day weather forecast."""
        try:
            from app.services.async_bridge import run_async
            ws = WeatherService()
            wf = run_async(ws.get_weather_forecast(latitude=lat, longitude=lon, forecast_days=days))
            return {"status": "success", "data": wf}
        except Exception as e:
            logger.error("Error fetching weather forecast: %s", e)
            return {"status": "error", "message": str(e)}

    @staticmethod
    def get_weather_agricultural_insights(lat: float, lon: float) -> Dict[str, Any]:
        """Fetch agromet agricultural weather insights."""
        try:
            from app.intelligence.weather_intelligence import WeatherIntelligence
            wi = WeatherIntelligence()
            insights = wi.generate_insights(lat, lon)
            return {"status": "success", "insights": insights}
        except Exception as e:
            logger.error("Error fetching weather insights: %s", e)
            return {"status": "error", "message": str(e)}



    @staticmethod
    def get_market_current(commodity: str, state: Optional[str] = None) -> Dict[str, Any]:
        """Fetch current market mandi price."""
        try:
            from app.database import connection
            from app.services.market_service import MarketService
            with connection.SessionLocal() as db:
                ms = MarketService(db)
                m = ms.get_latest_price(commodity=commodity, state=state)
                return {"status": "success", "data": m}
        except Exception as e:
            logger.error("Error fetching market current: %s", e)
            return {"status": "error", "message": str(e)}

    @staticmethod
    def get_market_history(commodity: str) -> Dict[str, Any]:
        """Fetch historical market price records."""
        try:
            from app.database import connection
            from app.services.market_service import MarketService
            with connection.SessionLocal() as db:
                ms = MarketService(db)
                records = ms.get_historical_prices(commodity=commodity)
                return {"status": "success", "history": records[:10]}
        except Exception as e:
            logger.error("Error fetching market history: %s", e)
            return {"status": "error", "message": str(e)}

    @staticmethod
    def get_market_forecast(commodity: str, horizon: int = 7, model: str = "ets") -> Dict[str, Any]:
        """Fetch market price forecast."""
        try:
            from app.database import connection
            from app.forecasting.forecast_service import ForecastService
            from app.services.async_bridge import run_async
            with connection.SessionLocal() as db:
                fs = ForecastService(db)
                fc = run_async(fs.generate_forecast(commodity=commodity, horizon_days=horizon, model_type=model))
                return {"status": "success", "commodity": commodity, "horizon": horizon, "model": model}
        except Exception as e:
            logger.error("Error fetching market forecast: %s", e)
            return {"status": "error", "message": str(e)}

    @staticmethod
    def get_crop_calendar() -> Dict[str, Any]:
        """Fetch crop calendar catalogue."""
        try:
            cat = CropCalendarService.get_catalogue()
            return {"status": "success", "catalogue": cat}
        except Exception as e:
            logger.error("Error fetching crop calendar catalogue: %s", e)
            return {"status": "error", "message": str(e)}

    @staticmethod
    def get_crop_schedule(crop: str, sowing_date: str, season: Optional[str] = None) -> Dict[str, Any]:
        """Fetch personalized crop schedule."""
        try:
            sched = CropCalendarService.get_schedule(crop=crop, sowing_date=sowing_date, season=season)
            return {"status": "success", "schedule": sched}
        except Exception as e:
            logger.error("Error fetching crop schedule: %s", e)
            return {"status": "error", "message": str(e)}

    @staticmethod
    def get_smart_crop_recommendation(payload: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch smart crop recommendation."""
        try:
            reg = ModelRegistry()
            res = reg.predict_crop(payload)
            return {"status": "success", "recommendation": res}
        except Exception as e:
            logger.error("Error predicting crop recommendation: %s", e)
            return {"status": "error", "message": str(e)}

    @staticmethod
    def get_irrigation_intelligence(field_id: Optional[int] = None, lat: Optional[float] = None, lon: Optional[float] = None, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Fetch irrigation intelligence & SWC forecast."""
        from app.database.connection import SessionLocal
        session = SessionLocal()
        try:
            from app.services.async_bridge import run_async
            svc = IrrigationIntelligenceService(session)
            res = run_async(svc.get_intelligence(user_id=user_id or "default_farmer", field_id=field_id, lat=lat, lon=lon))
            return {"status": "success", "data": res}
        except Exception as e:
            logger.error("Error fetching irrigation intelligence: %s", e)
            return {"status": "error", "message": str(e)}
        finally:
            session.close()

    @staticmethod
    def get_fertilizer_recommendation(payload: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch fertilizer recommendation."""
        try:
            reg = ModelRegistry()
            res = reg.predict_fertilizer(payload)
            return {"status": "success", "recommendation": res}
        except Exception as e:
            logger.error("Error predicting fertilizer: %s", e)
            return {"status": "error", "message": str(e)}

    @staticmethod
    def get_pest_environmental_risk(payload: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch environmental pest risk analysis."""
        try:
            reg = ModelRegistry()
            res = reg.predict_pest_risk(payload)
            return {"status": "success", "pest_risk": res}
        except Exception as e:
            logger.error("Error predicting pest risk: %s", e)
            return {"status": "error", "message": str(e)}

    @staticmethod
    def get_disease_model_guidance(disease_name: Optional[str] = None) -> Dict[str, Any]:
        """Fetch AI disease model limitations & domain guidance."""
        return {
            "status": "success",
            "model_type": "AI-Assisted Leaf Disease Classifier",
            "limitations": [
                "Supports documented crop disease classes in offline registry",
                "Outdoor field lighting and shadows can cause domain shift",
                "Verify leaf symptoms with local agricultural extension officers for major outbreaks"
            ]
        }

    @staticmethod
    def get_soil_analysis(payload: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze soil parameters and return suitability evaluation."""
        try:
            reg = ModelRegistry()
            res = reg.predict_soil(payload)
            return {"status": "success", "soil_analysis": res}
        except Exception as e:
            logger.error("Error analyzing soil: %s", e)
            return {"status": "error", "message": str(e)}

    @staticmethod
    def get_yield_prediction(payload: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch ML yield prediction."""
        try:
            reg = ModelRegistry()
            res = reg.predict_yield(payload)
            return {"status": "success", "yield_prediction": res}
        except Exception as e:
            logger.error("Error predicting yield: %s", e)
            return {"status": "error", "message": str(e)}

            return {"status": "success", "yield_prediction": res}
        except Exception as e:
            logger.error("Error predicting yield: %s", e)
            return {"status": "error", "message": str(e)}

    @staticmethod
    def get_data_quality(user_id: str, field_id: Optional[int] = None) -> Dict[str, Any]:
        """Return data quality & missing soil parameter report."""
        summary = AssistantTools.get_farm_summary(user_id)
        if field_id:
            fld = AssistantTools.get_field_details(user_id, field_id)
            if fld.get("status") == "success":
                s_data = fld.get("field", {}).get("soil_data", {})
                missing = [k for k, v in s_data.items() if v.get("provenance") == "UNKNOWN"]
                return {
                    "status": "success",
                    "field_id": field_id,
                    "measured_params": [k for k, v in s_data.items() if v.get("provenance") == "MEASURED"],
                    "estimated_params": [k for k, v in s_data.items() if v.get("provenance") == "ESTIMATED"],
                    "unknown_params": missing,
                    "completeness": round((len(s_data) - len(missing)) / len(s_data) * 100, 1) if s_data else 0
                }
        return {"status": "success", "total_farms": summary.get("farm_count", 0)}

    @staticmethod
    def get_location_context(user_id: str, lat: Optional[float] = None, lon: Optional[float] = None) -> Dict[str, Any]:
        """Fetch current location context for user."""
        summary = AssistantTools.get_farm_summary(user_id)
        farms = summary.get("farms", [])
        if farms:
            first = farms[0]
            return {
                "status": "success",
                "location_name": first.get("location"),
                "latitude": first.get("latitude"),
                "longitude": first.get("longitude"),
                "source": "Registered Farm Location"
            }
        return {
            "status": "success",
            "location_name": "Default AgriNexus Region",
            "latitude": lat or 22.5726,
            "longitude": lon or 88.3639,
            "source": "Default/Current Context"
        }

    @staticmethod
    def get_field_alerts(user_id: str) -> Dict[str, Any]:
        """Fetch active alerts for farmer's fields."""
        from app.database.connection import SessionLocal
        session = SessionLocal()
        try:
            from app.services.async_bridge import run_async
            svc = FarmIntelligenceService(db=session)
            dash = run_async(svc.get_dashboard(user_id=user_id))
            alerts = dash.get("alerts", [])
            return {"status": "success", "alerts": alerts}
        except Exception as e:
            return {"status": "error", "message": str(e)}
        finally:
            session.close()

    @staticmethod
    def get_farm_timeline(user_id: str) -> Dict[str, Any]:
        """Fetch farm operational timeline."""
        summary = AssistantTools.get_farm_summary(user_id)
        crops = summary.get("active_crops", [])
        events = []
        for c in crops:
            events.append({
                "crop": c.get("crop_name"),
                "stage": c.get("growth_stage"),
                "field": c.get("field_name"),
                "farm": c.get("farm_name"),
            })
        return {"status": "success", "timeline": events}
