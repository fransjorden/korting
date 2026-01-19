import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from contextlib import contextmanager

from .config import DATABASE_PATH
from .models import Deal, DealStatus


def init_db():
    """Initialize the database with required tables"""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS deals (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                merchant TEXT NOT NULL,
                merchant_logo TEXT,
                original_price REAL NOT NULL,
                sale_price REAL NOT NULL,
                discount_percentage INTEGER NOT NULL,
                coupon_code TEXT,
                affiliate_url TEXT NOT NULL,
                category TEXT NOT NULL,
                image_url TEXT,
                valid_from TEXT,
                valid_until TEXT,
                source TEXT NOT NULL,
                source_url TEXT DEFAULT '',
                status TEXT DEFAULT 'approved',
                created_at TEXT NOT NULL,
                is_active INTEGER DEFAULT 1
            )
        """)
        # Migration: add new columns if they don't exist (run before creating indexes)
        try:
            conn.execute("ALTER TABLE deals ADD COLUMN source_url TEXT DEFAULT ''")
        except sqlite3.OperationalError:
            pass  # Column already exists
        try:
            conn.execute("ALTER TABLE deals ADD COLUMN status TEXT DEFAULT 'approved'")
        except sqlite3.OperationalError:
            pass  # Column already exists

        # Create indexes (after migrations)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_category ON deals(category)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_merchant ON deals(merchant)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_is_active ON deals(is_active)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_valid_until ON deals(valid_until)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_status ON deals(status)")

        conn.commit()


@contextmanager
def get_connection():
    """Context manager for database connections"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def insert_deal(deal: Deal) -> bool:
    """Insert a new deal into the database"""
    with get_connection() as conn:
        try:
            conn.execute("""
                INSERT OR REPLACE INTO deals
                (id, title, description, merchant, merchant_logo, original_price, sale_price,
                 discount_percentage, coupon_code, affiliate_url, category, image_url,
                 valid_from, valid_until, source, source_url, status, created_at, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                deal.id, deal.title, deal.description, deal.merchant, deal.merchant_logo,
                deal.original_price, deal.sale_price, deal.discount_percentage, deal.coupon_code,
                deal.affiliate_url, deal.category, deal.image_url,
                deal.valid_from.isoformat(), deal.valid_until.isoformat(),
                deal.source, deal.source_url, deal.status,
                deal.created_at.isoformat(), 1 if deal.is_active else 0
            ))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error inserting deal: {e}")
            return False


def deal_exists(deal_id: str) -> bool:
    """Check if a deal with this ID already exists"""
    with get_connection() as conn:
        cursor = conn.execute("SELECT 1 FROM deals WHERE id = ?", (deal_id,))
        return cursor.fetchone() is not None


def get_all_deals(
    category: Optional[str] = None,
    merchant: Optional[str] = None,
    active_only: bool = True,
    approved_only: bool = True,
    limit: int = 100,
    offset: int = 0,
    sort_by: str = "created_at",
    sort_order: str = "desc"
) -> List[Deal]:
    """Get deals with optional filtering"""
    query = "SELECT * FROM deals WHERE 1=1"
    params = []

    if approved_only:
        query += " AND status = ?"
        params.append(DealStatus.APPROVED)

    if active_only:
        query += " AND is_active = 1"
        query += " AND valid_until >= ?"
        params.append(datetime.now().isoformat())

    if category and category != "all":
        query += " AND category = ?"
        params.append(category)

    if merchant:
        query += " AND merchant = ?"
        params.append(merchant)

    # Sorting
    valid_sort_fields = ["created_at", "discount_percentage", "valid_until", "sale_price"]
    if sort_by not in valid_sort_fields:
        sort_by = "created_at"

    sort_order = "DESC" if sort_order.lower() == "desc" else "ASC"
    query += f" ORDER BY {sort_by} {sort_order}"

    query += " LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    with get_connection() as conn:
        cursor = conn.execute(query, params)
        rows = cursor.fetchall()
        return [_row_to_deal(row) for row in rows]


def get_deal_by_id(deal_id: str) -> Optional[Deal]:
    """Get a single deal by ID"""
    with get_connection() as conn:
        cursor = conn.execute("SELECT * FROM deals WHERE id = ?", (deal_id,))
        row = cursor.fetchone()
        return _row_to_deal(row) if row else None


def get_merchants() -> List[str]:
    """Get list of unique merchants"""
    with get_connection() as conn:
        cursor = conn.execute("SELECT DISTINCT merchant FROM deals WHERE is_active = 1 ORDER BY merchant")
        return [row[0] for row in cursor.fetchall()]


def search_deals(query: str, limit: int = 50) -> List[Deal]:
    """Search deals by title or merchant"""
    with get_connection() as conn:
        cursor = conn.execute("""
            SELECT * FROM deals
            WHERE is_active = 1
            AND (title LIKE ? OR merchant LIKE ? OR description LIKE ?)
            AND valid_until >= ?
            ORDER BY discount_percentage DESC
            LIMIT ?
        """, (f"%{query}%", f"%{query}%", f"%{query}%", datetime.now().isoformat(), limit))
        return [_row_to_deal(row) for row in cursor.fetchall()]


def count_deals(category: Optional[str] = None, active_only: bool = True) -> int:
    """Count deals with optional filtering"""
    query = "SELECT COUNT(*) FROM deals WHERE 1=1"
    params = []

    if active_only:
        query += " AND is_active = 1"
        query += " AND valid_until >= ?"
        params.append(datetime.now().isoformat())

    if category and category != "all":
        query += " AND category = ?"
        params.append(category)

    with get_connection() as conn:
        cursor = conn.execute(query, params)
        return cursor.fetchone()[0]


def _row_to_deal(row: sqlite3.Row) -> Deal:
    """Convert a database row to a Deal object"""
    # Handle both old and new schema
    source_url = ""
    status = DealStatus.APPROVED
    try:
        source_url = row["source_url"] or ""
    except (IndexError, KeyError):
        pass
    try:
        status = row["status"] or DealStatus.APPROVED
    except (IndexError, KeyError):
        pass

    return Deal(
        id=row["id"],
        title=row["title"],
        description=row["description"] or "",
        merchant=row["merchant"],
        merchant_logo=row["merchant_logo"] or "",
        original_price=row["original_price"],
        sale_price=row["sale_price"],
        discount_percentage=row["discount_percentage"],
        coupon_code=row["coupon_code"],
        affiliate_url=row["affiliate_url"],
        category=row["category"],
        image_url=row["image_url"] or "",
        valid_from=datetime.fromisoformat(row["valid_from"]) if row["valid_from"] else datetime.now(),
        valid_until=datetime.fromisoformat(row["valid_until"]) if row["valid_until"] else datetime.now(),
        source=row["source"],
        source_url=source_url,
        status=status,
        created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else datetime.now(),
        is_active=bool(row["is_active"]),
    )


# Admin queue functions

def get_pending_deals(limit: int = 50) -> List[Deal]:
    """Get deals awaiting approval"""
    with get_connection() as conn:
        cursor = conn.execute("""
            SELECT * FROM deals
            WHERE status = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (DealStatus.PENDING, limit))
        return [_row_to_deal(row) for row in cursor.fetchall()]


