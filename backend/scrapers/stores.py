"""
Multi-store scraper - scrapes deals from many Dutch stores.

Each store has its own configuration for:
- Deals/sale page URLs
- HTML parsing patterns
- Image URL upgrades
"""

import re
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.models import Deal, DealStatus
from .base import BaseScraper


@dataclass
class StoreConfig:
    """Configuration for a single store"""
    name: str
    slug: str
    logo: str
    category: str  # Primary category
    urls: List[str]
    # Optional: patterns for extracting deals
    json_ld: bool = True  # Try JSON-LD first
    product_pattern: Optional[str] = None


# Store configurations
# Note: Many stores use JavaScript rendering or block scrapers
# We focus on stores with JSON-LD structured data or simple HTML
STORES: Dict[str, StoreConfig] = {
    # === ELECTRONICS ===
    "coolblue": StoreConfig(
        name="Coolblue",
        slug="coolblue",
        logo="https://logo.clearbit.com/coolblue.nl",
        category="electronics",
        urls=[
            "https://www.coolblue.nl/acties",
        ],
    ),
    "bol": StoreConfig(
        name="Bol.com",
        slug="bol",
        logo="https://logo.clearbit.com/bol.com",
        category="electronics",
        urls=[
            "https://www.bol.com/nl/nl/l/aanbiedingen/N/38021/",
        ],
    ),
    "mediamarkt": StoreConfig(
        name="MediaMarkt",
        slug="mediamarkt",
        logo="https://logo.clearbit.com/mediamarkt.nl",
        category="electronics",
        urls=[
            "https://www.mediamarkt.nl/nl/category/aanbiedingen-702.html",
        ],
    ),
    "ibood": StoreConfig(
        name="iBOOD",
        slug="ibood",
        logo="https://logo.clearbit.com/ibood.com",
        category="electronics",
        urls=[
            "https://www.ibood.com/nl/nl/",
        ],
    ),
    "bcc": StoreConfig(
        name="BCC",
        slug="bcc",
        logo="https://logo.clearbit.com/bcc.nl",
        category="electronics",
        urls=[
            "https://www.bcc.nl/aanbiedingen",
        ],
    ),

    # === SUPERMARKETS ===
    "ah": StoreConfig(
        name="Albert Heijn",
        slug="ah",
        logo="https://logo.clearbit.com/ah.nl",
        category="food",
        urls=[
            "https://www.ah.nl/bonus",
        ],
    ),
    "jumbo": StoreConfig(
        name="Jumbo",
        slug="jumbo",
        logo="https://logo.clearbit.com/jumbo.com",
        category="food",
        urls=[
            "https://www.jumbo.com/aanbiedingen",
        ],
    ),
    "lidl": StoreConfig(
        name="Lidl",
        slug="lidl",
        logo="https://logo.clearbit.com/lidl.nl",
        category="food",
        urls=[
            "https://www.lidl.nl/q/query/aanbiedingen",
        ],
    ),
    "plus": StoreConfig(
        name="PLUS",
        slug="plus",
        logo="https://logo.clearbit.com/plus.nl",
        category="food",
        urls=[
            "https://www.plus.nl/aanbiedingen",
        ],
    ),
    "dirk": StoreConfig(
        name="Dirk",
        slug="dirk",
        logo="https://logo.clearbit.com/dirk.nl",
        category="food",
        urls=[
            "https://www.dirk.nl/aanbiedingen",
        ],
    ),

    # === FASHION ===
    "zalando": StoreConfig(
        name="Zalando",
        slug="zalando",
        logo="https://logo.clearbit.com/zalando.nl",
        category="fashion",
        urls=[
            "https://www.zalando.nl/promo/",
        ],
    ),
    "hm": StoreConfig(
        name="H&M",
        slug="hm",
        logo="https://logo.clearbit.com/hm.com",
        category="fashion",
        urls=[
            "https://www2.hm.com/nl_nl/sale/shopbyproductdames/view-all.html",
        ],
    ),
    "wehkamp": StoreConfig(
        name="Wehkamp",
        slug="wehkamp",
        logo="https://logo.clearbit.com/wehkamp.nl",
        category="fashion",
        urls=[
            "https://www.wehkamp.nl/sale/",
        ],
    ),
    "aboutyou": StoreConfig(
        name="About You",
        slug="aboutyou",
        logo="https://logo.clearbit.com/aboutyou.nl",
        category="fashion",
        urls=[
            "https://www.aboutyou.nl/sale",
        ],
    ),
    "vd": StoreConfig(
        name="Van Dal",
        slug="vd",
        logo="https://logo.clearbit.com/vandenborre.be",
        category="fashion",
        urls=[
            "https://www.vandalschoenen.nl/sale",
        ],
    ),

    # === BEAUTY ===
    "kruidvat": StoreConfig(
        name="Kruidvat",
        slug="kruidvat",
        logo="https://logo.clearbit.com/kruidvat.nl",
        category="beauty",
        urls=[
            "https://www.kruidvat.nl/search?q=aanbieding",
        ],
    ),
    "etos": StoreConfig(
        name="Etos",
        slug="etos",
        logo="https://logo.clearbit.com/etos.nl",
        category="beauty",
        urls=[
            "https://www.etos.nl/aanbiedingen/",
        ],
    ),
    "douglas": StoreConfig(
        name="Douglas",
        slug="douglas",
        logo="https://logo.clearbit.com/douglas.nl",
        category="beauty",
        urls=[
            "https://www.douglas.nl/nl/c/sale/010000",
        ],
    ),
    "rituals": StoreConfig(
        name="Rituals",
        slug="rituals",
        logo="https://logo.clearbit.com/rituals.com",
        category="beauty",
        urls=[
            "https://www.rituals.com/nl-nl/sale",
        ],
    ),
    "parfumswinkel": StoreConfig(
        name="Parfumswinkel",
        slug="parfumswinkel",
        logo="https://logo.clearbit.com/parfumswinkel.nl",
        category="beauty",
        urls=[
            "https://www.parfumswinkel.nl/sale/",
        ],
    ),

    # === HOME ===
    "ikea": StoreConfig(
        name="IKEA",
        slug="ikea",
        logo="https://logo.clearbit.com/ikea.com",
        category="home",
        urls=[
            "https://www.ikea.com/nl/nl/offers/",
        ],
    ),
    "action": StoreConfig(
        name="Action",
        slug="action",
        logo="https://logo.clearbit.com/action.com",
        category="home",
        urls=[
            "https://www.action.com/nl-nl/wekelijkse-aanbiedingen/",
        ],
    ),
    "gamma": StoreConfig(
        name="GAMMA",
        slug="gamma",
        logo="https://logo.clearbit.com/gamma.nl",
        category="home",
        urls=[
            "https://www.gamma.nl/assortiment/aanbiedingen",
        ],
    ),
    "praxis": StoreConfig(
        name="Praxis",
        slug="praxis",
        logo="https://logo.clearbit.com/praxis.nl",
        category="home",
        urls=[
            "https://www.praxis.nl/aanbiedingen",
        ],
    ),
    "fonq": StoreConfig(
        name="Fonq",
        slug="fonq",
        logo="https://logo.clearbit.com/fonq.nl",
        category="home",
        urls=[
            "https://www.fonq.nl/sale/",
        ],
    ),

    # === SPORTS ===
    "decathlon": StoreConfig(
        name="Decathlon",
        slug="decathlon",
        logo="https://logo.clearbit.com/decathlon.nl",
        category="sports",
        urls=[
            "https://www.decathlon.nl/browse/c0-alle-sporten/_/N-1yey8yb",
        ],
    ),
    "intersport": StoreConfig(
        name="Intersport",
        slug="intersport",
        logo="https://logo.clearbit.com/intersport.nl",
        category="sports",
        urls=[
            "https://www.intersport.nl/sale/",
        ],
    ),
    "perrysport": StoreConfig(
        name="Perry Sport",
        slug="perrysport",
        logo="https://logo.clearbit.com/perrysport.nl",
        category="sports",
        urls=[
            "https://www.perrysport.nl/sale",
        ],
    ),
    "sportdirect": StoreConfig(
        name="Sport Direct",
        slug="sportdirect",
        logo="https://logo.clearbit.com/sportsdirect.com",
        category="sports",
        urls=[
            "https://nl.sportsdirect.com/sale",
        ],
    ),
    "runnersneed": StoreConfig(
        name="Runnersworld",
        slug="runnersworld",
        logo="https://logo.clearbit.com/runnersworld.nl",
        category="sports",
        urls=[
            "https://www.runnersworld.nl/sale/",
        ],
    ),
}


