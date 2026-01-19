"""
Pepper.nl (formerly Pepper.com/nl) deal scraper.

Uses the public RSS feed to fetch hot deals from the Dutch Pepper community.
"""

import re
from datetime import datetime, timedelta
from typing import List, Optional
import feedparser

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.models import Deal, DealStatus
from .base import BaseScraper


class PepperScraper(BaseScraper):
    """Scraper for Pepper.nl deals"""

    name = "pepper"
    source_type = "pepper"

    # Pepper.nl RSS feeds
    FEEDS = {
        "hot": "https://nl.pepper.com/rss/hot",
        "new": "https://nl.pepper.com/rss/nieuw",
    }

    def fetch_deals(self) -> List[Deal]:
        """Fetch deals from Pepper.nl RSS feeds"""
        deals = []

        for feed_name, feed_url in self.FEEDS.items():
            print(f"[{self.name}] Fetching {feed_name} feed...")
            feed_deals = self._parse_feed(feed_url)
            deals.extend(feed_deals)

        return deals

    def _parse_feed(self, feed_url: str) -> List[Deal]:
        """Parse a single RSS feed"""
        deals = []

        try:
            feed = feedparser.parse(feed_url)

            if feed.bozo:
                print(f"[{self.name}] Feed parse warning: {feed.bozo_exception}")

            for entry in feed.entries:
                deal = self._parse_entry(entry)
                if deal:
                    deals.append(deal)

        except Exception as e:
            print(f"[{self.name}] Error parsing feed: {e}")

        return deals

    def _parse_entry(self, entry) -> Optional[Deal]:
        """Parse a single RSS entry into a Deal"""
        try:
            title = entry.get('title', '')
            if not title:
                return None

            # Extract link
            link = entry.get('link', '')

            # Extract description
            description = entry.get('summary', '')

            # Try to extract price from title or description
            # Pepper titles often have format: "Product Name voor €XX,XX"
            original_price, sale_price = self._extract_prices(title, description)

            # Calculate discount if we have prices
            discount = 0
            if original_price and sale_price and original_price > sale_price:
                discount = int(((original_price - sale_price) / original_price) * 100)
            elif sale_price:
                # No original price - estimate 20% discount
                original_price = sale_price * 1.25
                discount = 20

            # If we couldn't find any price, skip this deal
            if not sale_price:
                # Try to extract any price
                sale_price = self._extract_any_price(title + " " + description)
                if sale_price:
                    original_price = sale_price * 1.25
                    discount = 20
                else:
                    # Still no price - might be a freebie or coupon-only deal
                    sale_price = 0.0
                    original_price = 0.0
                    discount = 100

            # Extract merchant
            merchant = self._extract_merchant(title, description)

            # Extract image
            image_url = self._extract_image(entry)

            # Extract coupon code
            coupon_code = self._extract_coupon(title, description)

            # Detect category
            category = self.detect_category(title, description)

            # Generate unique ID
            deal_id = self.generate_id(self.name, link or title)

            # Parse published date
            published = entry.get('published_parsed')
            if published:
                created_at = datetime(*published[:6])
            else:
                created_at = datetime.now()

            return Deal(
                id=deal_id,
                title=self._clean_title(title),
                description=self._clean_description(description),
                merchant=merchant,
                merchant_logo=self.get_merchant_logo(merchant),
                original_price=original_price or 0,
                sale_price=sale_price or 0,
                discount_percentage=discount,
                coupon_code=coupon_code,
                affiliate_url=link,  # Direct link (no affiliate yet)
                category=category,
                image_url=image_url,
                valid_from=created_at,
                valid_until=created_at + timedelta(days=7),  # Assume 7 day validity
                source=self.source_type,
                source_url=link,
                status=DealStatus.PENDING,  # Needs approval
                created_at=datetime.now(),
                is_active=True,
            )

        except Exception as e:
            print(f"[{self.name}] Error parsing entry: {e}")
            return None

    def _extract_prices(self, title: str, description: str) -> tuple:
        """Extract original and sale prices from text"""
        text = f"{title} {description}"

        # Pattern: "voor €XX,XX" or "€XX,XX"
        sale_match = re.search(r'voor\s*€?\s*([\d.,]+)', text, re.IGNORECASE)
        if sale_match:
            sale_price = self.parse_price(sale_match.group(1))
        else:
            sale_price = None

        # Pattern: "(was €XX,XX)" or "i.p.v. €XX,XX"
        original_match = re.search(r'(?:was|i\.?p\.?v\.?|van)\s*€?\s*([\d.,]+)', text, re.IGNORECASE)
        if original_match:
            original_price = self.parse_price(original_match.group(1))
        else:
            original_price = None

        return original_price, sale_price

    def _extract_any_price(self, text: str) -> Optional[float]:
        """Extract any price from text"""
        # Look for €XX,XX patterns
        matches = re.findall(r'€\s*([\d.,]+)', text)
        if matches:
            prices = [self.parse_price(m) for m in matches]
            prices = [p for p in prices if p and p > 0]
            if prices:
                return min(prices)  # Return lowest (likely sale price)
        return None

    def _extract_merchant(self, title: str, description: str) -> str:
        """Extract merchant name from text"""
        text = f"{title} {description}".lower()

        # Check known merchants
        known_merchants = [
            ("bol.com", "Bol.com"),
            ("coolblue", "Coolblue"),
            ("mediamarkt", "MediaMarkt"),
            ("amazon", "Amazon.nl"),
            ("zalando", "Zalando"),
            ("wehkamp", "Wehkamp"),
            ("kruidvat", "Kruidvat"),
            ("hema", "HEMA"),
            ("ikea", "IKEA"),
            ("albert heijn", "Albert Heijn"),
            ("ah.nl", "Albert Heijn"),
            ("jumbo", "Jumbo"),
            ("lidl", "Lidl"),
            ("action", "Action"),
            ("decathlon", "Decathlon"),
            ("douglas", "Douglas"),
            ("booking", "Booking.com"),
        ]

        for keyword, name in known_merchants:
            if keyword in text:
                return name

        # Try to extract from "@ Store" or "bij Store" pattern
        at_match = re.search(r'(?:@|bij|via)\s+([A-Za-z0-9.]+)', title, re.IGNORECASE)
        if at_match:
            return at_match.group(1).strip()

        return "Diverse"

    def _extract_image(self, entry) -> str:
        """Extract image URL from entry"""
        # Check media content
        if hasattr(entry, 'media_content') and entry.media_content:
            for media in entry.media_content:
                if 'url' in media:
                    return media['url']

        # Check enclosures
        if hasattr(entry, 'enclosures') and entry.enclosures:
            for enc in entry.enclosures:
                if 'url' in enc and 'image' in enc.get('type', ''):
                    return enc['url']

        # Check for image in description
        img_match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', entry.get('summary', ''))
        if img_match:
            return img_match.group(1)

        return ""

    def _extract_coupon(self, title: str, description: str) -> Optional[str]:
        """Extract coupon code from text"""
        text = f"{title} {description}"

        # Look for "code: XXX" or "code XXX" patterns
        code_match = re.search(r'code[:\s]+([A-Z0-9]{4,20})', text, re.IGNORECASE)
        if code_match:
            return code_match.group(1).upper()

        # Look for standalone coupon-like strings in caps
        caps_match = re.search(r'\b([A-Z0-9]{5,15})\b', text)
        if caps_match:
            potential_code = caps_match.group(1)
            # Verify it looks like a coupon (has both letters and numbers, or specific patterns)
            if re.search(r'[A-Z]', potential_code) and re.search(r'[0-9]', potential_code):
                return potential_code

        return None

    def _clean_title(self, title: str) -> str:
        """Clean up title"""
        # Remove excessive whitespace
        title = re.sub(r'\s+', ' ', title).strip()
        # Remove "@ Store" suffix as we have merchant separately
        title = re.sub(r'\s*@\s*[A-Za-z0-9.]+\s*$', '', title)
        return title

    def _clean_description(self, description: str) -> str:
        """Clean up description"""
        # Remove HTML tags
        description = re.sub(r'<[^>]+>', '', description)
        # Remove excessive whitespace
        description = re.sub(r'\s+', ' ', description).strip()
        return description[:500]  # Limit length


if __name__ == "__main__":
    # Test the scraper
    scraper = PepperScraper()
    scraper.run()
