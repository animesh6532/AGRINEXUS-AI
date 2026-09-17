"""
Script to collect market data from external APIs and store in database.
Can be run manually or scheduled for periodic data collection.
"""

import asyncio
import argparse
import sys
from datetime import datetime

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
        help="Maximum number of records to fetch per request (default: 1000)"
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

        # Fetch and store data
        logger.info("Fetching market data from external API...")
        start_time = datetime.now()

        stored_count = await market_service.fetch_and_store_latest_data(
            commodity=args.commodity,
            state=args.state,
            market=args.market,
            limit=args.limit
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
        print(f"State filter: {args.state or 'All'}")
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