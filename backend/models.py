from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import json


class DealStatus:
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass
class Deal:
    id: str
    title: str
    merchant: str
    original_price: float
    sale_price: float
    discount_percentage: int
    affiliate_url: str
    category: str
    image_url: str
    valid_from: datetime
    valid_until: datetime
    source: str  # Source type: pepper, bol, coolblue, user, affiliate
    created_at: datetime
    is_active: bool = True
    description: str = ""
    merchant_logo: str = ""
    coupon_code: Optional[str] = None
    status: str = DealStatus.APPROVED  # pending, approved, rejected
    source_url: str = ""  # Original URL where deal was found

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "merchant": self.merchant,
            "merchant_logo": self.merchant_logo,
            "original_price": self.original_price,
            "sale_price": self.sale_price,
            "discount_percentage": self.discount_percentage,
            "coupon_code": self.coupon_code,
            "affiliate_url": self.affiliate_url,
            "category": self.category,
            "image_url": self.image_url,
            "valid_from": self.valid_from.isoformat() if self.valid_from else None,
            "valid_until": self.valid_until.isoformat() if self.valid_until else None,
            "source": self.source,
            "source_url": self.source_url,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "is_active": self.is_active,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Deal":
        return cls(
            id=data["id"],
            title=data["title"],
            description=data.get("description", ""),
            merchant=data["merchant"],
            merchant_logo=data.get("merchant_logo", ""),
            original_price=float(data["original_price"]),
            sale_price=float(data["sale_price"]),
            discount_percentage=int(data["discount_percentage"]),
            coupon_code=data.get("coupon_code"),
            affiliate_url=data["affiliate_url"],
            category=data["category"],
            image_url=data["image_url"],
            valid_from=datetime.fromisoformat(data["valid_from"]) if data.get("valid_from") else datetime.now(),
            valid_until=datetime.fromisoformat(data["valid_until"]) if data.get("valid_until") else datetime.now(),
            source=data["source"],
            source_url=data.get("source_url", ""),
            status=data.get("status", DealStatus.APPROVED),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(),
            is_active=data.get("is_active", True),
        )

    @property
    def formatted_original_price(self) -> str:
        return f"€{self.original_price:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    @property
    def formatted_sale_price(self) -> str:
        return f"€{self.sale_price:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    @property
    def formatted_valid_until(self) -> str:
        months = ["jan", "feb", "mrt", "apr", "mei", "jun", "jul", "aug", "sep", "okt", "nov", "dec"]
        return f"{self.valid_until.day} {months[self.valid_until.month - 1]}"

    @property
    def is_expiring_soon(self) -> bool:
        """Check if deal expires within 3 days"""
        days_until_expiry = (self.valid_until - datetime.now()).days
        return 0 <= days_until_expiry <= 3

    @property
    def is_new(self) -> bool:
        """Check if deal was added in the last 24 hours"""
        hours_since_created = (datetime.now() - self.created_at).total_seconds() / 3600
        return hours_since_created <= 24
