"""
Feed Fetcher - Parses affiliate network XML feeds and stores deals.

This module handles fetching and parsing product/deal feeds from various
affiliate networks like Daisycon, TradeTracker, and Awin.
"""

import xml.etree.ElementTree as ET
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Dict, Any
from urllib.request import urlopen, Request
from urllib.error import URLError
import json

from .config import FEEDS_DIR, DAISYCON_API_KEY, DAISYCON_PUBLISHER_ID
from .models import Deal
from .database import insert_deal


# Category mapping from feed categories to our categories
CATEGORY_MAPPING = {
    # Electronics
    "elektronica": "electronics",
    "electronics": "electronics",
    "computers": "electronics",
    "telefoons": "electronics",
    "phones": "electronics",
    "audio": "electronics",
    "video": "electronics",
    "tv": "electronics",
    "gaming": "electronics",
    "games": "electronics",

    # Fashion
    "mode": "fashion",
    "fashion": "fashion",
    "kleding": "fashion",
    "clothing": "fashion",
    "schoenen": "fashion",
    "shoes": "fashion",
    "accessoires": "fashion",

    # Home
    "wonen": "home",
    "home": "home",
    "huis": "home",
    "tuin": "home",
    "garden": "home",
    "meubels": "home",
    "furniture": "home",
    "keuken": "home",
    "kitchen": "home",

    # Sports
    "sport": "sports",
    "sports": "sports",
    "fitness": "sports",
    "outdoor": "sports",
    "fietsen": "sports",

    # Beauty
    "beauty": "beauty",
    "gezondheid": "beauty",
    "health": "beauty",
    "cosmetica": "beauty",
    "parfum": "beauty",

    # Food
    "food": "food",
    "eten": "food",
    "drinken": "food",
    "supermarkt": "food",
    "groceries": "food",

    # Travel
    "reizen": "travel",
    "travel": "travel",
    "vakantie": "travel",
    "hotels": "travel",
    "vluchten": "travel",
}


def map_category(feed_category: str) -> str:
    """Map feed category to our category slugs"""
    if not feed_category:
        return "other"

    normalized = feed_category.lower().strip()

    # Check direct mapping
    if normalized in CATEGORY_MAPPING:
        return CATEGORY_MAPPING[normalized]

    # Check partial matches
    for key, value in CATEGORY_MAPPING.items():
        if key in normalized or normalized in key:
            return value

    return "other"


def generate_deal_id(merchant: str, title: str, source: str) -> str:
    """Generate a unique deal ID based on content"""
    content = f"{merchant}:{title}:{source}"
    return hashlib.md5(content.encode()).hexdigest()[:12]


def parse_daisycon_feed(xml_content: str) -> List[Deal]:
    """
    Parse Daisycon XML feed format.

    Expected structure:
    <products>
        <product>
            <name>Product Name</name>
            <price>29.99</price>
            <price_old>49.99</price_old>
            <link>https://tracking.daisycon.com/...</link>
            <category>Electronics</category>
            <merchant_name>Store</merchant_name>
            <merchant_logo>https://...</merchant_logo>
            <image_url>https://...</image_url>
            <coupon_code>SAVE20</coupon_code>
            <valid_until>2025-02-01</valid_until>
        </product>
    </products>
    """
    deals = []

    try:
        root = ET.fromstring(xml_content)

        for product in root.findall('.//product'):
            try:
                name = product.findtext('name', '')
                if not name:
                    continue

                price_str = product.findtext('price', '0')
                price_old_str = product.findtext('price_old', price_str)

                # Parse prices
                sale_price = float(price_str.replace(',', '.').replace('€', '').strip())
                original_price = float(price_old_str.replace(',', '.').replace('€', '').strip())

                # Skip if no discount
                if original_price <= sale_price:
                    original_price = sale_price * 1.2  # Assume 20% discount if not specified

                discount = int(((original_price - sale_price) / original_price) * 100)

                merchant = product.findtext('merchant_name', 'Onbekend')

                # Parse valid until date
                valid_until_str = product.findtext('valid_until', '')
                if valid_until_str:
                    try:
                        valid_until = datetime.strptime(valid_until_str, '%Y-%m-%d')
                    except ValueError:
                        valid_until = datetime.now() + timedelta(days=30)
                else:
                    valid_until = datetime.now() + timedelta(days=30)

                deal = Deal(
                    id=generate_deal_id(merchant, name, 'daisycon'),
                    title=name,
                    description=product.findtext('description', ''),
                    merchant=merchant,
                    merchant_logo=product.findtext('merchant_logo', f'https://logo.clearbit.com/{merchant.lower().replace(" ", "")}.nl'),
                    original_price=original_price,
                    sale_price=sale_price,
                    discount_percentage=discount,
                    coupon_code=product.findtext('coupon_code'),
                    affiliate_url=product.findtext('link', ''),
                    category=map_category(product.findtext('category', '')),
                    image_url=product.findtext('image_url', ''),
                    valid_from=datetime.now(),
                    valid_until=valid_until,
                    source='daisycon',
                    created_at=datetime.now(),
                    is_active=True,
                )

                deals.append(deal)

            except Exception as e:
                print(f"Error parsing product: {e}")
                continue

    except ET.ParseError as e:
        print(f"XML Parse error: {e}")

    return deals