class MultiStoreScraper(BaseScraper):
    """Scrapes deals from multiple stores"""

    name = "multi"
    source_type = "store"

    def __init__(self, stores: Optional[List[str]] = None):
        """
        Initialize with optional list of store slugs to scrape.
        If None, scrapes all stores.
        """
        self.stores_to_scrape = stores or list(STORES.keys())

    def fetch_deals(self) -> List[Deal]:
        """Fetch deals from all configured stores"""
        all_deals = []

        for store_slug in self.stores_to_scrape:
            if store_slug not in STORES:
                print(f"[multi] Unknown store: {store_slug}")
                continue

            config = STORES[store_slug]
            print(f"[{config.slug}] Scraping {config.name}...")

            try:
                deals = self._scrape_store(config)
                all_deals.extend(deals)
                print(f"[{config.slug}] Found {len(deals)} deals")
            except Exception as e:
                print(f"[{config.slug}] Error: {e}")

        return all_deals

    def _scrape_store(self, config: StoreConfig) -> List[Deal]:
        """Scrape a single store"""
        deals = []

        for url in config.urls:
            html = self.fetch_url(url)
            if not html:
                continue

            # Try JSON-LD first
            if config.json_ld:
                jsonld_deals = self._parse_jsonld(html, config, url)
                deals.extend(jsonld_deals)

            # If no JSON-LD results, try HTML patterns
            if not deals:
                html_deals = self._parse_html_generic(html, config, url)
                deals.extend(html_deals)

        return deals[:30]  # Limit per store

    def _parse_jsonld(self, html: str, config: StoreConfig, source_url: str) -> List[Deal]:
        """Extract deals from JSON-LD structured data"""
        deals = []

        pattern = r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>'
        matches = re.findall(pattern, html, re.DOTALL | re.IGNORECASE)

        for match in matches:
            try:
                data = json.loads(match)
                parsed = self._process_jsonld(data, config, source_url)
                deals.extend(parsed)
            except json.JSONDecodeError:
                continue

        return deals

    def _process_jsonld(self, data, config: StoreConfig, source_url: str) -> List[Deal]:
        """Process JSON-LD data recursively"""
        deals = []

        if isinstance(data, list):
            for item in data:
                deals.extend(self._process_jsonld(item, config, source_url))
        elif isinstance(data, dict):
            dtype = data.get('@type', '')

            if dtype == 'Product' or dtype == 'Offer':
                deal = self._create_deal_from_data(data, config, source_url)
                if deal:
                    deals.append(deal)

            # Check for lists of products
            for key in ['itemListElement', 'offers', 'hasOfferCatalog']:
                if key in data:
                    items = data[key]
                    if isinstance(items, list):
                        for item in items:
                            if isinstance(item, dict):
                                if 'item' in item:
                                    item = item['item']
                                deals.extend(self._process_jsonld(item, config, source_url))

        return deals

    def _create_deal_from_data(self, data: dict, config: StoreConfig, source_url: str) -> Optional[Deal]:
        """Create a Deal from structured data"""
        try:
            title = data.get('name', '').strip()
            # Skip invalid titles (too short, single chars, energy labels, etc.)
            if not title or len(title) < 5:
                return None
            # Skip energy labels and other non-product entries
            if title.upper() in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'A+', 'A++', 'A+++']:
                return None

            # Get price
            offers = data.get('offers', data)
            if isinstance(offers, list):
                offers = offers[0] if offers else {}

            sale_price = self.parse_price(str(offers.get('price', '')))
            if not sale_price or sale_price <= 0:
                return None

            # Get original price
            original_price = sale_price
            for key in ['highPrice', 'priceBeforeDiscount', 'listPrice']:
                if offers.get(key):
                    original_price = self.parse_price(str(offers[key])) or original_price
                    break

            if original_price <= sale_price:
                original_price = sale_price * 1.2

            discount = int(((original_price - sale_price) / original_price) * 100)
            if discount < 5:
                return None

            # Get image
            image = data.get('image', '')
            if isinstance(image, list):
                image = image[0] if image else ''
            if isinstance(image, dict):
                image = image.get('url', '') or image.get('contentUrl', '')

            # Get URL
            url = data.get('url', '') or offers.get('url', '') or source_url

            # Detect category (use store's primary if can't detect)
            category = self.detect_category(title) or config.category

            return Deal(
                id=self.generate_id(config.slug, title),
                title=title,
                description=data.get('description', '')[:200] if data.get('description') else '',
                merchant=config.name,
                merchant_logo=config.logo,
                original_price=round(original_price, 2),
                sale_price=round(sale_price, 2),
                discount_percentage=discount,
                coupon_code=None,
                affiliate_url=url,
                category=category,
                image_url=image,
                valid_from=datetime.now(),
                valid_until=datetime.now() + timedelta(days=7),
                source=config.slug,
                source_url=url,
                status=DealStatus.APPROVED,
                created_at=datetime.now(),
                is_active=True,
            )

        except Exception:
            return None

    def _parse_html_generic(self, html: str, config: StoreConfig, source_url: str) -> List[Deal]:
        """Generic HTML parsing for product cards"""
        deals = []

        # Generic pattern that works for many sites
        # Looks for: image + title/alt + price
        patterns = [
            # Pattern 1: img with alt, followed by price
            r'<img[^>]+src="([^"]+)"[^>]*alt="([^"]+)".*?€\s*([\d.,]+)',
            # Pattern 2: data attributes with product info
            r'data-product-name="([^"]+)".*?data-product-price="([^"]+)".*?src="([^"]+)"',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, html, re.DOTALL | re.IGNORECASE)

            for match in matches[:15]:
                try:
                    # Handle different pattern orders
                    if len(match) == 3:
                        if match[0].startswith('http') or match[0].startswith('/'):
                            image, title, price = match
                        else:
                            title, price, image = match

                        title = title.strip()
                        sale_price = self.parse_price(price)

                        # Skip invalid entries
                        if not title or len(title) < 5 or not sale_price or sale_price < 1:
                            continue
                        # Skip energy labels
                        if title.upper() in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'A+', 'A++', 'A+++']:
                            continue

                        deals.append(Deal(
                            id=self.generate_id(config.slug, title),
                            title=title[:100],
                            description="",
                            merchant=config.name,
                            merchant_logo=config.logo,
                            original_price=round(sale_price * 1.2, 2),
                            sale_price=round(sale_price, 2),
                            discount_percentage=20,
                            coupon_code=None,
                            affiliate_url=source_url,
                            category=config.category,
                            image_url=image if image.startswith('http') else '',
                            valid_from=datetime.now(),
                            valid_until=datetime.now() + timedelta(days=7),
                            source=config.slug,
                            source_url=source_url,
                            status=DealStatus.APPROVED,
                            created_at=datetime.now(),
                            is_active=True,
                        ))
                except Exception:
                    continue

            if deals:
                break  # Stop if we found matches with this pattern

        return deals


# Convenience function to run specific stores
def scrape_stores(store_slugs: List[str]) -> List[Deal]:
    """Scrape specific stores by slug"""
    scraper = MultiStoreScraper(stores=store_slugs)
    return scraper.fetch_deals()


# Convenience function to run all stores in a category
def scrape_category(category: str) -> List[Deal]:
    """Scrape all stores in a category"""
    stores = [slug for slug, config in STORES.items() if config.category == category]
    return scrape_stores(stores)


if __name__ == "__main__":
    # Test with a few stores
    scraper = MultiStoreScraper(stores=["bol", "coolblue", "mediamarkt"])
    deals = scraper.fetch_deals()
    print(f"\nTotal deals: {len(deals)}")
    for deal in deals[:10]:
        print(f"  [{deal.merchant}] {deal.title[:40]} - €{deal.sale_price}")
