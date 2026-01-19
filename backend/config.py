import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
FEEDS_DIR = DATA_DIR / "feeds"
DATABASE_PATH = DATA_DIR / "deals.db"

# Ensure directories exist (skip on read-only filesystems like Vercel)
try:
    DATA_DIR.mkdir(exist_ok=True)
    FEEDS_DIR.mkdir(exist_ok=True)
except OSError:
    pass  # Read-only filesystem (Vercel)

# Affiliate Network Credentials
DAISYCON_PUBLISHER_ID = os.getenv("DAISYCON_PUBLISHER_ID", "")
DAISYCON_API_KEY = os.getenv("DAISYCON_API_KEY", "")
TRADETRACKER_CUSTOMER_ID = os.getenv("TRADETRACKER_CUSTOMER_ID", "")
TRADETRACKER_PASSPHRASE = os.getenv("TRADETRACKER_PASSPHRASE", "")

# App Config
FEED_UPDATE_INTERVAL = int(os.getenv("FEED_UPDATE_INTERVAL", "3600"))

# Categories
CATEGORIES = [
    {"slug": "all", "name": "Alle", "icon": "🏷️"},
    {"slug": "electronics", "name": "Elektronica", "icon": "📱"},
    {"slug": "fashion", "name": "Mode", "icon": "👗"},
    {"slug": "home", "name": "Wonen", "icon": "🏠"},
    {"slug": "sports", "name": "Sport", "icon": "⚽"},
    {"slug": "beauty", "name": "Beauty", "icon": "💄"},
    {"slug": "food", "name": "Food", "icon": "🍕"},
    {"slug": "travel", "name": "Reizen", "icon": "✈️"},
    {"slug": "other", "name": "Overig", "icon": "📦"},
]
