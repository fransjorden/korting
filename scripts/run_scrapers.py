#!/usr/bin/env python3
"""
Run all deal scrapers and save to JSON.

This script is designed to run via GitHub Actions.
It fetches deals from various sources and saves them to data/deals.json.

Usage:
    python scripts/run_scrapers.py           # Run all scrapers
    python scripts/run_scrapers.py pepper    # Run only Pepper scraper
"""

import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.deals_store import load_deals, save_deals, cleanup_expired_deals
from backend.scrapers.pepper import PepperScraper
from backend.scrapers.bol import BolScraper
from backend.models import DealStatus


SCRAPERS = {
    "pepper": PepperScraper,
    "bol": BolScraper,
}


def run_scraper_and_collect(scraper_class) -> list:
    """Run a scraper and return the deals (don't save yet)"""
    scraper = scraper_class()
    print(f"[{scraper.name}] Fetching deals...")

    try:
        deals = scraper.fetch_deals()
        print(f"[{scraper.name}] Found {len(deals)} deals")

        # Mark all as approved (no approval queue in this version)
        for deal in deals:
            deal.status = DealStatus.APPROVED

        return deals
    except Exception as e:
        print(f"[{scraper.name}] Error: {e}")
        return []


def main():
    print(f"\n{'='*50}")
    print(f" kort.ing Deal Scraper")
    print(f" {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}\n")

    # Load existing deals
    existing_deals = load_deals()
    existing_ids = {d.id for d in existing_deals}
    print(f"Existing deals: {len(existing_deals)}")

    # Collect new deals from scrapers
    new_deals = []

    if len(sys.argv) > 1:
        # Run specific scraper(s)
        for scraper_name in sys.argv[1:]:
            if scraper_name in SCRAPERS:
                deals = run_scraper_and_collect(SCRAPERS[scraper_name])
                new_deals.extend(deals)
            else:
                print(f"Unknown scraper: {scraper_name}")
    else:
        # Run all scrapers
        for name, scraper_class in SCRAPERS.items():
            deals = run_scraper_and_collect(scraper_class)
            new_deals.extend(deals)

    # Filter out duplicates
    unique_new = [d for d in new_deals if d.id not in existing_ids]
    print(f"\nNew unique deals: {len(unique_new)}")

    # Combine and save
    all_deals = existing_deals + unique_new
    save_deals(all_deals)

    # Cleanup expired
    removed = cleanup_expired_deals()
    if removed > 0:
        print(f"Removed {removed} expired deals")

    # Final count
    final_deals = load_deals()

    print(f"\n{'='*50}")
    print(f" Summary")
    print(f"{'='*50}")
    print(f" New deals added: {len(unique_new)}")
    print(f" Total deals: {len(final_deals)}")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    main()
