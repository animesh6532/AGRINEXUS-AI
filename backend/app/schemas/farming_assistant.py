"""
Pydantic schemas for the AI Farming Assistant / Farming Chatbot layer.

Follows the AGRINEXUS architecture conventions:
- Reuses FarmContext and DecisionResponse from app.schemas.decision
- Reuses RiskOpportunityResponse from app.schemas.risk_opportunity
- Reuses SmartAlertResponse from app.schemas.smart_alert
- Reuses ActionPlanResponse and FarmerContext from app.schemas.action_plan
- Enforces strict Pydantic v2 validation without deprecated fields
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.schemas.action_plan import ActionPlanResponse, FarmerContext
from app.schemas.decision import DecisionResponse, FarmContext
from app.schemas.risk_opportunity import RiskOpportunityResponse
from app.schemas.smart_alert import SmartAlertResponse


class AssistantIntent(str, Enum):
    """Classified user intent for agricultural routing."""
    STATIC_KNOWLEDGE = "static_knowledge"
    DYNAMIC_ACTION_PLAN = "dynamic_action_plan"
    DYNAMIC_RISKS_ALERTS = "dynamic_risks_alerts"
    DYNAMIC_DECISION = "dynamic_decision"
    DYNAMIC_WEATHER = "dynamic_weather"
    DYNAMIC_MARKET = "dynamic_market"
    CLARIFICATION = "clarification"
    OUT_OF_SCOPE = "out_of_scope"


class KnowledgeSourceInfo(BaseModel):
    """Source provenance and agronomic citation for a knowledge record."""
    knowledge_id: int = Field(..., description="ID of the knowledge record")
    source: str = Field(..., description="Source organization or literature")
    source_url: Optional[str] = Field(None, description="URL reference if available")
    crop: Optional[str] = Field(None, description="Crop relevance")
    topic: Optional[str] = Field(None, description="Agronomic topic")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Cosine similarity score")


class FarmingKnowledgeMatch(BaseModel):
    """Matched Question-Answer pair from semantic search."""
    id: int
    question: str
    answer: str
    crop: Optional[str] = None
    crop_stage: Optional[str] = None
    topic: str
    subtopic: Optional[str] = None
    keywords: Optional[str] = None
    language: str = "en"
    region: Optional[str] = None
    source: str
    source_url: Optional[str] = None
    similarity_score: float = Field(..., ge=0.0, le=1.0)


class FarmingKnowledgeRecordCreate(BaseModel):
    """Schema for ingesting a single knowledge base record."""
    question: str = Field(..., min_length=5, description="Farming question")
    answer: str = Field(..., min_length=10, description="Agronomic answer")
    crop: Optional[str] = Field(None, description="Crop name")
    crop_stage: Optional[str] = Field(None, description="Crop growth stage")
    topic: str = Field(..., min_length=2, description="Agronomic topic")
    subtopic: Optional[str] = Field(None, description="Subtopic")
    keywords: Optional[str] = Field(None, description="Comma-separated keywords")
    language: str = Field(default="en", description="Language code")
    region: Optional[str] = Field(None, description="Geographic region")
    source: str = Field(default="AGRINEXUS Farming Knowledge Base", description="Source name")
    source_url: Optional[str] = Field(None, description="Reference URL")
    verified: bool = Field(default=True, description="Human/expert verified flag")


class ChatRequest(BaseModel):
    """Request payload for the conversational AI Farming Assistant."""
    message: str = Field(..., min_length=1, description="Farmer natural language query")
    conversation_id: Optional[str] = Field(None, description="Client conversation session ID")
    farm_context: Optional[FarmContext] = Field(None, description="Current farm situational context")
    farmer_context: Optional[FarmerContext] = Field(None, description="Farmer profile and field constraints")
    decision: Optional[DecisionResponse] = Field(None, description="Decision Engine structured response")
    risk_opportunity: Optional[RiskOpportunityResponse] = Field(None, description="Risk & Opportunity response")
    smart_alerts: Optional[SmartAlertResponse] = Field(None, description="Smart Alerts response")
    action_plan: Optional[ActionPlanResponse] = Field(None, description="Personalized Action Plan response")
    crop_filter: Optional[str] = Field(None, description="Optional crop override for knowledge search")
    topic_filter: Optional[str] = Field(None, description="Optional topic override for knowledge search")
    max_results: Optional[int] = Field(None, ge=1, le=10, description="Max candidate matches")


class ChatResponse(BaseModel):
    """Grounded, traceable response for the frontend chatbot."""
    status: str = Field(..., description="Response status (success, no_match, out_of_scope)")
    answer: str = Field(..., description="Grounded natural-language answer")
    intent: AssistantIntent = Field(..., description="Routing category identified")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence or highest similarity")
    sources: List[KnowledgeSourceInfo] = Field(default_factory=list, description="Preserved source attributions")
    knowledge_matches: List[FarmingKnowledgeMatch] = Field(default_factory=list, description="Top-K matched records")
    conversation_id: str = Field(..., description="Active conversation session ID")
    follow_up_question: Optional[str] = Field(None, description="Relevant contextual follow-up question")
    dynamic_data_used: List[str] = Field(default_factory=list, description="AGRINEXUS modules supplying data")
    created_at: str = Field(..., description="UTC ISO timestamp")


class FarmingAssistantHealthResponse(BaseModel):
    """Health check response for the Farming Assistant service."""
    status: str
    service: str
    version: str
    timestamp: str
    embedding_model: str
    embedding_dimension: int
    vector_search_ready: bool
    knowledge_base_record_count: int
    knowledge_base_target_met: bool
    upstream_dependencies: List[str]


class FarmingAssistantCapabilitiesResponse(BaseModel):
    """Supported domains and routing capabilities."""
    service: str
    version: str
    supported_topics: List[str]
    supported_crops: List[str]
    routing_intents: List[str]
    features: Dict[str, Any]
    similarity_threshold: float
    top_k: int
    timestamp: str


class KnowledgeBaseStatusResponse(BaseModel):
    """Status and count verification for the knowledge base."""
    record_count: int
    verified_count: int
    target_count: int = 10000
    is_target_met: bool
    status_summary: str
    embedding_model: str
    dataset_status: str
    timestamp: str
