"""
JSON-based deals storage.

Simple file-based storage that works with Vercel's read-only filesystem.
Deals are stored in data/deals.json and committed to the repo.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from .config import BASE_DIR
from .models import Deal, DealStatus


DEALS_FILE = BASE_DIR / "data" / "deals.json"


def load_deals() -> List[Deal]:
    """Load all deals from JSON file"""
    if not DEALS_FILE.exists():
        return []

    try:
        with open(DEALS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return [Deal.from_dict(d) for d in data]
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Error loading deals: {e}")
        return []


def save_deals(deals: List[Deal]):
    """Save all deals to JSON file"""
    DEALS_FILE.parent.mkdir(parents=True, exist_ok=True)

    data = [deal.to_dict() for deal in deals]
    with open(DEALS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_all_deals(
    category: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    sort_by: str = "created_at",
    sort_order: str = "desc"
) -> List[Deal]:
    """Get deals with optional filtering"""
    deals = load_deals()

    # Filter active and not expired
    now = datetime.now()
    deals = [d for d in deals if d.is_active and d.valid_until >= now]

    # Filter by category
    if category and category != "all":
        deals = [d for d in deals if d.category == category]

    # Sort
    reverse = sort_order.lower() == "desc"
    if sort_by == "created_at":
        deals.sort(key=lambda d: d.created_at, reverse=reverse)
    elif sort_by == "discount_percentage":
        deals.sort(key=lambda d: d.discount_percentage, reverse=reverse)
    elif sort_by == "valid_until":
        deals.sort(key=lambda d: d.valid_until, reverse=reverse)
    elif sort_by == "sale_price":
        deals.sort(key=lambda d: d.sale_price, reverse=reverse)

    # Paginate
    return deals[offset:offset + limit]


def get_deal_by_id(deal_id: str) -> Optional[Deal]:
    """Get a single deal by ID"""
    deals = load_deals()
    for deal in deals:
        if deal.id == deal_id:
            return deal
    return None


def count_deals(category: Optional[str] = None) -> int:
    """Count active deals"""
    deals = load_deals()
    now = datetime.now()
    deals = [d for d in deals if d.is_active and d.valid_until >= now]

    if category and category != "all":
        deals = [d for d in deals if d.category == category]

    return len(deals)


def search_deals(query: str, limit: int = 50) -> List[Deal]:
    """Search deals by title or merchant"""
    deals = load_deals()
    now = datetime.now()
    query_lower = query.lower()

    results = []
    for deal in deals:
        if not deal.is_active or deal.valid_until < now:
            continue
        if query_lower in deal.title.lower() or query_lower in deal.merchant.lower():
            results.append(deal)

    # Sort by discount
    results.sort(key=lambda d: d.discount_percentage, reverse=True)
    return results[:limit]


def get_merchants() -> List[str]:
    """Get list of unique merchants"""
    deals = load_deals()
    merchants = set(d.merchant for d in deals if d.is_active)
    return sorted(merchants)


def add_deal(deal: Deal) -> bool:
    """Add a new deal (used by scrapers)"""
    deals = load_deals()

    # Check if already exists
    existing_ids = {d.id for d in deals}
    if deal.id in existing_ids:
        return False

    deals.append(deal)
    save_deals(deals)
    return True


def add_deals(new_deals: List[Deal]) -> int:
    """Add multiple deals, skip duplicates"""
    deals = load_deals()
    existing_ids = {d.id for d in deals}

    added = 0
    for deal in new_deals:
        if deal.id not in existing_ids:
            deals.append(deal)
            existing_ids.add(deal.id)
            added += 1

    if added > 0:
        save_deals(deals)

    return added


def cleanup_expired_deals():
    """Remove deals that expired more than 7 days ago"""
    deals = load_deals()
    now = datetime.now()

    # Keep deals that haven't expired or expired less than 7 days ago
    from datetime import timedelta
    cutoff = now - timedelta(days=7)

    active_deals = [d for d in deals if d.valid_until >= cutoff]

    if len(active_deals) < len(deals):
        save_deals(active_deals)
        return len(deals) - len(active_deals)

    return 0


def update_deal(deal_id: str, updated_deal: Deal) -> bool:
    """Update an existing deal"""
    deals = load_deals()

    for i, deal in enumerate(deals):
        if deal.id == deal_id:
            deals[i] = updated_deal
            save_deals(deals)
            return True

    return False


def delete_deal(deal_id: str) -> bool:
    """Delete a deal by ID"""
    deals = load_deals()
    original_count = len(deals)

    deals = [d for d in deals if d.id != deal_id]

    if len(deals) < original_count:
        save_deals(deals)
        return True

    return False


def get_all_deals_unfiltered() -> List[Deal]:
    """Get all deals without filtering (for admin)"""
    return load_deals()
