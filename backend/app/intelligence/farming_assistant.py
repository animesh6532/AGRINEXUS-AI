"""
Farming Assistant Intelligence Layer.

Responsibilities:
1. Farming-only scope gate (redirect non-agricultural queries).
2. Intent classification and dynamic question routing:
   - Dynamic Farm Query: Personalized Action Plan, Smart Alerts, Risk & Opportunity, Decision Engine, Weather, Market.
   - Static Knowledge Query: Vector search over the 10,000+ agricultural knowledge base.
3. Agronomic entity extraction (crops, growth stages, topics).
4. Grounded answer synthesis without hallucination or invented facts.
5. Strict adherence to AGRINEXUS deterministic rules (never duplicating rule logic).
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from app.schemas.action_plan import ActionPlanResponse
from app.schemas.decision import DecisionResponse, FarmContext
from app.schemas.farming_assistant import (
    AssistantIntent,
    ChatRequest,
    ChatResponse,
    FarmingKnowledgeMatch,
    KnowledgeSourceInfo,
)
from app.schemas.risk_opportunity import RiskOpportunityResponse
from app.schemas.smart_alert import SmartAlertResponse

ENGINE_VERSION = "1.0.0"

# Scope definition: Agronomic keywords and topics supported by AgriNexus-AI
FARMING_KEYWORDS = {
    # Crops
    "rice", "paddy", "wheat", "maize", "corn", "cotton", "soybean", "sugarcane",
    "pulses", "gram", "mustard", "potato", "potatoes", "tomato", "tomatoes", "onion", "onions",
    "chilli", "chillies", "barley", "millet", "sorghum", "groundnut", "tea", "coffee", "jute",
    "cassava", "banana", "bananas", "beans", "bean", "apple", "apples", "mango", "mangoes",
    "citrus", "guava", "cabbage", "carrot", "pea", "peas",
    "vegetable", "vegetables", "fruit", "fruits", "grain", "grains",
    "crop", "crops", "plantation", "variety", "hybrid", "seed", "seeds",
    "farming", "farmer", "agriculture", "agricultural", "field", "farm",
    # Soil & Land
    "soil", "loam", "clay", "sand", "ph", "acidity", "alkalinity", "salinity",
    "organic matter", "humus", "fertility", "soil health", "soil test", "drainage",
    "plowing", "tillage", "mulch", "mulching",
    # Nutrition & Fertilizer
    "fertilizer", "fertilizers", "npk", "nitrogen", "phosphorus", "potassium",
    "urea", "dap", "potash", "manure", "compost", "micronutrient", "zinc",
    "iron", "deficiency", "chlorosis", "nutrient", "fertilization",
    # Water & Irrigation
    "irrigation", "irrigate", "water", "watering", "drip", "sprinkler", "flood",
    "moisture", "drought", "dry", "waterlogging", "evapotranspiration",
    # Plant Health & Protection
    "pest", "pests", "insect", "insects", "disease", "diseases", "fungus",
    "fungal", "bacterial", "virus", "viral", "blight", "blast", "rust",
    "mildew", "rot", "wilt", "borer", "aphid", "whitefly", "caterpillar",
    "armyworm", "thrips", "mite", "weevil", "locust", "mosaic", "anthracnose", "canker", "smut",
    "weed", "weeds", "herbicide", "pesticide", "fungicide", "infestation",
    "symptom", "symptoms", "yellow", "yellowing", "spot", "spots", "leaf", "leaves",
    # Farm Operations & Practices
    "sowing", "sow", "plant", "planting", "transplant", "transplanting",
    "harvest", "harvesting", "yield", "storage", "post-harvest", "rotation",
    "crop rotation", "intercropping", "agroforestry", "spacing", "germination", "flowering",
    "tillering", "maturity", "growth", "stage", "silage", "fodder", "livestock",
    # Agro-climate & Market
    "weather", "rain", "rainfall", "temperature", "frost", "heat", "humidity",
    "market", "mandi", "price", "prices", "commodity", "selling", "profit",
    # Dynamic farm intent triggers
    "alert", "alerts", "risk", "risks", "opportunity", "opportunities",
    "recommendation", "action", "today", "farm", "field", "advisory", "plan",
    "decision", "situation", "status", "do today", "check"
}

NON_FARMING_REDIRECT = (
    "I'm your farming assistant. I can help with crops, soil, irrigation, pests, "
    "diseases, fertilizer, weather, markets, harvesting, and farm management."
)

FALLBACK_NO_MATCH = (
    "I couldn't find sufficiently relevant information in my farming knowledge base "
    "for that question. Please provide more details about the crop, growth stage, "
    "symptoms, or farming situation."
)

SUPPORTED_CROPS = [
    "rice", "wheat", "maize", "cotton", "pulses", "soybean", "sugarcane",
    "potato", "tomato", "onion", "mustard", "groundnut", "barley", "millet"
]

SUPPORTED_TOPICS = [
    "crops", "soil", "fertilizer", "irrigation", "disease", "pest",
    "crop_management", "weather", "harvest", "farm_management", "market"
]


def is_farming_query(text: str) -> bool:
    """Determine whether the natural language text falls within agricultural scope."""
    cleaned = re.sub(r"[^\w\s]", " ", text.lower())
    tokens = set(cleaned.split())
    if not tokens:
        return False

    # Direct keyword or phrase intersection
    for kw in FARMING_KEYWORDS:
        if " " in kw:
            if kw in cleaned:
                return True
        elif kw in tokens:
            return True

    return False


def classify_assistant_intent(
    query: str,
    request: ChatRequest
) -> AssistantIntent:
    """
    Route query between static knowledge base and existing dynamic AGRINEXUS modules.
    
    Dynamic Routing Rules (Section 18 & 19):
    - Questions about 'today', 'what should I do', 'my actions' -> DYNAMIC_ACTION_PLAN
    - Questions about 'risks', 'my alerts', 'why alert' -> DYNAMIC_RISKS_ALERTS
    - Questions about 'why irrigate', 'my decision', 'recommendation' -> DYNAMIC_DECISION
    - Questions about current weather -> DYNAMIC_WEATHER
    - Questions about current market price/status -> DYNAMIC_MARKET
    - General agronomic queries ("What is NPK?", "What is rice blast?") -> STATIC_KNOWLEDGE
    """
    q = query.lower()

    if not is_farming_query(q):
        return AssistantIntent.OUT_OF_SCOPE

    # Check for Action Plan triggers ("what should I do", "action today", "tasks")
    if (
        "what should i do" in q
        or "what do i do" in q
        or "tasks for today" in q
        or "my plan" in q
        or "today's action" in q
        or "actions for today" in q
        or ("today" in q and ("do" in q or "action" in q or "priority" in q))
    ):
        return AssistantIntent.DYNAMIC_ACTION_PLAN

    # Check for Risk & Alert triggers ("risks", "alerts", "why did i receive")
    if (
        "my risk" in q
        or "my risks" in q
        or "biggest risk" in q
        or "current risk" in q
        or "farm risks" in q
        or "why did i receive this alert" in q
        or "why this alert" in q
        or "my alert" in q
        or "my alerts" in q
        or "active alert" in q
    ):
        return AssistantIntent.DYNAMIC_RISKS_ALERTS

    # Check for Decision Engine triggers ("why irrigate today", "why this recommendation")
    if (
        "why should i irrigate" in q
        or "should i irrigate today" in q
        or "current recommendation" in q
        or "why this decision" in q
        or "my farm decision" in q
    ):
        return AssistantIntent.DYNAMIC_DECISION

    # Check for dynamic weather triggers ("today's weather", "current weather")
    if ("today's weather" in q or "current weather" in q or "weather forecast" in q or "will it rain today" in q):
        if request.farm_context and request.farm_context.weather:
            return AssistantIntent.DYNAMIC_WEATHER

    # Check for dynamic market triggers ("current price", "market price today")
    if ("market price today" in q or "current market" in q or "mandi price today" in q or "today's price" in q):
        if request.farm_context and request.farm_context.market:
            return AssistantIntent.DYNAMIC_MARKET

    # If asking specifically about 'my field' or 'my crop' with existing upstream data
    if ("my field" in q or "my farm" in q or "my condition" in q) and (
        request.action_plan or request.smart_alerts or request.risk_opportunity or request.decision
    ):
        if request.action_plan:
            return AssistantIntent.DYNAMIC_ACTION_PLAN
        if request.smart_alerts or request.risk_opportunity:
            return AssistantIntent.DYNAMIC_RISKS_ALERTS
        return AssistantIntent.DYNAMIC_DECISION

    return AssistantIntent.STATIC_KNOWLEDGE


def extract_agronomic_entities(text: str) -> Dict[str, Optional[str]]:
    """Extract crop name, stage, and primary topic from query string."""
    q = text.lower()
    detected_crop = None
    detected_stage = None
    detected_topic = None

    # Detect crop
    crop_aliases = {
        "paddy": "rice", "rice": "rice", "wheat": "wheat",
        "maize": "maize", "corn": "maize", "cotton": "cotton",
        "soybean": "soybean", "pulses": "pulses", "potato": "potato",
        "tomato": "tomato", "onion": "onion", "mustard": "mustard",
        "groundnut": "groundnut", "sugarcane": "sugarcane"
    }
    for alias, standard_crop in crop_aliases.items():
        if re.search(r"\b" + re.escape(alias) + r"\b", q):
            detected_crop = standard_crop
            break

    # Detect stage
    stages = [
        "germination", "seedling", "tillering", "vegetative", "flowering",
        "booting", "panicle initiation", "grain filling", "milking", "maturity", "harvest"
    ]
    for st in stages:
        if st in q:
            detected_stage = st
            break

    # Detect topic
    if any(w in q for w in ["pest", "insect", "borer", "aphid", "whitefly", "infest"]):
        detected_topic = "pest"
    elif any(w in q for w in ["disease", "fungus", "blight", "blast", "rust", "rot", "wilt", "spot"]):
        detected_topic = "disease"
    elif any(w in q for w in ["fertilizer", "npk", "nitrogen", "urea", "nutrient", "dap"]):
        detected_topic = "fertilizer"
    elif any(w in q for w in ["irrigation", "water", "irrigate", "drip", "moisture"]):
        detected_topic = "irrigation"
    elif any(w in q for w in ["soil", "ph", "salinity", "loam", "fertility"]):
        detected_topic = "soil"
    elif any(w in q for w in ["harvest", "storage", "yield"]):
        detected_topic = "harvest"
    elif any(w in q for w in ["weather", "rain", "heat", "frost", "cold", "drought"]):
        detected_topic = "weather"
    elif any(w in q for w in ["price", "market", "mandi"]):
        detected_topic = "market"

    return {
        "crop": detected_crop,
        "crop_stage": detected_stage,
        "topic": detected_topic
    }


def synthesize_dynamic_response(
    intent: AssistantIntent,
    request: ChatRequest
) -> Tuple[str, List[str]]:
    """
    Format a grounded response from already-computed AGRINEXUS intelligence outputs.
    Never invents facts, never re-computes ML rules.
    """
    modules_used: List[str] = []
    lines: List[str] = []

    if intent == AssistantIntent.DYNAMIC_ACTION_PLAN:
        if request.action_plan and request.action_plan.actions:
            modules_used.append("personalized_action_plan")
            lines.append("Here is your current Personalized Action Plan for your farm:")
            for idx, act in enumerate(request.action_plan.actions[:4], start=1):
                timing = f" (Timing: {act.recommended_time})" if act.recommended_time else ""
                lines.append(f"{idx}. [{act.priority.upper()}] {act.title}: {act.action}{timing}")
                if act.reason:
                    lines.append(f"   Reason: {act.reason}")

            if request.smart_alerts and request.smart_alerts.alerts:
                modules_used.append("smart_alerts")
                crit_alerts = [a for a in request.smart_alerts.alerts if a.priority in ("critical", "high")]
                if crit_alerts:
                    lines.append("\nActive Critical Alerts:")
                    for ca in crit_alerts[:2]:
                        lines.append(f"- {ca.title}: {ca.message}")
            return "\n".join(lines), modules_used

        # Fallback if no action plan present in request
        if request.smart_alerts and request.smart_alerts.alerts:
            modules_used.append("smart_alerts")
            lines.append("Active Alerts for your farm:")
            for a in request.smart_alerts.alerts[:3]:
                lines.append(f"- [{a.priority.upper()}] {a.title}: {a.message}")
            return "\n".join(lines), modules_used

        return (
            "No active action plan is currently registered for your farm session. "
            "Please provide your farm context or run the Action Plan generator.",
            modules_used
        )

    if intent == AssistantIntent.DYNAMIC_RISKS_ALERTS:
        if request.smart_alerts and request.smart_alerts.alerts:
            modules_used.append("smart_alerts")
            lines.append("Here are your current Smart Alerts:")
            for a in request.smart_alerts.alerts:
                lines.append(f"- [{a.priority.upper()}] {a.title}: {a.message}")
                if a.recommended_action:
                    lines.append(f"  Recommended Action: {a.recommended_action}")

        if request.risk_opportunity and request.risk_opportunity.risks:
            modules_used.append("risk_opportunity")
            if not lines:
                lines.append("Identified Farm Risks:")
            else:
                lines.append("\nIdentified Farm Risks:")
            for r in request.risk_opportunity.risks[:3]:
                lines.append(f"- [{r.severity.upper()}] {r.title}: {r.description}")
                if r.recommended_follow_up:
                    lines.append(f"  Follow-up: {r.recommended_follow_up}")

        if lines:
            return "\n".join(lines), modules_used

        return (
            "No active risks or alerts have been flagged for your current farm context.",
            modules_used
        )

    if intent == AssistantIntent.DYNAMIC_DECISION:
        if request.decision:
            modules_used.append("decision_engine")
            lines.append("Current Farm Decision Engine Output:")
            if hasattr(request.decision, "decisions") and request.decision.decisions:
                for d in request.decision.decisions[:3]:
                    lines.append(f"Recommendation: {d.title} - {d.summary}")
                    if d.reason:
                        lines.append(f"Reasoning: {d.reason}")
            elif hasattr(request.decision, "primary_recommendation") and request.decision.primary_recommendation:
                lines.append(f"Primary Recommendation: {request.decision.primary_recommendation}")
                if getattr(request.decision, "reasoning", None):
                    lines.append(f"Reasoning: {request.decision.reasoning}")
            return "\n".join(lines), modules_used

        return (
            "No active decision recommendation is loaded. Please submit your farm context to evaluate.",
            modules_used
        )

    if intent == AssistantIntent.DYNAMIC_WEATHER:
        if request.farm_context and request.farm_context.weather:
            modules_used.append("weather_intelligence")
            w = request.farm_context.weather
            lines.append(f"Weather situation for {request.farm_context.location or 'your field'}:")
            if hasattr(w, "temperature_max_c") and w.temperature_max_c is not None:
                lines.append(f"- Temperature: Max {w.temperature_max_c}°C / Min {w.temperature_min_c}°C")
            if hasattr(w, "rainfall_mm") and w.rainfall_mm is not None:
                lines.append(f"- Rainfall: {w.rainfall_mm} mm")
            if hasattr(w, "relative_humidity_pct") and w.relative_humidity_pct is not None:
                lines.append(f"- Relative Humidity: {w.relative_humidity_pct}%")
            return "\n".join(lines), modules_used

    if intent == AssistantIntent.DYNAMIC_MARKET:
        if request.farm_context and request.farm_context.market:
            modules_used.append("market_intelligence")
            m = request.farm_context.market
            lines.append(f"Market data for {m.commodity} in {m.market or m.district or 'local market'}:")
            lines.append(f"- Current Modal Price: ₹{m.modal_price:.2f}/quintal")
            if m.trend:
                lines.append(f"- Price Trend: {m.trend}")
            return "\n".join(lines), modules_used

    return "No dynamic farm information is available for this request.", modules_used