def count_pending_deals() -> int:
    """Count deals awaiting approval"""
    with get_connection() as conn:
        cursor = conn.execute(
            "SELECT COUNT(*) FROM deals WHERE status = ?",
            (DealStatus.PENDING,)
        )
        return cursor.fetchone()[0]


def approve_deal(deal_id: str) -> bool:
    """Approve a pending deal"""
    with get_connection() as conn:
        try:
            conn.execute(
                "UPDATE deals SET status = ? WHERE id = ?",
                (DealStatus.APPROVED, deal_id)
            )
            conn.commit()
            return conn.total_changes > 0
        except Exception as e:
            print(f"Error approving deal: {e}")
            return False


def reject_deal(deal_id: str) -> bool:
    """Reject a pending deal"""
    with get_connection() as conn:
        try:
            conn.execute(
                "UPDATE deals SET status = ? WHERE id = ?",
                (DealStatus.REJECTED, deal_id)
            )
            conn.commit()
            return conn.total_changes > 0
        except Exception as e:
            print(f"Error rejecting deal: {e}")
            return False


def update_deal(deal_id: str, updates: dict) -> bool:
    """Update specific fields of a deal"""
    allowed_fields = [
        "title", "description", "merchant", "original_price", "sale_price",
        "discount_percentage", "coupon_code", "category", "image_url", "valid_until"
    ]

    # Filter to only allowed fields
    updates = {k: v for k, v in updates.items() if k in allowed_fields}
    if not updates:
        return False

    set_clause = ", ".join(f"{k} = ?" for k in updates.keys())
    values = list(updates.values()) + [deal_id]

    with get_connection() as conn:
        try:
            conn.execute(f"UPDATE deals SET {set_clause} WHERE id = ?", values)
            conn.commit()
            return conn.total_changes > 0
        except Exception as e:
            print(f"Error updating deal: {e}")
            return False


def delete_deal(deal_id: str) -> bool:
    """Permanently delete a deal"""
    with get_connection() as conn:
        try:
            conn.execute("DELETE FROM deals WHERE id = ?", (deal_id,))
            conn.commit()
            return conn.total_changes > 0
        except Exception as e:
            print(f"Error deleting deal: {e}")
            return False
