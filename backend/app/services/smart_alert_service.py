"""
Smart Alerts service layer. Reusable DI service delegating to the
deterministic engine in app.intelligence.smart_alert. No external
API calls, no ML calls.
"""

from datetime import datetime, timezone
from typing import Any, Dict

from app.intelligence.smart_alert import (
    ENGINE_VERSION, PRIORITY_ORDER, RULES, RULESET_VERSION,
    TYPE_ORDER, generate_alerts,
)
from app.schemas.risk_opportunity import RiskOpportunityResponse
from app.schemas.smart_alert import SmartAlertPreferences, SmartAlertResponse


class SmartAlertService:
    def __init__(self) -> None:
        self.engine_version = ENGINE_VERSION
        self.ruleset_version = RULESET_VERSION

    def health(self) -> Dict[str, Any]:
        return {
            "status": "healthy", "service": "agrinexus-smart-alerts",
            "version": self.engine_version,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "engine_available": True, "ruleset_version": self.ruleset_version,
            "upstream_dependencies": ["risk_opportunity"],
        }

    def generate(self, response: RiskOpportunityResponse,
                 preferences: SmartAlertPreferences | None = None) -> SmartAlertResponse:
        return generate_alerts(response, preferences)

    def describe_rules(self) -> Dict[str, Any]:
        return {
            "ruleset_version": self.ruleset_version,
            "engine_version": self.engine_version,
            "rules": [{"rule": r, "description": d} for r, d in RULES],
            "priority_order": sorted(PRIORITY_ORDER, key=PRIORITY_ORDER.get),
            "type_order": sorted(TYPE_ORDER, key=TYPE_ORDER.get),
        }
