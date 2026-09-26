"""
Knowledge Base Ingestion Script for AgriNexus-AI Farming Assistant.

CLI utility to:
1. Load agricultural Q&A dataset from JSON or CSV.
2. Validate required fields and minimum lengths.
3. Normalize text strings and categories.
4. Detect and skip duplicate questions.
5. Ingest into SQLite FarmingKnowledgeRecord table.
6. Recompute vector index.
7. Report progress and final record count.

Usage:
    python backend/scripts/ingest_farming_kb.py --file backend/data/knowledge_base/sample_knowledge_base.json
    python backend/scripts/ingest_farming_kb.py --file path/to/10k_farming_dataset.json
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Add project root and backend directory to path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.logging import logger
from app.database.connection import SessionLocal, create_tables
from app.services.farming_assistant_service import FarmingAssistantService


def ingest_file(file_path: str, reindex_only: bool = False) -> None:
    path = Path(file_path)
    if not path.exists():
        print(f"Error: Dataset file not found at {file_path}")
        sys.exit(1)

    print(f"Reading dataset from {path}...")
    create_tables()

    service = FarmingAssistantService()

    if reindex_only:
        print("Reindexing existing database records...")
        count = service.reload_knowledge_base()
        print(f"Reindexed {count} records successfully.")
        return

    # Load dataset
    items = []
    if path.suffix.lower() == ".json":
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                items = data
            elif isinstance(data, dict) and "records" in data:
                items = data["records"]
            else:
                print("Error: JSON must be an array of records or contain a 'records' key.")
                sys.exit(1)
    elif path.suffix.lower() == ".csv":
        import csv
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            items = list(reader)
    else:
        print(f"Error: Unsupported file format {path.suffix}. Use .json or .csv.")
        sys.exit(1)

    print(f"Loaded {len(items)} raw records. Validating, deduplicating, and ingesting...")

    db = SessionLocal()
    try:
        results = service.ingest_records_bulk(items, db=db)
        print("\nIngestion Summary:")
        print(f"  Total Processed: {results['total_processed']}")
        print(f"  Added Records:   {results['added']}")
        print(f"  Skipped (Dup/Invalid): {results['skipped_duplicates_or_invalid']}")
        print(f"  Errors:          {results['errors']}")
        print(f"  Final Total KB Records: {results['new_total_records']}")

        status = service.get_kb_status()
        print(f"\n10,000+ Verification: {'PASSED' if status['is_target_met'] else 'PENDING'}")
        print(f"Status: {status['status_summary']}\n")
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="AgriNexus-AI Farming Knowledge Ingestion")
    parser.add_argument("--file", type=str, default=str(backend_dir / "data" / "knowledge_base" / "sample_knowledge_base.json"),
                        help="Path to JSON or CSV dataset file")
    parser.add_argument("--reindex", action="store_true", help="Reindex existing records without importing new file")

    args = parser.parse_args()
    ingest_file(args.file, reindex_only=args.reindex)


if __name__ == "__main__":
    main()
