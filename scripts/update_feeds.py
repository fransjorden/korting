#!/usr/bin/env python3
"""
Cron script to update deals from affiliate feeds.

Run this script periodically (e.g., every 1-6 hours) to keep deals fresh.

Usage:
    python scripts/update_feeds.py

Cron example (every 2 hours):
    0 */2 * * * cd /path/to/kort.ing && python scripts/update_feeds.py
"""

import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database import init_db
from backend.feed_fetcher import update_deals_from_feeds, EXAMPLE_FEED_URLS


def main():
    print(f"[{datetime.now().isoformat()}] Starting feed update...")

    # Initialize database
    init_db()

    # Define your feed URLs here (after getting affiliate approval)
    feed_urls = {
        # Uncomment and add your real feed URLs:
        # "daisycon": "https://datafeed.daisycon.com/feeds/YOUR_ID/products.xml",
        # "tradetracker": "https://pf.tradetracker.net/feed/YOUR_ID/products.xml",
    }

    if not feed_urls:
        print("No feed URLs configured. Using mock data.")
        print("To add real feeds, edit scripts/update_feeds.py with your affiliate feed URLs.")
        return

    # Update deals from feeds
    total = update_deals_from_feeds(feed_urls)

    print(f"[{datetime.now().isoformat()}] Feed update complete. {total} deals processed.")


if __name__ == "__main__":
    main()
