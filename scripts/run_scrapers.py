#!/usr/bin/env python3
"""
Run all deal scrapers and save to JSON.

This script is designed to run via GitHub Actions.
It fetches deals from various sources and saves them to data/deals.json.

Usage:
    python scripts/run_scrapers.py              # Run all store scrapers
    python scripts/run_scrapers.py electronics  # Run only electronics category
    python scripts/run_scrapers.py bol coolblue # Run specific stores
"""

import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.deals_store import load_deals, save_deals, cleanup_expired_deals
from backend.scrapers.stores import MultiStoreScraper, STORES, scrape_category
from backend.models import DealStatus


# Categories available
CATEGORIES = ["electronics", "food", "fashion", "beauty", "home", "sports"]


def run_stores(stores: list = None) -> list:
    """Run MultiStoreScraper for given stores (or all)"""
    scraper = MultiStoreScraper(stores=stores)
    print(f"[multi] Scraping {len(scraper.stores_to_scrape)} stores...")

    try:
        deals = scraper.fetch_deals()
        print(f"[multi] Total: {len(deals)} deals")

        # Mark all as approved (no approval queue in this version)
        for deal in deals:
            deal.status = DealStatus.APPROVED

        return deals
    except Exception as e:
        print(f"[multi] Error: {e}")
        import traceback
        traceback.print_exc()
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

    # Collect new deals
    new_deals = []

    if len(sys.argv) > 1:
        args = sys.argv[1:]

        # Check if argument is a category
        if args[0] in CATEGORIES:
            category = args[0]
            stores = [slug for slug, config in STORES.items() if config.category == category]
            print(f"Scraping category: {category} ({len(stores)} stores)")
            new_deals = run_stores(stores)
        else:
            # Assume arguments are store slugs
            valid_stores = [s for s in args if s in STORES]
            if valid_stores:
                print(f"Scraping stores: {', '.join(valid_stores)}")
                new_deals = run_stores(valid_stores)
            else:
                print(f"Unknown stores/category: {args}")
                print(f"Available stores: {', '.join(STORES.keys())}")
                print(f"Available categories: {', '.join(CATEGORIES)}")
                return
    else:
        # Run all stores
        print(f"Scraping ALL stores ({len(STORES)} total)")
        new_deals = run_stores()

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
