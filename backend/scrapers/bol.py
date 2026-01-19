"""
Bol.com direct scraper.

Scrapes deals directly from Bol.com's deals pages.
"""

import re
import json
from datetime import datetime, timedelta
from typing import List, Optional
from urllib.request import urlopen, Request
from urllib.error import URLError

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.models import Deal, DealStatus
from .base import BaseScraper


class BolScraper(BaseScraper):
    """Scraper for Bol.com deals"""

    name = "bol"
    source_type = "bol"
    merchant = "Bol.com"
    merchant_logo = "https://logo.clearbit.com/bol.com"

    # Bol.com deals pages
    PAGES = [
        "https://www.bol.com/nl/nl/m/aanbiedingen/",
        "https://www.bol.com/nl/nl/m/deals-van-de-dag/",
    ]

    def fetch_deals(self) -> List[Deal]:
        """Fetch deals from Bol.com"""
        deals = []

        for url in self.PAGES:
            print(f"[{self.name}] Fetching {url}...")
            html = self.fetch_url(url)
            if html:
                page_deals = self._parse_page(html, url)
                deals.extend(page_deals)
                print(f"[{self.name}] Found {len(page_deals)} deals from this page")

        return deals

    def _parse_page(self, html: str, source_url: str) -> List[Deal]:
        """Parse deals from Bol.com HTML"""
        deals = []

        # Try to find product data in script tags (JSON)
        # Bol.com often embeds product data as JSON
        script_pattern = r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>'
        matches = re.findall(script_pattern, html, re.DOTALL | re.IGNORECASE)

        for match in matches:
            try:
                data = json.loads(match)
                parsed = self._parse_jsonld(data, source_url)
                deals.extend(parsed)
            except json.JSONDecodeError:
                continue

        # Also try to extract from HTML patterns
        html_deals = self._parse_html_products(html, source_url)

        # Deduplicate by title
        seen_titles = {d.title for d in deals}
        for deal in html_deals:
            if deal.title not in seen_titles:
                deals.append(deal)
                seen_titles.add(deal.title)

        return deals[:30]  # Limit per page

    def _parse_jsonld(self, data, source_url: str) -> List[Deal]:
        """Parse JSON-LD structured data"""
        deals = []

        if isinstance(data, list):
            for item in data:
                deals.extend(self._parse_jsonld(item, source_url))
        elif isinstance(data, dict):
            if data.get('@type') == 'Product':
                deal = self._create_deal_from_jsonld(data, source_url)
                if deal:
                    deals.append(deal)
            elif 'itemListElement' in data:
                for item in data.get('itemListElement', []):
                    if isinstance(item, dict) and 'item' in item:
                        deal = self._create_deal_from_jsonld(item['item'], source_url)
                        if deal:
                            deals.append(deal)

        return deals

    def _create_deal_from_jsonld(self, data: dict, source_url: str) -> Optional[Deal]:
        """Create a Deal from JSON-LD product data"""
        try:
            title = data.get('name', '').strip()
            if not title or len(title) < 5:
                return None

            offers = data.get('offers', {})
            if isinstance(offers, list):
                offers = offers[0] if offers else {}

            price_str = str(offers.get('price', ''))
            sale_price = self.parse_price(price_str)
            if not sale_price or sale_price <= 0:
                return None

            # Get original price if available
            original_price = sale_price
            high_price = offers.get('highPrice')
            if high_price:
                original_price = self.parse_price(str(high_price))

            # If no discount info, estimate or skip
            if original_price <= sale_price:
                original_price = sale_price * 1.25  # Assume ~20% off

            discount = int(((original_price - sale_price) / original_price) * 100)
            if discount < 5:
                return None  # Skip tiny discounts

            # Get image - prefer high quality
            image = data.get('image', '')
            if isinstance(image, list):
                image = image[0] if image else ''
            if isinstance(image, dict):
                image = image.get('url', '')
            # Try to get higher resolution
            image = self._upgrade_image_url(image)

            # Get product URL
            url = offers.get('url', '') or data.get('url', '')
            if not url:
                url = source_url

            deal_id = self.generate_id(self.name, title)

            return Deal(
                id=deal_id,
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
        except Exception as e:
            return None

    def _parse_html_products(self, html: str, source_url: str) -> List[Deal]:
        """Parse products from HTML structure"""
        deals = []

        # Pattern to find product cards with data attributes
        # This is a simplified extraction - adjust based on actual HTML
        product_pattern = r'data-product-id="(\d+)"[^>]*>.*?<img[^>]+src="([^"]+)".*?class="[^"]*product-title[^"]*"[^>]*>([^<]+)<.*?class="[^"]*promo-price[^"]*"[^>]*>.*?€\s*([\d,]+)'

        matches = re.findall(product_pattern, html, re.DOTALL | re.IGNORECASE)

        for product_id, image, title, price in matches[:20]:
            try:
                title = title.strip()
                sale_price = self.parse_price(price)

                if not title or not sale_price:
                    continue

                original_price = sale_price * 1.25
                discount = 20

                image = self._upgrade_image_url(image)
                url = f"https://www.bol.com/nl/nl/p/-/{product_id}/"

                deal_id = self.generate_id(self.name, title)

                deal = Deal(
                    id=deal_id,
                    title=title,
                    description="",
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
                deals.append(deal)
            except Exception:
                continue

        return deals

    def _upgrade_image_url(self, url: str) -> str:
        """Try to get higher resolution image"""
        if not url:
            return ""
        # Bol.com image URLs often have size parameters
        # Try to upgrade to larger size
        url = re.sub(r'/\d+x\d+/', '/550x550/', url)
        url = re.sub(r'_\d+x\d+\.', '_550x550.', url)
        return url


if __name__ == "__main__":
    scraper = BolScraper()
    deals = scraper.fetch_deals()
    print(f"Total deals: {len(deals)}")
    for deal in deals[:5]:
        print(f"  - {deal.title[:50]} | €{deal.sale_price} | {deal.image_url[:50]}")
