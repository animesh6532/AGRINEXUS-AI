"""
Script to collect market data from external APIs and store in database.
Can be run manually or scheduled for periodic data collection.
"""

import asyncio
import argparse
import sys
from datetime import datetime
from typing import List, Optional

from backend.app.core.logging import logger
from backend.app.services.market_service import MarketService
from backend.app.database import connection


async def main():
    """Main function for market data collection script."""
    parser = argparse.ArgumentParser(
        description="Collect market data from government APIs"
    )
    parser.add_argument(
        "--commodity",
        type=str,
        help="Commodity to filter (optional, collects all if not specified)"
    )
    parser.add_argument(
        "--state",
        type=str,
        help="State to filter (optional)"
    )
    parser.add_argument(
        "--market",
        type=str,
        help="Market to filter (optional)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=1000,
        help="Maximum total number of records to fetch (default: 1000)"
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=20,
        help="Maximum API pages to walk using offset pagination "
             "(default: 20)"
    )
    parser.add_argument(
        "--page-size",
        type=int,
        default=None,
        help="Records requested per API page (default: min(limit, 500))"
    )
    parser.add_argument(
        "--state-file",
        type=str,
        default=None,
        help="Optional path to a text file with one state name per line; "
             "each state is fetched separately for complete coverage"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Configure logging level
    if args.verbose:
        logger.setLevel("DEBUG")
        logger.debug("Verbose logging enabled")

    logger.info("Starting market data collection script")
    logger.info(f"Arguments: {vars(args)}")

    try:
        # Initialize database
        logger.info("Initializing database connection...")
        connection.create_tables()
        logger.info("Database initialized successfully")

        # Create market service
        db = connection.SessionLocal()
        market_service = MarketService(db)

        # data.gov.in serves pages in ingestion order, so a single
        # unfiltered walk only ever reaches a shallow slice of states.
        # Fetching one state at a time gives every state (for example
        # West Bengal) a full, dedicated paging window.
        states: List[Optional[str]] = [args.state]
        if args.state_file:
            with open(args.state_file, "r", encoding="utf-8") as handle:
                states = [
                    line.strip()
                    for line in handle
                    if line.strip() and not line.strip().startswith("#")
                ]
            logger.info(
                f"Loaded {len(states)} state filter(s) from "
                f"{args.state_file}"
            )

        # Fetch and store data
        logger.info("Fetching market data from external API...")
        start_time = datetime.now()

        stored_count = 0
        for index, state_name in enumerate(states, start=1):
            logger.info(
                f"[{index}/{len(states)}] fetching state={state_name or 'All'}"
            )
            stored = await market_service.fetch_and_store_latest_data(
                commodity=args.commodity,
                state=state_name,
                market=args.market,
                limit=args.limit,
                max_pages=args.max_pages,
                page_size=args.page_size
            )
            stored_count += stored
            logger.info(
                f"[{index}/{len(states)}] state={state_name or 'All'} "
                f"stored={stored}"
            )

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        logger.info(
            f"Market data collection completed successfully\n"
            f"Records stored: {stored_count}\n"
            f"Duration: {duration:.2f} seconds"
        )

        # Print summary
        print(f"\n=== Market Data Collection Summary ===")
        print(f"Commodity filter: {args.commodity or 'All'}")
        print(f"State filter(s): {args.state or f'{len(states)} states' }")
        print(f"Market filter: {args.market or 'All'}")
        print(f"Records stored: {stored_count}")
        print(f"Duration: {duration:.2f} seconds")
        print(f"Timestamp: {end_time.isoformat()}")

        # Close database connection
        db.close()

        return 0

    except Exception as e:
        logger.error(f"Error in market data collection: {e}", exc_info=True)
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))