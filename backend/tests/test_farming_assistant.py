"""
Unit and Integration Tests for AI Farming Assistant / Farming Chatbot.

Verifies:
 1. Health endpoint.
 2. Capabilities endpoint.
 3. Valid chat request.
 4. Empty question handling.
 5. Farming question processing.
 6. Non-farming question scope redirection.
 7. Exact knowledge match.
 8. Semantically similar question matching.
 9. Multiple relevant results retrieval.
10. Similarity threshold filtering.
11. No-match fallback behavior.
12. Source traceability.
13. Crop filtering.
14. Topic filtering.
15. Dynamic question routing.
16. Action Plan integration.
17. Smart Alert integration.
18. Risk & Opportunity integration.
19. Decision Engine integration.
20. Conversation context memory.
21. Missing farm context follow-up.
22. Duplicate knowledge handling.
23. Knowledge ingestion validation.
24. Response schema validation.
25. No hallucinated fallback answer.
26. Knowledge base count verification (10,000+ verification check).
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.api.farming_assistant import get_farming_assistant_service
from app.intelligence.farming_assistant import (
    FALLBACK_NO_MATCH,
    NON_FARMING_REDIRECT,
    AssistantIntent,
    classify_assistant_intent,
    is_farming_query,
)
from app.main import app
from app.schemas.action_plan import (
    ActionPlanItem,
    ActionPlanResponse,
    ActionPriority,
    ActionSourceType,
    ActionStatus,
    ActionType,
)
from app.schemas.decision import (
    DataQuality,
    Decision,
    DecisionResponse,
    DecisionStatus,
    DecisionType,
    Priority,
)
from app.schemas.farming_assistant import (
    ChatRequest,
    ChatResponse,
    FarmingKnowledgeRecordCreate,
)
from app.schemas.risk_opportunity import (
    ConfidenceLevel,
    ItemStatus,
    PriorityLevel,
    Risk,
    RiskCategory,
    RiskOpportunityResponse,
    RiskOpportunitySummary,
    SeverityLevel,
)
from app.schemas.smart_alert import (
    AlertPriority,
    AlertSeverity,
    AlertSourceType,
    AlertStatus,
    AlertType,
    SmartAlert,
    SmartAlertResponse,
)

client = TestClient(app)


@pytest.fixture(scope="session")
def service():
    """Provides a singleton service instance with pre-seeded knowledge base."""
    svc = get_farming_assistant_service()
    svc.reload_knowledge_base()
    return svc


# -------------------------------------------------------------
# 1. Health Endpoint
# -------------------------------------------------------------
def test_health_endpoint():
    res = client.get("/api/farming-assistant/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["service"] == "agrinexus-farming-assistant"
    assert "embedding_model" in data
    assert "knowledge_base_record_count" in data
    assert isinstance(data["knowledge_base_target_met"], bool)
    assert "upstream_dependencies" in data


# -------------------------------------------------------------
# 2. Capabilities Endpoint
# -------------------------------------------------------------
def test_capabilities_endpoint():
    res = client.get("/api/farming-assistant/capabilities")
    assert res.status_code == 200
    data = res.json()
    assert data["service"] == "agrinexus-farming-assistant"
    assert "rice" in data["supported_crops"]
    assert "fertilizer" in data["supported_topics"]
    assert "static_knowledge" in data["routing_intents"]
    assert data["features"]["semantic_vector_search"] is True
    assert data["features"]["no_external_llm_required"] is True


# -------------------------------------------------------------
# 3. Valid Chat Request via API
# -------------------------------------------------------------
def test_valid_chat_request(service):
    payload = {"message": "What is crop rotation?"}
    res = client.post("/api/farming-assistant/chat", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["intent"] == "static_knowledge"
    assert len(data["answer"]) > 20
    assert len(data["sources"]) > 0
    assert data["sources"][0]["source"] is not None


# -------------------------------------------------------------
# 4. Empty Question Validation
# -------------------------------------------------------------
def test_empty_question():
    res = client.post("/api/farming-assistant/chat", json={"message": "   "})
    assert res.status_code == 400
    assert "empty" in res.json()["detail"].lower()


# -------------------------------------------------------------
# 5. Farming Question
# -------------------------------------------------------------
def test_farming_question_scope(service):
    assert is_farming_query("What is NPK fertilizer?") is True
    assert is_farming_query("Why are my rice leaves turning yellow?") is True
    assert is_farming_query("How to control fall armyworm in maize?") is True


# -------------------------------------------------------------
# 6. Non-Farming Question Scope Redirection
# -------------------------------------------------------------
def test_non_farming_question_redirect(service):
    res = client.post("/api/farming-assistant/chat", json={"message": "Tell me a joke."})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "out_of_scope"
    assert data["intent"] == "out_of_scope"
    assert data["answer"] == NON_FARMING_REDIRECT


# -------------------------------------------------------------
# 7. Exact Knowledge Match
# -------------------------------------------------------------
def test_exact_knowledge_match(service):
    matches = service.search_knowledge_base("What is crop rotation?", top_k=1)
    assert len(matches) > 0
    assert matches[0].question == "What is crop rotation?"
    assert "practice of growing different types of crops sequentially" in matches[0].answer


# -------------------------------------------------------------
# 8. Semantically Similar Question Matching
# -------------------------------------------------------------
def test_semantically_similar_question(service):
    # Paraphrased query: "paddy leaves are turning yellow" instead of "Why do rice leaves become yellow?"
    matches = service.search_knowledge_base("My paddy leaves are turning yellow. What is causing this?", top_k=1)
    assert len(matches) > 0
    assert "rice" in (matches[0].crop or "").lower() or "yellow" in matches[0].question.lower() or "leaves" in matches[0].answer.lower()


# -------------------------------------------------------------
# 9. Multiple Relevant Results Retrieval
# -------------------------------------------------------------
def test_multiple_relevant_results(service):
    matches = service.search_knowledge_base("rice disease spots leaves", top_k=3, similarity_threshold=0.1)
    assert len(matches) >= 2


# -------------------------------------------------------------
# 10. Similarity Threshold Filtering
# -------------------------------------------------------------
def test_similarity_threshold_filtering(service):
    # High threshold should filter out unrelated queries
    matches = service.search_knowledge_base("quantum mechanics physics equation", similarity_threshold=0.95)
    assert len(matches) == 0


# -------------------------------------------------------------
# 11. No-Match Fallback Behavior
# -------------------------------------------------------------
def test_no_match_fallback():
    # Agronomic query but for completely unsupported niche crop/topic without matches
    res = client.post("/api/farming-assistant/chat", json={"message": "How to cultivate hydroponic saffron in antarctica soil?"})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "no_match"
    assert data["answer"] == FALLBACK_NO_MATCH
    assert data["confidence"] == 0.0


# -------------------------------------------------------------
# 12. Source Traceability
# -------------------------------------------------------------
def test_source_traceability(service):
    res = client.post("/api/farming-assistant/chat", json={"message": "What is NPK fertilizer?"})
    assert res.status_code == 200
    data = res.json()
    assert len(data["sources"]) > 0
    src = data["sources"][0]
    assert "source" in src
    assert "knowledge_id" in src
    assert "relevance_score" in src
    assert src["topic"] == "fertilizer"


# -------------------------------------------------------------
# 13. Crop Filtering
# -------------------------------------------------------------
def test_crop_filtering(service):
    matches = service.search_knowledge_base("harvest timing", crop_filter="wheat", similarity_threshold=0.1)
    for m in matches:
        assert m.crop == "wheat"


# -------------------------------------------------------------
# 14. Topic Filtering
# -------------------------------------------------------------
def test_topic_filtering(service):
    matches = service.search_knowledge_base("improve health and drainage", topic_filter="soil", similarity_threshold=0.1)
    for m in matches:
        assert m.topic == "soil"


# -------------------------------------------------------------
# 15. Dynamic Question Routing
# -------------------------------------------------------------
def test_dynamic_question_routing():
    req1 = ChatRequest(message="What should I do today?")
    assert classify_assistant_intent(req1.message, req1) == AssistantIntent.DYNAMIC_ACTION_PLAN

    req2 = ChatRequest(message="What are my biggest farm risks?")
    assert classify_assistant_intent(req2.message, req2) == AssistantIntent.DYNAMIC_RISKS_ALERTS

    req3 = ChatRequest(message="Why should I irrigate today?")
    assert classify_assistant_intent(req3.message, req3) == AssistantIntent.DYNAMIC_DECISION


# -------------------------------------------------------------
# 16. Action Plan Integration
# -------------------------------------------------------------
def test_action_plan_integration(service):
    action_item = ActionPlanItem(
        id="act-1",
        action_type=ActionType.IRRIGATION,
        priority=ActionPriority.HIGH,
        status=ActionStatus.ACTIVE,
        title="Irrigate paddy field",
        action="Apply 3 cm irrigation within morning hours",
        reason="Soil moisture dropped below threshold",
        source_id="upstream-1",
        source_type=ActionSourceType.RISK,
        created_at="2026-09-26T10:00:00Z",
        dedupe_key="hash123",
        recommended_time="within 6 hours"
    )
    ap = ActionPlanResponse(
        status=DecisionStatus.partial_context,
        actions=[action_item],
        total_actions=1,
        critical_count=0,
        high_count=1,
        medium_count=0,
        low_count=0,
        suppressed_count=0,
        engine_version="1.0.0",
        ruleset_version="1.0.0",
        generated_at="2026-09-26T10:00:00Z"
    )

    req = ChatRequest(message="What should I do today?", action_plan=ap)
    resp = service.chat(req)
    assert resp.status == "success"
    assert resp.intent == AssistantIntent.DYNAMIC_ACTION_PLAN
    assert "Apply 3 cm irrigation" in resp.answer
    assert "personalized_action_plan" in resp.dynamic_data_used


# -------------------------------------------------------------
# 17. Smart Alert Integration
# -------------------------------------------------------------
def test_smart_alert_integration(service):
    alert = SmartAlert(
        id="alert-1",
        alert_type=AlertType.RISK,
        priority=AlertPriority.CRITICAL,
        severity=AlertSeverity.CRITICAL,
        status=AlertStatus.ACTIVE,
        title="Rice Blast Warning",
        message="High humidity and leaf wetness favor blast progression",
        recommended_action="Inspect field immediately and prepare preventative fungicide",
        source_id="src-1",
        source_type=AlertSourceType.RISK,
        category="disease",
        created_at="2026-09-26T10:00:00Z",
        dedupe_key="dedupe-1"
    )
    alerts_resp = SmartAlertResponse(
        status=DecisionStatus.partial_context,
        alerts=[alert],
        total_alerts=1,
        critical_count=1,
        high_count=0,
        medium_count=0,
        low_count=0,
        risk_count=1,
        opportunity_count=0,
        conflict_count=0,
        data_quality_count=0,
        suppressed_count=0,
        engine_version="1.0.0",
        ruleset_version="1.0.0",
        generated_at="2026-09-26T10:00:00Z"
    )

    req = ChatRequest(message="Why did I receive this alert?", smart_alerts=alerts_resp)
    resp = service.chat(req)
    assert resp.status == "success"
    assert resp.intent == AssistantIntent.DYNAMIC_RISKS_ALERTS
    assert "Rice Blast Warning" in resp.answer
    assert "smart_alerts" in resp.dynamic_data_used


# -------------------------------------------------------------
# 18. Risk & Opportunity Integration
# -------------------------------------------------------------
def test_risk_opportunity_integration(service):
    risk = Risk(
        id="risk-1",
        category=RiskCategory.WEATHER,
        title="Excess Heat Stress Risk",
        description="Daytime temperatures exceeding 38°C during flowering",
        severity=SeverityLevel.HIGH,
        priority=PriorityLevel.HIGH,
        status=ItemStatus.ACTIVE,
        confidence=ConfidenceLevel.HIGH,
        numerical_confidence=0.85,
        confidence_source="decision_engine",
        confidence_rationale="Temperature forecast agreement",
        evidence=[],
        contributing_sources=[],
        contributing_signals=["temp_max_high"],
        reasoning="Temperature anomaly",
        recommended_follow_up="Maintain standing water layer to mitigate heat",
        detected_at="2026-09-26T10:00:00Z"
    )
    ro_resp = RiskOpportunityResponse(
        status=DecisionStatus.partial_context,
        risks=[risk],
        opportunities=[],
        data_quality=DataQuality(status="partial_context"),
        summary=RiskOpportunitySummary(risk_count=1, opportunity_count=0, data_quality_notice_count=0, conflict_notice_count=0),
        engine_version="1.0.0",
        ruleset_version="1.0.0",
        analysis_timestamp="2026-09-26T10:00:00Z",
        total_risks=1,
        total_opportunities=0
    )

    req = ChatRequest(message="What are my current farm risks?", risk_opportunity=ro_resp)
    resp = service.chat(req)
    assert resp.status == "success"
    assert "Excess Heat Stress Risk" in resp.answer
    assert "risk_opportunity" in resp.dynamic_data_used


# -------------------------------------------------------------
# 19. Decision Engine Integration
# -------------------------------------------------------------
def test_decision_engine_integration(service):
    decision_item = Decision(
        id="dec-1",
        decision_type=DecisionType.weather_irrigation_interaction,
        status=DecisionStatus.partial_context,
        priority=Priority.HIGH,
        title="Irrigate Field",
        summary="Apply 40 mm irrigation today",
        reason="Evapotranspiration exceeded rainfall over past 4 days",
        created_at="2026-09-26T10:00:00Z"
    )
    dec = DecisionResponse(
        status=DecisionStatus.partial_context,
        data_quality=DataQuality(status="partial_context"),
        decisions=[decision_item],
        warnings=[],
        ruleset_version="1.0.0",
        engine_version="1.0.0",
        evaluation_timestamp="2026-09-26T10:00:00Z",
        total_decisions=1
    )

    req = ChatRequest(message="Why should I irrigate today?", decision=dec)
    resp = service.chat(req)
    assert resp.status == "success"
    assert resp.intent == AssistantIntent.DYNAMIC_DECISION
    assert "Irrigate Field" in resp.answer
    assert "decision_engine" in resp.dynamic_data_used


# -------------------------------------------------------------
# 20. Conversation Context Memory
# -------------------------------------------------------------
def test_conversation_context(service):
    cid = "session-test-memory-1"
    req1 = ChatRequest(message="What causes brown spots on rice leaves?", conversation_id=cid)
    resp1 = service.chat(req1)
    assert resp1.status == "success"

    history = service.get_conversation_history(cid)
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[1]["role"] == "assistant"

    # Subsequent interaction
    req2 = ChatRequest(message="What should I check first?", conversation_id=cid)
    resp2 = service.chat(req2)
    history_after = service.get_conversation_history(cid)
    assert len(history_after) == 4


# -------------------------------------------------------------
# 21. Missing Farm Context Follow-Up
# -------------------------------------------------------------
def test_missing_farm_context_followup(service):
    # Query with symptom but no crop mentioned
    req = ChatRequest(message="My leaves are turning yellow with brown spots.")
    resp = service.chat(req)
    assert resp.follow_up_question is not None
    assert "crop" in resp.follow_up_question.lower()


# -------------------------------------------------------------
# 22. Duplicate Knowledge Ingestion Handling
# -------------------------------------------------------------
def test_duplicate_knowledge_handling(service):
    item = FarmingKnowledgeRecordCreate(
        question="Can drip irrigation save water in tomato fields?",
        answer="Yes, drip irrigation delivers water directly to the plant root zone, reducing evaporation and runoff by up to 50 percent.",
        crop="tomato",
        topic="irrigation",
        verified=True
    )
    rec1 = service.ingest_record(item)
    count_after_first = service.get_kb_record_count()
    rec2 = service.ingest_record(item)
    count_after_second = service.get_kb_record_count()
    assert count_after_first == count_after_second
    assert rec2 is not None


# -------------------------------------------------------------
# 23. Knowledge Ingestion Validation
# -------------------------------------------------------------
def test_knowledge_ingestion_validation(service):
    # Test min length validation on question
    with pytest.raises(Exception):
        FarmingKnowledgeRecordCreate(
            question="Hi",  # too short (< 5 chars)
            answer="This is a valid answer for the test.",
            topic="crop"
        )


# -------------------------------------------------------------
# 24. Response Schema Validation
# -------------------------------------------------------------
def test_response_schema_validation(service):
    res = client.post("/api/farming-assistant/chat", json={"message": "What is NPK fertilizer?"})
    assert res.status_code == 200
    data = res.json()
    chat_resp = ChatResponse(**data)
    assert chat_resp.status == "success"
    assert isinstance(chat_resp.sources, list)
    assert isinstance(chat_resp.dynamic_data_used, list)


# -------------------------------------------------------------
# 25. No Hallucinated Fallback Answer
# -------------------------------------------------------------
def test_no_hallucinated_fallback_answer(service):
    # When query has no supporting knowledge, system MUST return standard fallback and never fabricate facts
    req = ChatRequest(message="What is the exact chemical dosage of chemical xyz999 on potato crops?")
    resp = service.chat(req)
    assert resp.status == "no_match"
    assert resp.answer == FALLBACK_NO_MATCH
    assert "xyz999" not in resp.answer


# -------------------------------------------------------------
# 26. Knowledge Base Count Verification (Section 41)
# -------------------------------------------------------------
def test_knowledge_base_count_verification():
    res = client.get("/api/farming-assistant/kb-status")
    assert res.status_code == 200
    data = res.json()
    assert "record_count" in data
    assert "target_count" in data
    assert data["target_count"] == 10000
    # Must transparently reflect whether 10k target is met
    assert data["is_target_met"] == (data["record_count"] >= 10000)
    assert "Knowledge base contains" in data["status_summary"]


# -------------------------------------------------------------
# 27. KisanVaani Parquet Loading
# -------------------------------------------------------------
def test_kisanvaani_parquet_loading():
    import pandas as pd
    from pathlib import Path
    from app.core.config import BACKEND_DIR
    parquet_path = Path(BACKEND_DIR) / "data" / "knowledge_base" / "kisanvaani_agriculture_qa.parquet"
    assert parquet_path.exists(), "KisanVaani parquet file must exist"
    df = pd.read_parquet(parquet_path)
    assert len(df) == 22615, f"Expected 22,615 rows, found {len(df)}"
    assert "question" in df.columns
    assert "answers" in df.columns


# -------------------------------------------------------------
# 28. Answer Normalization
# -------------------------------------------------------------
def test_kisanvaani_answer_normalization():
    from scripts.prepare_kisanvaani_kb import normalize_text
    assert normalize_text("  hello   world  \n\t") == "hello world"
    assert normalize_text(["First part.", "Second part."]) == "First part. Second part."
    assert normalize_text(None) == ""
    assert normalize_text("") == ""


# -------------------------------------------------------------
# 29. Empty-Row Handling
# -------------------------------------------------------------
def test_kisanvaani_empty_row_handling():
    from scripts.prepare_kisanvaani_kb import normalize_text
    # Empty or whitespace only questions and answers must normalize to empty string
    assert not normalize_text("   \n\t  ")
    assert not normalize_text(None)
    assert normalize_text("Legitimate question?") == "Legitimate question?"


# -------------------------------------------------------------
# 30. List and Array Answers Handling
# -------------------------------------------------------------
def test_kisanvaani_list_answers():
    from scripts.prepare_kisanvaani_kb import normalize_text
    ans_list = ["Crop rotation prevents soil erosion.", "It also manages pests."]
    normalized = normalize_text(ans_list)
    assert normalized == "Crop rotation prevents soil erosion. It also manages pests."


# -------------------------------------------------------------
# 31. Exact Duplicate Handling vs Distinct Answers
# -------------------------------------------------------------
def test_kisanvaani_duplicate_handling(service):
    # Distinct answers for the same question should be allowed
    rec1 = {"question": "What is the best fertilizer for beans?", "answer": "DAP applied at planting time.", "topic": "fertilizer"}
    rec2 = {"question": "What is the best fertilizer for beans?", "answer": "NPK 17:17:17 at vegetative stage.", "topic": "fertilizer"}
    
    result = service.ingest_records_bulk([rec1, rec2])
    # Exact duplicate submission
    result_dup = service.ingest_records_bulk([rec1])
    assert result_dup["added"] == 0
    assert result_dup["skipped_duplicates_or_invalid"] == 1


# -------------------------------------------------------------
# 32. Metadata Defaults and Provenance
# -------------------------------------------------------------
def test_kisanvaani_metadata_defaults():
    import json
    from pathlib import Path
    from app.core.config import BACKEND_DIR
    json_path = Path(BACKEND_DIR) / "data" / "knowledge_base" / "kisanvaani_agriculture_qa_agrinexus.json"
    assert json_path.exists()
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert len(data) >= 2331
    sample = data[0]
    assert sample["source"] == "KisanVaani Agriculture Q&A"
    assert sample["source_url"] == "https://huggingface.co/datasets/KisanVaani/agriculture-qa-english-only"
    assert sample["verified"] is False
    assert sample["language"] == "en"
    assert sample["region"] == "global"


# -------------------------------------------------------------
# 33. JSON Schema Compatibility
# -------------------------------------------------------------
def test_kisanvaani_json_schema_compatibility():
    import json
    from pathlib import Path
    from app.core.config import BACKEND_DIR
    json_path = Path(BACKEND_DIR) / "data" / "knowledge_base" / "kisanvaani_agriculture_qa_agrinexus.json"
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert isinstance(data, list)
    for r in data[:50]:
        assert "question" in r and len(r["question"]) >= 5
        assert "answer" in r and len(r["answer"]) >= 2
        assert "topic" in r and r["topic"]
        assert "source" in r and r["source"]
        assert "verified" in r and r["verified"] is False


# -------------------------------------------------------------
# 34. Ingestion and Source Traceability
# -------------------------------------------------------------
def test_kisanvaani_source_traceability(service):
    # Alternaria rot in chilli is a known KisanVaani question
    req = ChatRequest(message="What pathogen causes Alternaria rot in chilli plants?")
    resp = service.chat(req)
    assert resp.status == "success"
    assert resp.intent == AssistantIntent.STATIC_KNOWLEDGE
    assert len(resp.sources) > 0
    kisan_source = any("KisanVaani" in s.source for s in resp.sources)
    assert kisan_source is True, f"Expected KisanVaani source in {resp.sources}"


# -------------------------------------------------------------
# 35. Knowledge Base Record Count and KB Status Check
# -------------------------------------------------------------
def test_kisanvaani_kb_status(service):
    res = client.get("/api/farming-assistant/kb-status")
    assert res.status_code == 200
    data = res.json()
    assert data["record_count"] >= 2200
    assert data["target_count"] == 10000
    # Transparent reporting: ~2253 records is < 10000, so target must be False
    assert data["is_target_met"] is False
    assert "pending" in data["status_summary"].lower()


# -------------------------------------------------------------
# 36. Semantic Retrieval from Ingested Knowledge Base
# -------------------------------------------------------------
def test_kisanvaani_semantic_retrieval(service):
    # Query matching semantic meaning rather than exact keywords
    matches = service.search_knowledge_base("how can I prevent soil erosion on farmland?", top_k=3)
    assert len(matches) > 0
    # Should match crop rotation or soil erosion practices
    matched_text = " ".join([m.question.lower() + " " + m.answer.lower() for m in matches])
    assert "erosion" in matched_text or "soil" in matched_text or "crop rotation" in matched_text

