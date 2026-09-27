"""
Inspect the local SQLite market database.

Prints row counts, per-state counts, distinct commodities and the date
range that is currently available so ingestion runs can be verified.

Usage:
    python backend/scripts/check_market_db.py
    python backend/scripts/check_market_db.py --state "West Bengal"
"""

import argparse
import os
import sqlite3
import sys

DEFAULT_DB = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "market",
    "market_data.db",
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Summarise the contents of the market SQLite database"
    )
    parser.add_argument("--db", default=DEFAULT_DB, help="Path to .db file")
    parser.add_argument(
        "--state",
        default=None,
        help="Only summarise rows for this state",
    )
    args = parser.parse_args()

    if not os.path.exists(args.db):
        print(f"Database not found: {args.db}", file=sys.stderr)
        return 1

    conn = sqlite3.connect(args.db)
    cur = conn.cursor()

    where, params = "", []
    if args.state:
        where = "WHERE state = ?"
        params = [args.state]

    total = cur.execute(
        f"SELECT COUNT(*) FROM market_observations {where}", params
    ).fetchone()[0]
    print(f"db            : {args.db}")
    print(f"total rows    : {total}")

    print("\nrows by state (top 40):")
    for state, count in cur.execute(
        f"""
        SELECT state, COUNT(*) FROM market_observations
        {where} GROUP BY state ORDER BY COUNT(*) DESC LIMIT 40
        """,
        params,
    ):
        print(f"  {count:>7}  {state}")

    print("\ndistinct commodities:")
    commodities = cur.execute(
        f"""
        SELECT commodity, COUNT(*) FROM market_observations
        {where} GROUP BY commodity ORDER BY COUNT(*) DESC
        """,
        params,
    ).fetchall()
    print(f"  count: {len(commodities)}")
    for commodity, count in commodities[:40]:
        print(f"  {count:>7}  {commodity}")

    print("\ndate range / markets:")
    row = cur.execute(
        f"""
        SELECT MIN(observation_date), MAX(observation_date),
               COUNT(DISTINCT market), COUNT(DISTINCT district)
        FROM market_observations {where}
        """,
        params,
    ).fetchone()
    print(f"  dates     : {row[0]} .. {row[1]}")
    print(f"  markets   : {row[2]}")
    print(f"  districts : {row[3]}")

    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
