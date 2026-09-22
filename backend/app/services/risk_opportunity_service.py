"""
Risk & Opportunity Analysis service layer.

Responsibilities:
- Provide a reusable, dependency-injectable RiskOpportunityService
- Accept the normalized RiskOpportunityContext (FarmContext + optional
  Decision Engine output) and delegate all analysis to the deterministic
  engine in app.intelligence.risk_opportunity
- Reuse DecisionEngineService adapters for normalizing existing module
  outputs (weather/market/crop-calendar/ML contracts); this service never
  fetches external APIs itself

This service is NOT an ML model and performs no external API calls.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.intelligence.risk_opportunity import (
    ENGINE_VERSION,
    KNOWN_ML_MODELS,
    RULESET_VERSION,
    analyze_risk_opportunity,
)
from app.schemas.decision import DecisionResponse, FarmContext
from app.schemas.risk_opportunity import (
    OpportunityCategory,
    RiskCategory,
    RiskOpportunityContext,
    RiskOpportunityResponse,
)
from app.services.decision_engine_service import DecisionEngineService


class RiskOpportunityService:
    """
    Application service for Risk & Opportunity Analysis.

    Usage:
        service = RiskOpportunityService()
        response = service.analyze(RiskOpportunityContext(...))
    """

    def __init__(self) -> None:
        self.engine_version = ENGINE_VERSION
        self.ruleset_version = RULESET_VERSION
        # Adapters are reused, never duplicated.
        self._decision_service = DecisionEngineService()

    # ------------------------------------------------------------------
    # Health
    # ------------------------------------------------------------------

    def health(self) -> Dict[str, Any]:
        """Health snapshot (no secrets, no API keys)."""
        return {
            "status": "healthy",
            "service": "agrinexus-risk-opportunity",
            "version": self.engine_version,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "engine_available": True,
            "ruleset_version": self.ruleset_version,
            "supported_risk_categories": [c.value for c in RiskCategory],
            "supported_opportunity_categories": [
                c.value for c in OpportunityCategory
            ],
            "upstream_dependencies": [
                "weather",
                "market",
                "crop_calendar",
                "decision_engine",
            ],
            "ml_model_contracts_available": list(KNOWN_ML_MODELS),
        }

    # ------------------------------------------------------------------
    # Analysis
    # ------------------------------------------------------------------

    def analyze(
        self, context: RiskOpportunityContext
    ) -> RiskOpportunityResponse:
        """Run deterministic risk & opportunity analysis."""
        return analyze_risk_opportunity(context)

    def analyze_farm_context(
        self,
        farm_context: FarmContext,
        decision_engine_output: Optional[DecisionResponse] = None,
        source_metadata: Optional[Dict[str, Any]] = None,
    ) -> RiskOpportunityResponse:
        """Convenience wrapper when callers already hold a FarmContext."""
        return analyze_risk_opportunity(
            RiskOpportunityContext(
                farm_context=farm_context,
                decision_engine_output=decision_engine_output,
                source_metadata=source_metadata,
            )
        )

    # ------------------------------------------------------------------
    # Normalization adapters (reused from DecisionEngineService)
    # ------------------------------------------------------------------

    @property
    def decision_service(self) -> DecisionEngineService:
        """Exposed so callers can reuse existing normalization adapters."""
        return self._decision_service

    def describe_ruleset(self) -> Dict[str, Any]:
        """Documented ruleset vocabulary snapshot."""
        return {
            "ruleset_version": self.ruleset_version,
            "risk_categories": [c.value for c in RiskCategory],
            "opportunity_categories": [c.value for c in OpportunityCategory],
        }

    def supported_ml_contracts(self) -> List[str]:
        """Known standardized ML prediction contracts (names only)."""
        return list(KNOWN_ML_MODELS)
