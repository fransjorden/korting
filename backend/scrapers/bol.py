"""
Bol.com deals scraper.

Scrapes the Bol.com daily deals and promotions pages.
Note: This is a basic scraper. Bol.com may change their HTML structure.
"""

import re
import json
from datetime import datetime, timedelta
from typing import List, Optional
from html.parser import HTMLParser

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.models import Deal, DealStatus
from .base import BaseScraper


class BolScraper(BaseScraper):
    """Scraper for Bol.com deals"""

    name = "bol"
    source_type = "bol"

    # Bol.com deal pages
    URLS = {
        "deals": "https://www.bol.com/nl/nl/m/aanbiedingen/",
        "dagdeal": "https://www.bol.com/nl/nl/m/deals-van-de-dag/",
    }

    def fetch_deals(self) -> List[Deal]:
        """Fetch deals from Bol.com pages"""
        deals = []

        for page_name, url in self.URLS.items():
            print(f"[{self.name}] Fetching {page_name}...")
            page_deals = self._scrape_page(url, page_name)
            deals.extend(page_deals)

        return deals

    def _scrape_page(self, url: str, page_type: str) -> List[Deal]:
        """Scrape a single Bol.com page"""
        deals = []

        html = self.fetch_url(url)
        if not html:
            print(f"[{self.name}] Failed to fetch {url}")
            return deals

        # Try to find product data in JSON-LD or script tags
        deals = self._extract_from_jsonld(html, url)

        if not deals:
            # Fallback: try to extract from HTML
            deals = self._extract_from_html(html, url)

        return deals

    def _extract_from_jsonld(self, html: str, source_url: str) -> List[Deal]:
        """Extract deals from JSON-LD structured data"""
        deals = []

        # Find JSON-LD scripts
        jsonld_pattern = r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>'
        matches = re.findall(jsonld_pattern, html, re.DOTALL | re.IGNORECASE)

        for match in matches:
            try:
                data = json.loads(match)
                if isinstance(data, list):
                    for item in data:
                        deal = self._parse_jsonld_product(item, source_url)
                        if deal:
                            deals.append(deal)
                elif isinstance(data, dict):
                    if data.get('@type') == 'Product':
                        deal = self._parse_jsonld_product(data, source_url)
                        if deal:
                            deals.append(deal)
                    elif 'itemListElement' in data:
                        for item in data['itemListElement']:
                            if 'item' in item:
                                deal = self._parse_jsonld_product(item['item'], source_url)
                                if deal:
                                    deals.append(deal)
            except json.JSONDecodeError:
                continue

        return deals

    def _parse_jsonld_product(self, data: dict, source_url: str) -> Optional[Deal]:
        """Parse a JSON-LD product into a Deal"""
        try:
            if data.get('@type') != 'Product':
                return None

            title = data.get('name', '')
            if not title:
                return None

            # Get prices from offers
            offers = data.get('offers', {})
            if isinstance(offers, list):
                offers = offers[0] if offers else {}

            sale_price = self.parse_price(str(offers.get('price', '')))
            if not sale_price:
                return None

            # Bol.com doesn't always have original price in JSON-LD
            # Estimate 20% discount as placeholder
            original_price = sale_price * 1.25
            discount = 20

            # Get image
            image = data.get('image', '')
            if isinstance(image, list):
                image = image[0] if image else ''

            # Get URL
            url = offers.get('url', '') or data.get('url', '') or source_url

            deal_id = self.generate_id(self.name, title, str(sale_price))

            return Deal(
                id=deal_id,
                title=title,
                description=data.get('description', '')[:500],
                merchant="Bol.com",
                merchant_logo=self.get_merchant_logo("bol.com"),
                original_price=original_price,
                sale_price=sale_price,
                discount_percentage=discount,
                coupon_code=None,
                affiliate_url=url,
                category=self.detect_category(title),
                image_url=image,
                valid_from=datetime.now(),
                valid_until=datetime.now() + timedelta(days=3),
                source=self.source_type,
                source_url=source_url,
                status=DealStatus.PENDING,
                created_at=datetime.now(),
                is_active=True,
            )

        except Exception as e:
            print(f"[{self.name}] Error parsing JSON-LD: {e}")
            return None

    def _extract_from_html(self, html: str, source_url: str) -> List[Deal]:
        """Fallback: extract deals from HTML patterns"""
        deals = []

        # Look for product cards with price patterns
        # This is a simplified extraction - Bol.com's actual HTML varies

        # Pattern for product titles and prices
        # Note: This is fragile and may break if Bol.com changes their HTML
        product_pattern = r'data-test="product-title"[^>]*>([^<]+)</.*?€\s*([\d.,]+)'

        matches = re.findall(product_pattern, html, re.DOTALL)

        for title, price_str in matches[:20]:  # Limit to 20 items
            try:
                title = title.strip()
                sale_price = self.parse_price(price_str)

                if not title or not sale_price:
                    continue

                original_price = sale_price * 1.25
                discount = 20

                deal_id = self.generate_id(self.name, title, str(sale_price))

                deal = Deal(
                    id=deal_id,
                    title=title,
                    description="",
                    merchant="Bol.com",
                    merchant_logo=self.get_merchant_logo("bol.com"),
                    original_price=original_price,
                    sale_price=sale_price,
                    discount_percentage=discount,
                    coupon_code=None,
                    affiliate_url=source_url,
                    category=self.detect_category(title),
                    image_url="",
                    valid_from=datetime.now(),
                    valid_until=datetime.now() + timedelta(days=3),
                    source=self.source_type,
                    source_url=source_url,
                    status=DealStatus.PENDING,
                    created_at=datetime.now(),
                    is_active=True,
                )
                deals.append(deal)

            except Exception as e:
                continue

        return deals


if __name__ == "__main__":
    # Test the scraper
    scraper = BolScraper()
    scraper.run()
