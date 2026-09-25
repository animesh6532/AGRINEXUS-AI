"""
Action Plan service layer. Reusable DI service delegating to the
deterministic engine in app.intelligence.action_plan. No external
API calls, no ML calls.
"""

from datetime import datetime, timezone
from typing import Any, Dict

from app.intelligence.action_plan import (
    ENGINE_VERSION, PRIORITY_ORDER, RULES, RULESET_VERSION,
    generate_action_plan,
)
from app.schemas.action_plan import ActionPlanRequest, ActionPlanResponse


class ActionPlanService:
    def __init__(self) -> None:
        self.engine_version = ENGINE_VERSION
        self.ruleset_version = RULESET_VERSION

    def health(self) -> Dict[str, Any]:
        return {
            "status": "healthy", "service": "agrinexus-action-plan",
            "version": self.engine_version,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "engine_available": True, "ruleset_version": self.ruleset_version,
            "upstream_dependencies": ["decision_engine", "risk_opportunity", "smart_alerts"],
        }

    def generate(self, request: ActionPlanRequest) -> ActionPlanResponse:
        return generate_action_plan(request)

    def describe_rules(self) -> Dict[str, Any]:
        return {
            "ruleset_version": self.ruleset_version,
            "engine_version": self.engine_version,
            "rules": [{"rule": r, "description": d} for r, d in RULES],
            "priority_order": sorted(PRIORITY_ORDER, key=PRIORITY_ORDER.get),
        }
