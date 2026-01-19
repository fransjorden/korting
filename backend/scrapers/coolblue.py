"""
Coolblue direct scraper.

Scrapes deals directly from Coolblue's promotions pages.
"""

import re
import json
from datetime import datetime, timedelta
from typing import List, Optional

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.models import Deal, DealStatus
from .base import BaseScraper


class CoolblueScraper(BaseScraper):
    """Scraper for Coolblue deals"""

    name = "coolblue"
    source_type = "coolblue"
    merchant = "Coolblue"
    merchant_logo = "https://logo.clearbit.com/coolblue.nl"

    PAGES = [
        "https://www.coolblue.nl/acties",
        "https://www.coolblue.nl/outlet",
    ]

    def fetch_deals(self) -> List[Deal]:
        """Fetch deals from Coolblue"""
        deals = []

        for url in self.PAGES:
            print(f"[{self.name}] Fetching {url}...")
            html = self.fetch_url(url)
            if html:
                page_deals = self._parse_page(html, url)
                deals.extend(page_deals)
                print(f"[{self.name}] Found {len(page_deals)} deals")

        return deals

    def _parse_page(self, html: str, source_url: str) -> List[Deal]:
        """Parse Coolblue deals page"""
        deals = []

        # Look for JSON-LD data
        jsonld_pattern = r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>'
        matches = re.findall(jsonld_pattern, html, re.DOTALL | re.IGNORECASE)

        for match in matches:
            try:
                data = json.loads(match)
                if isinstance(data, dict) and data.get('@type') == 'Product':
                    deal = self._create_deal(data, source_url)
                    if deal:
                        deals.append(deal)
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and item.get('@type') == 'Product':
                            deal = self._create_deal(item, source_url)
                            if deal:
                                deals.append(deal)
            except json.JSONDecodeError:
                continue

        # Fallback: parse HTML patterns
        if not deals:
            deals = self._parse_html(html, source_url)

        return deals[:30]

    def _create_deal(self, data: dict, source_url: str) -> Optional[Deal]:
        """Create deal from JSON-LD data"""
        try:
            title = data.get('name', '').strip()
            if not title:
                return None

            offers = data.get('offers', {})
            if isinstance(offers, list):
                offers = offers[0] if offers else {}

            sale_price = self.parse_price(str(offers.get('price', '')))
            if not sale_price:
                return None

            # Try to get original price
            original_price = sale_price * 1.2
            discount = 20

            image = data.get('image', '')
            if isinstance(image, list):
                image = image[0] if image else ''

            url = data.get('url', '') or offers.get('url', '') or source_url

            return Deal(
                id=self.generate_id(self.name, title),
                title=title,
                description=data.get('description', '')[:300] if data.get('description') else '',
                merchant=self.merchant,
                merchant_logo=self.merchant_logo,
                original_price=round(original_price, 2),
                sale_price=round(sale_price, 2),
                discount_percentage=discount,
                coupon_code=None,
                affiliate_url=url,
                category=self.detect_category(title),
                image_url=image,
                valid_from=datetime.now(),
                valid_until=datetime.now() + timedelta(days=7),
                source=self.source_type,
                source_url=url,
                status=DealStatus.APPROVED,
                created_at=datetime.now(),
                is_active=True,
            )
        except Exception:
            return None

    def _parse_html(self, html: str, source_url: str) -> List[Deal]:
        """Fallback HTML parsing"""
        deals = []

        # Look for product cards
        # Coolblue uses specific class patterns
        product_pattern = r'href="(/[^"]+)"[^>]*>.*?<img[^>]+src="([^"]+)"[^>]*alt="([^"]+)".*?€\s*([\d.,]+)'
        matches = re.findall(product_pattern, html, re.DOTALL | re.IGNORECASE)

        for href, image, title, price in matches[:20]:
            try:
                title = title.strip()
                sale_price = self.parse_price(price)

                if not title or not sale_price or sale_price < 1:
                    continue

                url = f"https://www.coolblue.nl{href}" if href.startswith('/') else href

                deals.append(Deal(
                    id=self.generate_id(self.name, title),
                    title=title,
                    description="",
                    merchant=self.merchant,
                    merchant_logo=self.merchant_logo,
                    original_price=round(sale_price * 1.2, 2),
                    sale_price=round(sale_price, 2),
                    discount_percentage=20,
                    coupon_code=None,
                    affiliate_url=url,
                    category=self.detect_category(title),
                    image_url=image,
                    valid_from=datetime.now(),
                    valid_until=datetime.now() + timedelta(days=7),
                    source=self.source_type,
                    source_url=url,
                    status=DealStatus.APPROVED,
                    created_at=datetime.now(),
                    is_active=True,
                ))
            except Exception:
                continue

        return deals


if __name__ == "__main__":
    scraper = CoolblueScraper()
    deals = scraper.fetch_deals()
    print(f"Total: {len(deals)}")
