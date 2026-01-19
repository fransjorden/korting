"""
Base scraper class for deal discovery.
"""

import hashlib
import re
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import List, Optional
from urllib.request import urlopen, Request
from urllib.error import URLError

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.models import Deal, DealStatus
from backend.database import insert_deal, deal_exists


class BaseScraper(ABC):
    """Base class for all deal scrapers"""

    name: str = "base"
    source_type: str = "scraper"

    # Merchant logo mapping
    MERCHANT_LOGOS = {
        "bol.com": "https://logo.clearbit.com/bol.com",
        "coolblue": "https://logo.clearbit.com/coolblue.nl",
        "mediamarkt": "https://logo.clearbit.com/mediamarkt.nl",
        "amazon": "https://logo.clearbit.com/amazon.nl",
        "zalando": "https://logo.clearbit.com/zalando.nl",
        "wehkamp": "https://logo.clearbit.com/wehkamp.nl",
        "kruidvat": "https://logo.clearbit.com/kruidvat.nl",
        "hema": "https://logo.clearbit.com/hema.nl",
        "ikea": "https://logo.clearbit.com/ikea.com",
        "ah": "https://logo.clearbit.com/ah.nl",
        "albert heijn": "https://logo.clearbit.com/ah.nl",
        "jumbo": "https://logo.clearbit.com/jumbo.com",
        "lidl": "https://logo.clearbit.com/lidl.nl",
        "action": "https://logo.clearbit.com/action.com",
        "decathlon": "https://logo.clearbit.com/decathlon.nl",
        "gamma": "https://logo.clearbit.com/gamma.nl",
        "praxis": "https://logo.clearbit.com/praxis.nl",
        "blokker": "https://logo.clearbit.com/blokker.nl",
        "douglas": "https://logo.clearbit.com/douglas.nl",
        "ici paris xl": "https://logo.clearbit.com/iciparisxl.nl",
        "booking.com": "https://logo.clearbit.com/booking.com",
        "thuisbezorgd": "https://logo.clearbit.com/thuisbezorgd.nl",
    }

    # Category mapping
    CATEGORY_KEYWORDS = {
        "electronics": ["tv", "laptop", "tablet", "telefoon", "phone", "iphone", "samsung", "sony", "computer", "gaming", "playstation", "xbox", "nintendo", "koptelefoon", "headphone", "speaker", "camera", "drone"],
        "fashion": ["kleding", "schoenen", "sneakers", "nike", "adidas", "mode", "shirt", "jeans", "jas", "jacket", "dress", "jurk"],
        "home": ["meubel", "bank", "stoel", "tafel", "keuken", "bed", "matras", "lamp", "ikea", "wonen", "tuin", "garden"],
        "sports": ["sport", "fitness", "fiets", "bike", "voetbal", "hardlopen", "gym", "decathlon"],
        "beauty": ["parfum", "makeup", "skincare", "shampoo", "douglas", "kruidvat", "beauty", "cosmetica"],
        "food": ["eten", "food", "restaurant", "thuisbezorgd", "pizza", "ah", "jumbo", "lidl", "supermarkt"],
        "travel": ["reis", "travel", "hotel", "vlucht", "flight", "booking", "vakantie", "koffer"],
    }

    @abstractmethod
    def fetch_deals(self) -> List[Deal]:
        """Fetch deals from the source. Must be implemented by subclasses."""
        pass

    def run(self) -> int:
        """Run the scraper and insert new deals into the database"""
        print(f"[{self.name}] Fetching deals...")
        deals = self.fetch_deals()
        print(f"[{self.name}] Found {len(deals)} deals")

        new_deals = 0
        for deal in deals:
            if not deal_exists(deal.id):
                if insert_deal(deal):
                    new_deals += 1
                    # Safe print for Windows console
                    try:
                        print(f"[{self.name}] + {deal.title[:50]}...")
                    except UnicodeEncodeError:
                        safe_title = deal.title[:50].encode('ascii', 'replace').decode('ascii')
                        print(f"[{self.name}] + {safe_title}...")

        print(f"[{self.name}] Added {new_deals} new deals")
        return new_deals

    def generate_id(self, *parts) -> str:
        """Generate a unique deal ID from parts"""
        content = ":".join(str(p) for p in parts)
        return hashlib.md5(content.encode()).hexdigest()[:12]

    def get_merchant_logo(self, merchant: str) -> str:
        """Get logo URL for a merchant"""
        merchant_lower = merchant.lower()
        for key, url in self.MERCHANT_LOGOS.items():
            if key in merchant_lower:
                return url
        # Fallback: try clearbit
        domain = re.sub(r'[^a-z0-9]', '', merchant_lower)
        return f"https://logo.clearbit.com/{domain}.nl"

    def detect_category(self, title: str, description: str = "") -> str:
        """Detect category from title and description"""
        text = f"{title} {description}".lower()
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text:
                    return category
        return "other"

    def parse_price(self, price_str: str) -> Optional[float]:
        """Parse price string to float"""
        if not price_str:
            return None
        # Remove currency symbols and normalize
        price_str = re.sub(r'[€$]', '', price_str)
        price_str = price_str.replace(',', '.').strip()
        # Handle "1.234,56" format
        if '.' in price_str and price_str.count('.') > 1:
            price_str = price_str.replace('.', '', price_str.count('.') - 1)
        try:
            return float(price_str)
        except ValueError:
            return None

    def fetch_url(self, url: str, headers: Optional[dict] = None) -> Optional[str]:
        """Fetch content from URL"""
        default_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'nl-NL,nl;q=0.9,en;q=0.8',
        }
        if headers:
            default_headers.update(headers)

        try:
            request = Request(url, headers=default_headers)
            with urlopen(request, timeout=30) as response:
                return response.read().decode('utf-8')
        except URLError as e:
            print(f"[{self.name}] Error fetching {url}: {e}")
            return None
        except Exception as e:
            print(f"[{self.name}] Unexpected error: {e}")
            return None
