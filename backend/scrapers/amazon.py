"""
Amazon.nl direct scraper.

Scrapes deals from Amazon.nl deals page.
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


class AmazonScraper(BaseScraper):
    """Scraper for Amazon.nl deals"""

    name = "amazon"
    source_type = "amazon"
    merchant = "Amazon.nl"
    merchant_logo = "https://logo.clearbit.com/amazon.nl"

    PAGES = [
        "https://www.amazon.nl/gp/goldbox",
        "https://www.amazon.nl/deals",
    ]

    def fetch_deals(self) -> List[Deal]:
        """Fetch deals from Amazon.nl"""
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
        """Parse Amazon deals"""
        deals = []

        # Amazon embeds deal data in various formats
        # Try to find deal widgets

        # Pattern for deal cards
        deal_pattern = r'data-deal-id="([^"]+)".*?<img[^>]+src="([^"]+)".*?<span[^>]*class="[^"]*dealTitle[^"]*"[^>]*>([^<]+)</span>.*?€\s*([\d.,]+)'
        matches = re.findall(deal_pattern, html, re.DOTALL | re.IGNORECASE)

        for deal_id, image, title, price in matches[:30]:
            try:
                title = title.strip()
                sale_price = self.parse_price(price)

                if not title or not sale_price:
                    continue

                # Upgrade image quality
                image = self._upgrade_image(image)
                url = f"https://www.amazon.nl/dp/{deal_id}"

                deals.append(Deal(
                    id=self.generate_id(self.name, deal_id),
                    title=title,
                    description="",
                    merchant=self.merchant,
                    merchant_logo=self.merchant_logo,
                    original_price=round(sale_price * 1.25, 2),
                    sale_price=round(sale_price, 2),
                    discount_percentage=20,
                    coupon_code=None,
                    affiliate_url=url,
                    category=self.detect_category(title),
                    image_url=image,
                    valid_from=datetime.now(),
                    valid_until=datetime.now() + timedelta(days=3),
                    source=self.source_type,
                    source_url=url,
                    status=DealStatus.APPROVED,
                    created_at=datetime.now(),
                    is_active=True,
                ))
            except Exception:
                continue

        # Alternative pattern for product listings
        if not deals:
            deals = self._parse_product_grid(html, source_url)

        return deals

    def _parse_product_grid(self, html: str, source_url: str) -> List[Deal]:
        """Parse product grid layout"""
        deals = []

        # Find ASIN codes and basic info
        asin_pattern = r'data-asin="([A-Z0-9]{10})".*?<img[^>]+src="([^"]+)"[^>]*>.*?<span[^>]*class="[^"]*a-price-whole[^"]*"[^>]*>(\d+)</span>'
        matches = re.findall(asin_pattern, html, re.DOTALL | re.IGNORECASE)

        for asin, image, price_whole in matches[:20]:
            try:
                sale_price = float(price_whole)
                if sale_price < 1:
                    continue

                image = self._upgrade_image(image)
                url = f"https://www.amazon.nl/dp/{asin}"

                deals.append(Deal(
                    id=self.generate_id(self.name, asin),
                    title=f"Amazon Deal {asin}",  # Will need to fetch actual title
                    description="",
                    merchant=self.merchant,
                    merchant_logo=self.merchant_logo,
                    original_price=round(sale_price * 1.2, 2),
                    sale_price=round(sale_price, 2),
                    discount_percentage=20,
                    coupon_code=None,
                    affiliate_url=url,
                    category="other",
                    image_url=image,
                    valid_from=datetime.now(),
                    valid_until=datetime.now() + timedelta(days=3),
                    source=self.source_type,
                    source_url=url,
                    status=DealStatus.APPROVED,
                    created_at=datetime.now(),
                    is_active=True,
                ))
            except Exception:
                continue

        return deals

    def _upgrade_image(self, url: str) -> str:
        """Get higher resolution Amazon image"""
        if not url:
            return ""
        # Amazon images: replace size suffix for larger version
        # ._SX300_ -> ._SX500_ or remove entirely
        url = re.sub(r'\._[A-Z]{2}\d+_\.', '.', url)
        return url


if __name__ == "__main__":
    scraper = AmazonScraper()
    deals = scraper.fetch_deals()
    print(f"Total: {len(deals)}")
