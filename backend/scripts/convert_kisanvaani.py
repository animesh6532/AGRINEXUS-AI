import json
from pathlib import Path

import pandas as pd


INPUT = Path("data/knowledge_base/kisanvaani_agriculture_qa.parquet")
OUTPUT = Path("data/knowledge_base/kisanvaani_agriculture_qa_agrinexus.json")

SOURCE = "KisanVaani Agriculture Q&A"
SOURCE_URL = "https://huggingface.co/datasets/KisanVaani/agriculture-qa-english-only"


def clean_text(value):
    if value is None:
        return ""
    if isinstance(value, list):
        return " ".join(str(x).strip() for x in value if str(x).strip())
    return str(value).strip()


df = pd.read_parquet(INPUT)

records = []
seen = set()

for _, row in df.iterrows():
    question = clean_text(row.get("question"))
    answer = clean_text(row.get("answers"))

    if not question or not answer:
        continue

    key = (question.casefold(), answer.casefold())

    if key in seen:
        continue

    seen.add(key)

    records.append({
        "question": question,
        "answer": answer,
        "crop": None,
        "crop_stage": None,
        "topic": "general_farming",
        "subtopic": None,
        "keywords": "",
        "language": "en",
        "region": "global",
        "source": SOURCE,
        "source_url": SOURCE_URL,
        "verified": False
    })


OUTPUT.write_text(
    json.dumps(records, ensure_ascii=False, indent=2),
    encoding="utf-8"
)

print("Conversion complete")
print(f"Input rows: {len(df)}")
print(f"Output records: {len(records)}")
print(f"Output: {OUTPUT}")
