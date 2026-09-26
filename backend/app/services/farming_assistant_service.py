"""
Farming Assistant Service Layer.

Responsibilities:
1. Local lightweight embedding generation (Sentence-Transformers with robust TF-IDF fallback).
2. Semantic vector index management and cosine-similarity search over Q&A records.
3. Agronomic Q&A retrieval with similarity thresholding and crop/topic filtering.
4. Bounded conversation context memory management.
5. Ingestion, deduplication, and indexing pipeline for agricultural knowledge base records.
6. Integration with upstream AGRINEXUS intelligence modules (Personalized Action Plan,
   Smart Alerts, Risk & Opportunity, Decision Engine, Weather, Market).
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from sqlalchemy.orm import Session

from app.core.config import BACKEND_DIR, settings
from app.core.logging import logger
from app.database.connection import SessionLocal
from app.database.models import FarmingKnowledgeRecord
from app.intelligence.farming_assistant import (
    ENGINE_VERSION,
    FALLBACK_NO_MATCH,
    NON_FARMING_REDIRECT,
    SUPPORTED_CROPS,
    SUPPORTED_TOPICS,
    AssistantIntent,
    classify_assistant_intent,
    extract_agronomic_entities,
    synthesize_dynamic_response,
)
from app.schemas.farming_assistant import (
    ChatRequest,
    ChatResponse,
    FarmingKnowledgeMatch,
    FarmingKnowledgeRecordCreate,
    KnowledgeSourceInfo,
)

_DEFAULT_EMBEDDER: Optional["LocalEmbeddingEngine"] = None


def get_default_embedder() -> "LocalEmbeddingEngine":
    global _DEFAULT_EMBEDDER
    if _DEFAULT_EMBEDDER is None:
        _DEFAULT_EMBEDDER = LocalEmbeddingEngine()
    return _DEFAULT_EMBEDDER


class LocalEmbeddingEngine:
    """
    Local embedding engine providing 100% offline vector representation.
    Prefers SentenceTransformers; falls back gracefully to Scikit-Learn TF-IDF
    vectorizer with L2-normalized dense embeddings for maximum reliability.
    """

    def __init__(self, model_name: Optional[str] = None) -> None:
        self.model_name = model_name or settings.FARMING_EMBEDDING_MODEL
        self._st_model = None
        self._tfidf_vectorizer = None
        self.embedding_dimension = 384
        self.backend = "uninitialized"
        self._initialize_engine()

    def _initialize_engine(self) -> None:
        # Check if sentence-transformers can be loaded quickly
        try:
            from sentence_transformers import SentenceTransformer
            # Disable tokenizers parallelism warning
            os.environ["TOKENIZERS_PARALLELISM"] = "false"
            logger.info("Initializing SentenceTransformer: %s", self.model_name)
            self._st_model = SentenceTransformer(self.model_name)
            if hasattr(self._st_model, "get_embedding_dimension"):
                self.embedding_dimension = self._st_model.get_embedding_dimension()
            else:
                self.embedding_dimension = self._st_model.get_sentence_embedding_dimension()
            self.backend = "sentence-transformers"
            logger.info("SentenceTransformer initialized successfully (dim=%d)", self.embedding_dimension)
            return
        except Exception as exc:
            logger.warning("SentenceTransformer not available or failed to load (%s). Falling back to TF-IDF vectorizer.", exc)

        self._init_tfidf()

    def _init_tfidf(self) -> None:
        from sklearn.feature_extraction.text import TfidfVectorizer
        self._tfidf_vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            max_features=512,
            sublinear_tf=True
        )
        self.embedding_dimension = 512
        self.backend = "tfidf-fallback"

    def fit_fallback_corpus(self, texts: List[str]) -> None:
        """Fit fallback TF-IDF vectorizer if using fallback backend."""
        if self.backend == "tfidf-fallback" and self._tfidf_vectorizer and texts:
            try:
                self._tfidf_vectorizer.fit(texts)
                self.embedding_dimension = len(self._tfidf_vectorizer.get_feature_names_out())
            except Exception as e:
                logger.error("Failed to fit TF-IDF vectorizer: %s", e)

    def encode(self, texts: List[str]) -> np.ndarray:
        """Generate normalized 2D numpy array of embeddings."""
        if not texts:
            return np.empty((0, self.embedding_dimension), dtype=np.float32)

        if self._st_model and self.backend == "sentence-transformers":
            try:
                raw = self._st_model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
                norms = np.linalg.norm(raw, axis=1, keepdims=True)
                norms[norms == 0.0] = 1.0
                return (raw / norms).astype(np.float32)
            except Exception as exc:
                logger.warning("SentenceTransformer encode error (%s). Falling back to TF-IDF.", exc)
                self._init_tfidf()

        # Fallback vectorizer
        if self._tfidf_vectorizer:
            try:
                sparse = self._tfidf_vectorizer.transform(texts)
                dense = sparse.toarray().astype(np.float32)
                norms = np.linalg.norm(dense, axis=1, keepdims=True)
                norms[norms == 0.0] = 1.0
                return dense / norms
            except Exception:
                # If vectorizer is not yet fitted, fit on incoming batch
                self._tfidf_vectorizer.fit(texts)
                sparse = self._tfidf_vectorizer.transform(texts)
                dense = sparse.toarray().astype(np.float32)
                norms = np.linalg.norm(dense, axis=1, keepdims=True)
                norms[norms == 0.0] = 1.0
                return dense / norms

        return np.zeros((len(texts), self.embedding_dimension), dtype=np.float32)


class FarmingAssistantService:
    """Core Farming Assistant Service orchestrating retrieval and intelligence."""

    def __init__(self, embedder: Optional[LocalEmbeddingEngine] = None) -> None:
        self.engine_version = ENGINE_VERSION
        self.top_k = settings.FARMING_ASSISTANT_TOP_K
        self.similarity_threshold = settings.FARMING_ASSISTANT_SIMILARITY_THRESHOLD
        self.max_history = settings.FARMING_ASSISTANT_MAX_HISTORY
        self.embedder = embedder or get_default_embedder()

        # In-memory vector store caches
        self._record_cache: List[Dict[str, Any]] = []
        self._embedding_matrix: Optional[np.ndarray] = None
        self._conversation_memory: Dict[str, List[Dict[str, str]]] = {}

        # Auto-load existing records from SQLite and seed default sample dataset if DB is empty
        self.reload_knowledge_base()

    def reload_knowledge_base(self) -> int:
        """Synchronize in-memory vector index with SQLite knowledge base records."""
        db: Session = SessionLocal()
        try:
            records = db.query(FarmingKnowledgeRecord).all()
            existing_questions = {
                re.sub(r"[^\w\s]", "", r.question.lower().strip()): r
                for r in records
            }

            sample_file = Path(BACKEND_DIR) / "data" / "knowledge_base" / "sample_knowledge_base.json"
            if sample_file.exists():
                with open(sample_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    added_any = False
                    for item in data:
                        norm_q = re.sub(r"[^\w\s]", "", item["question"].lower().strip())
                        if norm_q not in existing_questions:
                            rec = FarmingKnowledgeRecord(
                                question=item["question"],
                                answer=item["answer"],
                                crop=item.get("crop"),
                                crop_stage=item.get("crop_stage"),
                                topic=item.get("topic", "crop_management"),
                                subtopic=item.get("subtopic"),
                                keywords=item.get("keywords"),
                                language=item.get("language", "en"),
                                region=item.get("region"),
                                source=item.get("source", "AGRINEXUS Agronomic Knowledge Base"),
                                source_url=item.get("source_url"),
                                verified=item.get("verified", True)
                            )
                            db.add(rec)
                            existing_questions[norm_q] = rec
                            added_any = True
                        else:
                            ex_rec = existing_questions[norm_q]
                            if ex_rec.answer != item["answer"]:
                                ex_rec.answer = item["answer"]
                                added_any = True
                    if added_any:
                        db.commit()
                        records = db.query(FarmingKnowledgeRecord).all()

            self._record_cache = [r.to_dict() for r in records]

            # Fit TF-IDF on corpus if using fallback backend
            if self.embedder.backend == "tfidf-fallback" and self._record_cache:
                corpus = [
                    f"{r['question']} {r['answer']} {r.get('keywords') or ''} {r.get('crop') or ''}"
                    for r in self._record_cache
                ]
                self.embedder.fit_fallback_corpus(corpus)

            # Generate and cache embeddings
            if self._record_cache:
                texts = [
                    f"{r['question']} {r['answer']} {r.get('keywords') or ''} {r.get('crop') or ''}"
                    for r in self._record_cache
                ]
                self._embedding_matrix = self.embedder.encode(texts)
            else:
                self._embedding_matrix = None

            logger.info("Knowledge base index loaded: %d records", len(self._record_cache))
            return len(self._record_cache)
        except Exception as exc:
            logger.error("Error loading knowledge base: %s", exc)
            return len(self._record_cache)
        finally:
            db.close()

    def get_kb_record_count(self) -> int:
        """Return the exact count of records stored in the knowledge base."""
        return len(self._record_cache)

    def health(self) -> Dict[str, Any]:
        """Health status check for Farming Assistant service."""
        count = self.get_kb_record_count()
        return {
            "status": "healthy",
            "service": "agrinexus-farming-assistant",
            "version": self.engine_version,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "embedding_model": self.embedder.model_name,
            "embedding_dimension": self.embedder.embedding_dimension,
            "vector_search_ready": self._embedding_matrix is not None and len(self._embedding_matrix) > 0,
            "knowledge_base_record_count": count,
            "knowledge_base_target_met": count >= 10000,
            "upstream_dependencies": [
                "decision_engine",
                "risk_opportunity",
                "smart_alerts",
                "action_plan",
                "weather_intelligence",
                "market_intelligence"
            ]
        }

    def capabilities(self) -> Dict[str, Any]:
        """Expose supported agronomic domains, crops, and routing capabilities."""
        return {
            "service": "agrinexus-farming-assistant",
            "version": self.engine_version,
            "supported_topics": SUPPORTED_TOPICS,
            "supported_crops": SUPPORTED_CROPS,
            "routing_intents": [i.value for i in AssistantIntent],
            "features": {
                "semantic_vector_search": True,
                "local_embeddings": True,
                "no_external_llm_required": True,
                "dynamic_agrinexus_routing": True,
                "grounded_source_traceability": True,
                "farming_only_scope_gate": True,
                "conversation_memory": True
            },
            "similarity_threshold": self.similarity_threshold,
            "top_k": self.top_k,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    def get_kb_status(self) -> Dict[str, Any]:
        """Detailed status and dataset verification for the 10,000+ requirement."""
        count = self.get_kb_record_count()
        target = 10000
        is_target_met = count >= target

        if is_target_met:
            dataset_status = "target_achieved"
            status_msg = f"Knowledge base contains {count} records (target of {target}+ achieved)."
        elif count > 100:
            dataset_status = "kisanvaani_ingested_pending_additional_sources"
            status_msg = f"Knowledge base contains {count} records. (Target: {target}+ records; full population pending external dataset)."
        else:
            dataset_status = "sample_installed_pending_10k_dataset"
            status_msg = f"Knowledge base contains {count} records. (Target: {target}+ records; full population pending external dataset)."

        return {
            "record_count": count,
            "verified_count": len([r for r in self._record_cache if r.get("verified")]),
            "target_count": target,
            "is_target_met": is_target_met,
            "status_summary": status_msg,
            "embedding_model": self.embedder.model_name,
            "dataset_status": dataset_status,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    def search_knowledge_base(
        self,
        query: str,
        top_k: Optional[int] = None,
        similarity_threshold: Optional[float] = None,
        crop_filter: Optional[str] = None,
        topic_filter: Optional[str] = None
    ) -> List[FarmingKnowledgeMatch]:
        """
        Execute semantic vector search over precomputed knowledge base embeddings.
        Applies similarity thresholding and optional agronomic metadata filters.
        """
        k = top_k or self.top_k
        thresh = similarity_threshold if similarity_threshold is not None else self.similarity_threshold

        if not self._record_cache or self._embedding_matrix is None or len(self._embedding_matrix) == 0:
            return []

        # Generate single query embedding
        q_vec = self.embedder.encode([query])[0]

        # Cosine similarity via dot product (both vectors are L2-normalized)
        scores = np.dot(self._embedding_matrix, q_vec)

        # Rank indices
        ranked_indices = np.argsort(scores)[::-1]

        matches: List[FarmingKnowledgeMatch] = []
        for idx in ranked_indices:
            score = float(scores[idx])
            if score < thresh:
                break

            record = self._record_cache[idx]

            # Crop filter
            if crop_filter:
                rec_crop = (record.get("crop") or "").lower()
                if rec_crop != crop_filter.lower():
                    continue

            # Topic filter
            if topic_filter:
                rec_topic = (record.get("topic") or "").lower()
                if rec_topic != topic_filter.lower():
                    continue

            matches.append(
                FarmingKnowledgeMatch(
                    id=record["id"],
                    question=record["question"],
                    answer=record["answer"],
                    crop=record.get("crop"),
                    crop_stage=record.get("crop_stage"),
                    topic=record["topic"],
                    subtopic=record.get("subtopic"),
                    keywords=record.get("keywords"),
                    language=record.get("language", "en"),
                    region=record.get("region"),
                    source=record.get("source", "AGRINEXUS Farming Knowledge Base"),
                    source_url=record.get("source_url"),
                    similarity_score=round(score, 4)
                )
            )

            if len(matches) >= k:
                break

        return matches

    def chat(self, request: ChatRequest) -> ChatResponse:
        """
        End-to-end conversation handler.
        1. Classifies intent (scope gate & dynamic routing).
        2. Routes to AGRINEXUS dynamic intelligence or vector knowledge base.
        3. Maintains bounded session memory.
        4. Synthesizes grounded answer without hallucinating facts.
        """
        cid = request.conversation_id or str(uuid.uuid4())
        msg = request.message.strip()

        # Validate empty question
        if not msg:
            raise ValueError("User message cannot be empty.")

        # Classify intent
        intent = classify_assistant_intent(msg, request)

        # 1. Out-of-scope enforcement
        if intent == AssistantIntent.OUT_OF_SCOPE:
            self._record_conversation(cid, "user", msg)
            self._record_conversation(cid, "assistant", NON_FARMING_REDIRECT)
            return ChatResponse(
                status="out_of_scope",
                answer=NON_FARMING_REDIRECT,
                intent=intent,
                confidence=1.0,
                sources=[],
                knowledge_matches=[],
                conversation_id=cid,
                follow_up_question="You can ask me questions about crop management, soil health, pests, diseases, irrigation, or fertilizer.",
                dynamic_data_used=[],
                created_at=datetime.now(timezone.utc).isoformat()
            )

        # 2. Dynamic AGRINEXUS modules routing
        if intent != AssistantIntent.STATIC_KNOWLEDGE:
            dynamic_answer, modules_used = synthesize_dynamic_response(intent, request)
            self._record_conversation(cid, "user", msg)
            self._record_conversation(cid, "assistant", dynamic_answer)
            return ChatResponse(
                status="success",
                answer=dynamic_answer,
                intent=intent,
                confidence=0.95,
                sources=[],
                knowledge_matches=[],
                conversation_id=cid,
                follow_up_question="Would you like more details on any of these recommendations or risk items?",
                dynamic_data_used=modules_used,
                created_at=datetime.now(timezone.utc).isoformat()
            )

        # 3. Static Knowledge Base retrieval
        # Extract agronomic context to assist filtering if user did not explicitly provide one
        entities = extract_agronomic_entities(msg)
        crop_filter = request.crop_filter or entities.get("crop")
        topic_filter = request.topic_filter or entities.get("topic")

        # First attempt search with crop filter if available
        matches = self.search_knowledge_base(
            query=msg,
            top_k=request.max_results or self.top_k,
            similarity_threshold=self.similarity_threshold,
            crop_filter=crop_filter,
            topic_filter=topic_filter
        )

        # If no match with strict filters, attempt global search without filters
        if not matches and (crop_filter or topic_filter):
            matches = self.search_knowledge_base(
                query=msg,
                top_k=request.max_results or self.top_k,
                similarity_threshold=self.similarity_threshold
            )

        # Check if match was found
        if not matches:
            follow_up = None
            if not entities.get("crop"):
                follow_up = "What crop are you asking about, or what growth stage is it currently in?"

            self._record_conversation(cid, "user", msg)
            self._record_conversation(cid, "assistant", FALLBACK_NO_MATCH)
            return ChatResponse(
                status="no_match",
                answer=FALLBACK_NO_MATCH,
                intent=intent,
                confidence=0.0,
                sources=[],
                knowledge_matches=[],
                conversation_id=cid,
                follow_up_question=follow_up,
                dynamic_data_used=[],
                created_at=datetime.now(timezone.utc).isoformat()
            )

        # Top match grounded answer
        best_match = matches[0]
        answer_text = best_match.answer

        # Preserve sources
        sources = [
            KnowledgeSourceInfo(
                knowledge_id=m.id,
                source=m.source,
                source_url=m.source_url,
                crop=m.crop,
                topic=m.topic,
                relevance_score=m.similarity_score
            )
            for m in matches
        ]

        # Follow-up suggestion
        follow_up = None
        if not entities.get("crop") and best_match.crop:
            follow_up = f"Are you inquiring specifically for {best_match.crop.capitalize()} or a different crop?"

        self._record_conversation(cid, "user", msg)
        self._record_conversation(cid, "assistant", answer_text)

        return ChatResponse(
            status="success",
            answer=answer_text,
            intent=intent,
            confidence=best_match.similarity_score,
            sources=sources,
            knowledge_matches=matches,
            conversation_id=cid,
            follow_up_question=follow_up,
            dynamic_data_used=[],
            created_at=datetime.now(timezone.utc).isoformat()
        )

    def _record_conversation(self, cid: str, role: str, text: str) -> None:
        """Store bounded conversation history."""
        if cid not in self._conversation_memory:
            self._conversation_memory[cid] = []
        self._conversation_memory[cid].append({"role": role, "text": text})
        # Bound history length
        if len(self._conversation_memory[cid]) > self.max_history:
            self._conversation_memory[cid] = self._conversation_memory[cid][-self.max_history:]

    def get_conversation_history(self, cid: str) -> List[Dict[str, str]]:
        """Retrieve bounded history for session."""
        return self._conversation_memory.get(cid, [])

    def clear_conversation_history(self, cid: str) -> None:
        """Clear session memory."""
        if cid in self._conversation_memory:
            del self._conversation_memory[cid]

    def ingest_record(self, item: FarmingKnowledgeRecordCreate, db: Optional[Session] = None) -> FarmingKnowledgeRecord:
        """Ingest, validate, deduplicate, and index a single knowledge record."""
        session = db or SessionLocal()
        try:
            # Check duplicate question via normalized string
            norm_q = re.sub(r"[^\w\s]", "", item.question.lower().strip())
            for existing in self._record_cache:
                ex_norm = re.sub(r"[^\w\s]", "", existing["question"].lower().strip())
                if norm_q == ex_norm:
                    logger.info("Skipping duplicate knowledge question: %s", item.question)
                    return session.query(FarmingKnowledgeRecord).filter_by(id=existing["id"]).first()

            rec = FarmingKnowledgeRecord(
                question=item.question.strip(),
                answer=item.answer.strip(),
                crop=item.crop.lower().strip() if item.crop else None,
                crop_stage=item.crop_stage.lower().strip() if item.crop_stage else None,
                topic=item.topic.lower().strip(),
                subtopic=item.subtopic.lower().strip() if item.subtopic else None,
                keywords=item.keywords.strip() if item.keywords else None,
                language=item.language.strip() if item.language else "en",
                region=item.region.strip() if item.region else None,
                source=item.source.strip() if item.source else "AGRINEXUS Farming Knowledge Base",
                source_url=item.source_url.strip() if item.source_url else None,
                verified=item.verified
            )
            session.add(rec)
            session.commit()
            session.refresh(rec)

            # Reload into memory index
            self.reload_knowledge_base()
            return rec
        finally:
            if not db:
                session.close()

    def ingest_records_bulk(self, items: List[Dict[str, Any]], db: Optional[Session] = None) -> Dict[str, Any]:
        """Bulk ingest and index verified farming records."""
        session = db or SessionLocal()
        added = 0
        skipped = 0
        errors = 0

        try:
            # Pre-load existing normalized question-answer pairs for exact deduplication
            existing_pairs = {
                (
                    re.sub(r"[^\w\s]", "", r["question"].lower().strip()),
                    re.sub(r"\s+", " ", r["answer"].lower().strip())
                )
                for r in self._record_cache
            }

            to_add: List[FarmingKnowledgeRecord] = []
            for item in items:
                try:
                    q = item.get("question", "").strip()
                    a = item.get("answer", "").strip()
                    if not q or not a or len(q) < 5 or len(a) < 2:
                        skipped += 1
                        continue

                    norm_q = re.sub(r"[^\w\s]", "", q.lower().strip())
                    norm_a = re.sub(r"\s+", " ", a.lower().strip())
                    pair_key = (norm_q, norm_a)
                    if pair_key in existing_pairs:
                        skipped += 1
                        continue

                    existing_pairs.add(pair_key)
                    to_add.append(
                        FarmingKnowledgeRecord(
                            question=q,
                            answer=a,
                            crop=item.get("crop", "").lower().strip() or None if item.get("crop") else None,
                            crop_stage=item.get("crop_stage", "").lower().strip() or None if item.get("crop_stage") else None,
                            topic=item.get("topic", "general_farming").lower().strip(),
                            subtopic=item.get("subtopic", "").lower().strip() or None if item.get("subtopic") else None,
                            keywords=item.get("keywords", "").strip() or None if item.get("keywords") else None,
                            language=item.get("language", "en"),
                            region=item.get("region", "global"),
                            source=item.get("source", "AGRINEXUS Farming Knowledge Base"),
                            source_url=item.get("source_url"),
                            verified=bool(item.get("verified", False))
                        )
                    )
                    added += 1
                except Exception:
                    errors += 1

            if to_add:
                session.bulk_save_objects(to_add)
                session.commit()
                self.reload_knowledge_base()

            return {
                "total_processed": len(items),
                "added": added,
                "skipped_duplicates_or_invalid": skipped,
                "errors": errors,
                "new_total_records": self.get_kb_record_count()
            }
        finally:
            if not db:
                session.close()
