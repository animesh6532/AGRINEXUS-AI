"""
Data Preparation and Normalization Script for KisanVaani Agriculture Q&A.

Processes:
1. Loads backend/data/knowledge_base/kisanvaani_agriculture_qa.parquet
2. Audits all rows for nulls, empty values, types, and duplicates
3. Normalizes question and answer text (preserving original meaning without rewriting)
4. Deduplicates exact question+answer pairs while preserving distinct answers for identical questions
5. Assigns safe, deterministic AGRINEXUS metadata (crops, topics, keywords, unverified provenance)
6. Outputs backend/data/knowledge_base/kisanvaani_agriculture_qa_agrinexus.json
7. Reports complete audit and 10,000+ verification status

Usage:
    python backend/scripts/prepare_kisanvaani_kb.py
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import pandas as pd

# Paths
BACKEND_DIR = Path(__file__).resolve().parent.parent
INPUT_PARQUET = BACKEND_DIR / "data" / "knowledge_base" / "kisanvaani_agriculture_qa.parquet"
OUTPUT_JSON = BACKEND_DIR / "data" / "knowledge_base" / "kisanvaani_agriculture_qa_agrinexus.json"

SOURCE_NAME = "KisanVaani Agriculture Q&A"
SOURCE_URL = "https://huggingface.co/datasets/KisanVaani/agriculture-qa-english-only"
TARGET_RECORDS = 10000

# Deterministic Agronomic Topic Rules
TOPIC_RULES = [
    ("pest_management", ["pest", "insect", "borer", "aphid", "whitefly", "caterpillar", "infestation", "armyworm", "weevil", "mite", "locust"]),
    ("disease_management", ["disease", "fungus", "fungal", "bacterial", "virus", "viral", "blight", "blast", "rust", "mildew", "rot", "wilt", "canker", "smut", "leaf spot"]),
    ("weed_management", ["weed", "weeds", "weeding", "herbicide"]),
    ("fertilizer", ["fertilizer", "fertilizers", "npk", "nitrogen", "phosphorus", "potassium", "urea", "dap", "potash", "manure", "compost", "micronutrient", "zinc"]),
    ("irrigation", ["irrigation", "irrigate", "watering", "drip", "sprinkler", "flood irrigation", "furrow", "water requirement"]),
    ("soil_management", ["soil", "loam", "clay", "sand", "soil ph", "acidity", "alkalinity", "salinity", "humus", "soil fertility", "erosion", "tillage", "plowing"]),
    ("organic_farming", ["organic farm", "organic farming", "organic fertilizer", "biofertilizer", "vermicompost"]),
    ("sustainable_agriculture", ["crop rotation", "agroforestry", "intercropping", "sustainable", "cover crop", "mulch", "mulching", "conservation agriculture"]),
    ("livestock", ["cow", "cattle", "dairy", "goat", "sheep", "poultry", "chicken", "horse", "livestock", "animal", "pasture", "silage", "fodder", "hay", "breed", "foal"]),
    ("planting", ["planting", "transplanting", "seedling", "spacing", "seed rate", "seed population"]),
    ("sowing", ["sowing", "sow", "germination"]),
    ("harvesting", ["harvest", "harvesting", "threshing", "yield"]),
    ("post_harvest", ["storage", "post-harvest", "silo", "drying", "granary"]),
    ("market", ["market", "mandi", "price", "selling", "cost", "profit", "economy"]),
    ("weather", ["weather", "rainfall", "temperature", "frost", "drought", "monsoon", "climate", "humidity"]),
    ("farm_management", ["farm tool", "machinery", "tractor", "farm management", "farm practice", "equipment"]),
    ("crop_management", ["crop", "growth", "flowering", "tillering", "pruning", "canopy"]),
]

# Standard Crop Aliases
CROP_ALIASES = {
    "rice": "rice", "paddy": "rice",
    "wheat": "wheat",
    "maize": "maize", "corn": "maize",
    "cotton": "cotton",
    "soybean": "soybean", "soya": "soybean",
    "sugarcane": "sugarcane",
    "pulses": "pulses", "chickpea": "pulses", "gram": "pulses", "lentil": "pulses",
    "mustard": "mustard",
    "potato": "potato", "potatoes": "potato",
    "tomato": "tomato", "tomatoes": "tomato",
    "onion": "onion", "onions": "onion",
    "groundnut": "groundnut", "peanut": "groundnut",
    "barley": "barley",
    "millet": "millet", "sorghum": "sorghum",
    "cassava": "cassava",
    "apple": "apple", "apples": "apple",
    "banana": "banana", "bananas": "banana",
    "beans": "beans", "bean": "beans",
    "coffee": "coffee", "tea": "tea",
    "guava": "guava", "mango": "mango", "citrus": "citrus",
    "cabbage": "cabbage", "carrot": "carrot", "pea": "pea", "peas": "pea",
}

# Crop Growth Stages
GROWTH_STAGES = [
    "germination", "seedling", "tillering", "vegetative", "flowering",
    "booting", "panicle initiation", "grain filling", "milking", "maturity", "harvest"
]

STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being",
    "below", "between", "both", "but", "by", "can", "can't", "cannot", "could",
    "did", "do", "does", "doing", "don't", "down", "during", "each", "few", "for",
    "from", "further", "had", "has", "have", "having", "he", "her", "here", "hers",
    "herself", "him", "himself", "his", "how", "i", "if", "in", "into", "is",
    "it", "its", "itself", "let's", "me", "more", "most", "my", "myself", "no",
    "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought",
    "our", "ours", "ourselves", "out", "over", "own", "same", "she", "should",
    "so", "some", "such", "than", "that", "the", "their", "theirs", "them",
    "themselves", "then", "there", "these", "they", "this", "those", "through",
    "to", "too", "under", "until", "up", "very", "was", "we", "were", "what",
    "when", "where", "which", "while", "who", "whom", "why", "with", "would",
    "you", "your", "yours", "yourself", "yourselves"
}


def normalize_text(value: Any) -> str:
    """Robust text normalization preserving original content and handling arrays/lists."""
    if value is None:
        return ""
    if isinstance(value, list):
        parts = [str(x).strip() for x in value if x is not None and str(x).strip()]
        return " ".join(parts).strip()
    text = str(value).strip()
    # Normalize multiple whitespace, tabs, and newlines to a single space
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def classify_topic(question: str, answer: str) -> str:
    """Deterministically classify agricultural topic based on question and answer."""
    combined = f"{question} {answer}".lower()
    for topic, keywords in TOPIC_RULES:
        for kw in keywords:
            if re.search(r"\b" + re.escape(kw) + r"\b", combined):
                return topic
    return "general_farming"


def extract_crop(question: str, answer: str) -> Optional[str]:
    """Deterministically detect crop mention in question or answer."""
    combined = f"{question} {answer}".lower()
    for alias, standard in CROP_ALIASES.items():
        if re.search(r"\b" + re.escape(alias) + r"\b", combined):
            return standard
    return None


def extract_growth_stage(question: str, answer: str) -> Optional[str]:
    """Deterministically detect crop growth stage mention."""
    combined = f"{question} {answer}".lower()
    for stage in GROWTH_STAGES:
        if re.search(r"\b" + re.escape(stage) + r"\b", combined):
            return stage
    return None


def extract_keywords(question: str, answer: str, crop: Optional[str], topic: str) -> str:
    """Deterministically extract keywords from question, answer, and metadata."""
    combined = f"{question} {answer}".lower()
    tokens = re.findall(r"\b[a-z]{3,}\b", combined)
    filtered = [t for t in tokens if t not in STOPWORDS]
    
    # Priority keywords: crop and topic parts
    priority = []
    if crop:
        priority.append(crop)
    if topic and topic != "general_farming":
        priority.extend(topic.replace("_", " ").split())

    # Collect up to 8 unique keywords
    seen_kws = set()
    result = []
    for kw in priority + filtered:
        if kw not in seen_kws:
            seen_kws.add(kw)
            result.append(kw)
        if len(result) >= 8:
            break

    return ", ".join(result)


def audit_and_prepare_dataset(
    input_path: Path = INPUT_PARQUET,
    output_path: Path = OUTPUT_JSON
) -> Dict[str, Any]:
    """Load, audit, normalize, deduplicate, and prepare agricultural Q&A dataset."""
    if not input_path.exists():
        raise FileNotFoundError(f"Source Parquet dataset not found at: {input_path}")

    print("=" * 60)
    print("AGRINEXUS-AI KNOWLEDGE BASE AUDIT & PREPARATION")
    print(f"Source file: {input_path}")
    print("=" * 60)

    df = pd.read_parquet(input_path)
    total_rows = len(df)

    empty_questions = 0
    empty_answers = 0
    invalid_rows = 0
    list_answers_count = 0
    whitespace_only_questions = 0
    whitespace_only_answers = 0

    valid_records: List[Dict[str, Any]] = []
    seen_exact_pairs: Set[Tuple[str, str]] = set()
    exact_duplicates_removed = 0
    questions_with_multiple_answers: Dict[str, List[str]] = {}

    for idx, row in df.iterrows():
        raw_q = row.get("question")
        raw_a = row.get("answers")

        if isinstance(raw_a, list):
            list_answers_count += 1

        norm_q = normalize_text(raw_q)
        norm_a = normalize_text(raw_a)

        # Audit checks
        is_q_empty = not norm_q
        is_a_empty = not norm_a

        if raw_q is not None and str(raw_q).strip() == "" and str(raw_q) != "":
            whitespace_only_questions += 1
        if raw_a is not None and str(raw_a).strip() == "" and str(raw_a) != "":
            whitespace_only_answers += 1

        if is_q_empty:
            empty_questions += 1
        if is_a_empty:
            empty_answers += 1

        if is_q_empty or is_a_empty:
            invalid_rows += 1
            continue

        # Exact duplicate check: same normalized question AND same normalized answer
        pair_key = (norm_q.casefold(), norm_a.casefold())
        if pair_key in seen_exact_pairs:
            exact_duplicates_removed += 1
            continue

        seen_exact_pairs.add(pair_key)

        # Track multiple answers for identical questions
        q_fold = norm_q.casefold()
        if q_fold not in questions_with_multiple_answers:
            questions_with_multiple_answers[q_fold] = []
        questions_with_multiple_answers[q_fold].append(norm_a)

        # Deterministic metadata derivation
        detected_crop = extract_crop(norm_q, norm_a)
        detected_stage = extract_growth_stage(norm_q, norm_a)
        detected_topic = classify_topic(norm_q, norm_a)
        keywords = extract_keywords(norm_q, norm_a, detected_crop, detected_topic)

        record = {
            "question": norm_q,
            "answer": norm_a,
            "crop": detected_crop,
            "crop_stage": detected_stage,
            "topic": detected_topic,
            "subtopic": None,
            "keywords": keywords,
            "language": "en",
            "region": "global",
            "source": SOURCE_NAME,
            "source_url": SOURCE_URL,
            "verified": False  # Must not be marked verified without human verification
        }
        valid_records.append(record)

    multi_answer_questions = sum(1 for answers in questions_with_multiple_answers.values() if len(answers) > 1)

    # Save to output file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(valid_records, f, ensure_ascii=False, indent=2)

    is_target_met = len(valid_records) >= TARGET_RECORDS

    report = {
        "dataset_name": SOURCE_NAME,
        "input_rows": total_rows,
        "valid_qa_rows": total_rows - invalid_rows,
        "invalid_rows": invalid_rows,
        "empty_questions": empty_questions,
        "empty_answers": empty_answers,
        "list_answers_count": list_answers_count,
        "whitespace_only_questions": whitespace_only_questions,
        "whitespace_only_answers": whitespace_only_answers,
        "exact_duplicates_removed": exact_duplicates_removed,
        "unique_questions_with_multiple_answers": multi_answer_questions,
        "final_records": len(valid_records),
        "target": TARGET_RECORDS,
        "target_met": is_target_met,
        "output_file": str(output_path)
    }

    # Print required audit report
    print("\n" + "=" * 60)
    print("AUDIT & PREPARATION REPORT")
    print("=" * 60)
    print(f"Input rows: {report['input_rows']}")
    print(f"Valid Q&A rows: {report['valid_qa_rows']}")
    print(f"Invalid rows: {report['invalid_rows']}")
    print(f"Empty questions: {report['empty_questions']}")
    print(f"Empty answers: {report['empty_answers']}")
    print(f"Exact duplicates removed: {report['exact_duplicates_removed']}")
    print(f"Unique questions with multiple legitimate answers: {report['unique_questions_with_multiple_answers']}")
    print(f"Final records: {report['final_records']}")
    print(f"Target: {report['target']}")
    print(f"Target met: {'true' if report['target_met'] else 'false'}")
    print(f"Output: {report['output_file']}")
    print("=" * 60)

    if not is_target_met:
        print(f"\n[NOTE] 10,000+ target is NOT MET because the available legitimate source data produced only {report['final_records']} usable records.")
        print(f"       Difference to target: {TARGET_RECORDS - report['final_records']} records.")
        print("       Per project guidelines, fake or duplicated records were NOT generated to artificially reach 10,000.\n")

    return report


def main():
    try:
        report = audit_and_prepare_dataset()
        print("Dataset preparation completed successfully.")
        sys.exit(0)
    except Exception as exc:
        print(f"Error during dataset preparation: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