def parse_tradetracker_feed(xml_content: str) -> List[Deal]:
    """
    Parse TradeTracker XML feed format.

    Similar structure to Daisycon but with different element names.
    """
    deals = []

    try:
        root = ET.fromstring(xml_content)

        for product in root.findall('.//product'):
            try:
                name = product.findtext('title', '') or product.findtext('name', '')
                if not name:
                    continue

                price_str = product.findtext('price', '0')
                price_old_str = product.findtext('fromPrice', product.findtext('price_old', price_str))

                sale_price = float(price_str.replace(',', '.').replace('€', '').strip())
                original_price = float(price_old_str.replace(',', '.').replace('€', '').strip())

                if original_price <= sale_price:
                    original_price = sale_price * 1.2

                discount = int(((original_price - sale_price) / original_price) * 100)

                merchant = product.findtext('programName', product.findtext('merchant', 'Onbekend'))

                valid_until_str = product.findtext('validTo', product.findtext('valid_until', ''))
                if valid_until_str:
                    try:
                        valid_until = datetime.strptime(valid_until_str[:10], '%Y-%m-%d')
                    except ValueError:
                        valid_until = datetime.now() + timedelta(days=30)
                else:
                    valid_until = datetime.now() + timedelta(days=30)

                deal = Deal(
                    id=generate_deal_id(merchant, name, 'tradetracker'),
                    title=name,
                    description=product.findtext('description', ''),
                    merchant=merchant,
                    merchant_logo=product.findtext('programLogo', f'https://logo.clearbit.com/{merchant.lower().replace(" ", "")}.nl'),
                    original_price=original_price,
                    sale_price=sale_price,
                    discount_percentage=discount,
                    coupon_code=product.findtext('code', product.findtext('coupon_code')),
                    affiliate_url=product.findtext('productURL', product.findtext('link', '')),
                    category=map_category(product.findtext('category', '')),
                    image_url=product.findtext('imageURL', product.findtext('image_url', '')),
                    valid_from=datetime.now(),
                    valid_until=valid_until,
                    source='tradetracker',
                    created_at=datetime.now(),
                    is_active=True,
                )

                deals.append(deal)

            except Exception as e:
                print(f"Error parsing TradeTracker product: {e}")
                continue

    except ET.ParseError as e:
        print(f"TradeTracker XML Parse error: {e}")

    return deals


def fetch_feed(url: str, cache_hours: int = 1) -> Optional[str]:
    """
    Fetch XML feed from URL with caching.

    Args:
        url: The feed URL
        cache_hours: How long to cache the feed (in hours)

    Returns:
        XML content as string, or None if failed
    """
    # Create cache filename from URL
    cache_key = hashlib.md5(url.encode()).hexdigest()
    cache_file = FEEDS_DIR / f"{cache_key}.xml"

    # Check cache
    if cache_file.exists():
        cache_age = datetime.now().timestamp() - cache_file.stat().st_mtime
        if cache_age < (cache_hours * 3600):
            return cache_file.read_text(encoding='utf-8')

    # Fetch fresh content
    try:
        headers = {
            'User-Agent': 'kort.ing/1.0 (Dutch Deal Aggregator)'
        }
        request = Request(url, headers=headers)
        with urlopen(request, timeout=30) as response:
            content = response.read().decode('utf-8')

        # Save to cache
        cache_file.write_text(content, encoding='utf-8')

        return content

    except URLError as e:
        print(f"Error fetching feed {url}: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error fetching feed: {e}")
        return None


def update_deals_from_feeds(feed_urls: Dict[str, str]) -> int:
    """
    Update deals database from multiple feed URLs.

    Args:
        feed_urls: Dict mapping source name to feed URL

    Returns:
        Number of deals added/updated
    """
    total_deals = 0

    for source, url in feed_urls.items():
        print(f"Fetching {source} feed...")
        content = fetch_feed(url)

        if not content:
            print(f"  Failed to fetch {source}")
            continue

        # Parse based on source
        if source == 'daisycon':
            deals = parse_daisycon_feed(content)
        elif source == 'tradetracker':
            deals = parse_tradetracker_feed(content)
        else:
            # Try generic parsing
            deals = parse_daisycon_feed(content)

        print(f"  Found {len(deals)} deals")

        # Insert deals
        for deal in deals:
            if insert_deal(deal):
                total_deals += 1

    print(f"Total deals updated: {total_deals}")
    return total_deals


# Example feed URLs (replace with real URLs after affiliate approval)
EXAMPLE_FEED_URLS = {
    # "daisycon": f"https://datafeed.daisycon.com/feeds/{DAISYCON_PUBLISHER_ID}/products.xml",
    # "tradetracker": f"https://pf.tradetracker.net/feed/{TRADETRACKER_ID}/products.xml",
}
