"""
Generate mock deals data for development/testing.
Run this script to populate the database with sample deals.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime, timedelta
import random
from backend.database import init_db, insert_deal
from backend.models import Deal

# Mock merchants with logos (using placeholder logos)
MERCHANTS = [
    {"name": "Bol.com", "logo": "https://logo.clearbit.com/bol.com"},
    {"name": "Coolblue", "logo": "https://logo.clearbit.com/coolblue.nl"},
    {"name": "MediaMarkt", "logo": "https://logo.clearbit.com/mediamarkt.nl"},
    {"name": "Zalando", "logo": "https://logo.clearbit.com/zalando.nl"},
    {"name": "Amazon.nl", "logo": "https://logo.clearbit.com/amazon.nl"},
    {"name": "HEMA", "logo": "https://logo.clearbit.com/hema.nl"},
    {"name": "Wehkamp", "logo": "https://logo.clearbit.com/wehkamp.nl"},
    {"name": "Kruidvat", "logo": "https://logo.clearbit.com/kruidvat.nl"},
    {"name": "Decathlon", "logo": "https://logo.clearbit.com/decathlon.nl"},
    {"name": "IKEA", "logo": "https://logo.clearbit.com/ikea.com"},
    {"name": "Booking.com", "logo": "https://logo.clearbit.com/booking.com"},
    {"name": "Albert Heijn", "logo": "https://logo.clearbit.com/ah.nl"},
]

# Sample products per category
PRODUCTS = {
    "electronics": [
        {"title": "Samsung Galaxy S24 Ultra 256GB", "original": 1449.00, "sale": 1149.00, "image": "https://images.unsplash.com/photo-1610945415295-d9bbf067e59c?w=400"},
        {"title": "Apple AirPods Pro 2", "original": 279.00, "sale": 229.00, "image": "https://images.unsplash.com/photo-1600294037681-c80b4cb5b434?w=400"},
        {"title": "Sony WH-1000XM5 Koptelefoon", "original": 399.00, "sale": 299.00, "image": "https://images.unsplash.com/photo-1546435770-a3e426bf472b?w=400"},
        {"title": "LG OLED55C4 55\" 4K TV", "original": 1799.00, "sale": 1299.00, "image": "https://images.unsplash.com/photo-1593359677879-a4bb92f829d1?w=400"},
        {"title": "Nintendo Switch OLED", "original": 359.00, "sale": 299.00, "image": "https://images.unsplash.com/photo-1578303512597-81e6cc155b3e?w=400"},
        {"title": "iPad Air 2024 256GB", "original": 849.00, "sale": 749.00, "image": "https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?w=400"},
        {"title": "DJI Mini 4 Pro Drone", "original": 999.00, "sale": 799.00, "image": "https://images.unsplash.com/photo-1473968512647-3e447244af8f?w=400"},
        {"title": "Philips Hue Starterkit", "original": 179.00, "sale": 129.00, "image": "https://images.unsplash.com/photo-1558089687-f282ffcbc126?w=400"},
    ],
    "fashion": [
        {"title": "Nike Air Max 90 Sneakers", "original": 149.99, "sale": 99.99, "image": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400"},
        {"title": "Levi's 501 Original Jeans", "original": 119.00, "sale": 79.00, "image": "https://images.unsplash.com/photo-1542272604-787c3835535d?w=400"},
        {"title": "The North Face Puffer Jacket", "original": 299.00, "sale": 199.00, "image": "https://images.unsplash.com/photo-1591047139829-d91aecb6caea?w=400"},
        {"title": "Ray-Ban Aviator Zonnebril", "original": 169.00, "sale": 119.00, "image": "https://images.unsplash.com/photo-1572635196237-14b3f281503f?w=400"},
        {"title": "Adidas Ultraboost Running", "original": 189.00, "sale": 129.00, "image": "https://images.unsplash.com/photo-1608231387042-66d1773070a5?w=400"},
        {"title": "Tommy Hilfiger Polo Shirt", "original": 89.90, "sale": 59.90, "image": "https://images.unsplash.com/photo-1625910513413-5fc4c283fba5?w=400"},
    ],
    "home": [
        {"title": "Dyson V15 Detect Stofzuiger", "original": 749.00, "sale": 599.00, "image": "https://images.unsplash.com/photo-1558317374-067fb5f30001?w=400"},
        {"title": "Philips Airfryer XXL", "original": 299.00, "sale": 199.00, "image": "https://images.unsplash.com/photo-1626509653291-18d9a934b9db?w=400"},
        {"title": "Nespresso Vertuo Next", "original": 199.00, "sale": 129.00, "image": "https://images.unsplash.com/photo-1517668808822-9ebb02f2a0e6?w=400"},
        {"title": "IKEA MALM Bed 160x200", "original": 299.00, "sale": 249.00, "image": "https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?w=400"},
        {"title": "Brabantia Bo Afvalbak 60L", "original": 249.00, "sale": 179.00, "image": "https://images.unsplash.com/photo-1604187351574-c75ca79f5807?w=400"},
        {"title": "KitchenAid Artisan Mixer", "original": 649.00, "sale": 479.00, "image": "https://images.unsplash.com/photo-1594385208974-2e75f8d7bb48?w=400"},
    ],
    "sports": [
        {"title": "Garmin Forerunner 265 Sporthorloge", "original": 449.00, "sale": 379.00, "image": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400"},
        {"title": "Peloton Hometrainer", "original": 1495.00, "sale": 1195.00, "image": "https://images.unsplash.com/photo-1591291621164-2c6367723315?w=400"},
        {"title": "TRX Pro4 Suspension Trainer", "original": 269.00, "sale": 199.00, "image": "https://images.unsplash.com/photo-1534438327276-14e5300c3a48?w=400"},
        {"title": "Adidas Predator Voetbalschoenen", "original": 159.00, "sale": 109.00, "image": "https://images.unsplash.com/photo-1511886929837-354d827aae26?w=400"},
        {"title": "Kettlebell Set 4-16kg", "original": 199.00, "sale": 149.00, "image": "https://images.unsplash.com/photo-1517963879433-6ad2b056d712?w=400"},
    ],
    "beauty": [
        {"title": "Dyson Airwrap Complete", "original": 549.00, "sale": 449.00, "image": "https://images.unsplash.com/photo-1522338140262-f46f5913618a?w=400"},
        {"title": "Chanel No. 5 Eau de Parfum 100ml", "original": 169.00, "sale": 139.00, "image": "https://images.unsplash.com/photo-1541643600914-78b084683601?w=400"},
        {"title": "Philips Lumea IPL Ontharing", "original": 499.00, "sale": 349.00, "image": "https://images.unsplash.com/photo-1596462502278-27bfdc403348?w=400"},
        {"title": "La Roche-Posay Skincare Set", "original": 89.00, "sale": 59.00, "image": "https://images.unsplash.com/photo-1556228720-195a672e8a03?w=400"},
        {"title": "GHD Platinum+ Stijltang", "original": 279.00, "sale": 219.00, "image": "https://images.unsplash.com/photo-1527799820374-dcf8d9d4a388?w=400"},
    ],
    "food": [
        {"title": "HelloFresh 4 Weken Box", "original": 199.00, "sale": 99.00, "image": "https://images.unsplash.com/photo-1498837167922-ddd27525d352?w=400"},
        {"title": "Nespresso Capsules 100 stuks", "original": 45.00, "sale": 35.00, "image": "https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?w=400"},
        {"title": "Tony's Chocolonely Proefpakket", "original": 29.95, "sale": 22.95, "image": "https://images.unsplash.com/photo-1481391319762-47dff72954d9?w=400"},
        {"title": "Picnic Boodschappen €15 Korting", "original": 15.00, "sale": 0.00, "image": "https://images.unsplash.com/photo-1542838132-92c53300491e?w=400"},
    ],
    "travel": [
        {"title": "Samsonite Koffer 75cm", "original": 329.00, "sale": 229.00, "image": "https://images.unsplash.com/photo-1565026057447-bc90a3dceb87?w=400"},
        {"title": "Booking.com €50 Reistegoed", "original": 50.00, "sale": 0.00, "image": "https://images.unsplash.com/photo-1436491865332-7a61a109cc05?w=400"},
        {"title": "Osprey Farpoint 40L Rugzak", "original": 189.00, "sale": 149.00, "image": "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=400"},
        {"title": "NS Flex Dagkaart", "original": 54.40, "sale": 19.00, "image": "https://images.unsplash.com/photo-1474487548417-781cb71495f3?w=400"},
    ],
}

# Coupon codes (some deals have them, some don't)
COUPON_CODES = ["KORTING20", "SAVE15", "DEAL10", "EXTRA25", "FLASH30", "NIEUW10", "WINTER50", None, None, None]


def generate_mock_deals(num_deals: int = 50):
    """Generate and insert mock deals into the database"""
    print("Initializing database...")
    init_db()

    print(f"Generating {num_deals} mock deals...")
    deals_created = 0

    for i in range(num_deals):
        # Pick random category and product
        category = random.choice(list(PRODUCTS.keys()))
        product = random.choice(PRODUCTS[category])
        merchant_info = random.choice(MERCHANTS)

        # Calculate prices with some variance
        variance = random.uniform(0.9, 1.1)
        original = round(product["original"] * variance, 2)
        sale = round(product["sale"] * variance, 2)
        discount = int(((original - sale) / original) * 100)

        # Random dates
        created_days_ago = random.randint(0, 7)
        valid_days = random.randint(3, 30)

        deal = Deal(
            id=f"deal-{i+1:04d}",
            title=product["title"],
            description=f"Geweldige aanbieding op {product['title']} bij {merchant_info['name']}!",
            merchant=merchant_info["name"],
            merchant_logo=merchant_info["logo"],
            original_price=original,
            sale_price=sale,
            discount_percentage=discount,
            coupon_code=random.choice(COUPON_CODES),
            affiliate_url=f"https://kort.ing/go/{i+1}",
            category=category,
            image_url=product["image"],
            valid_from=datetime.now() - timedelta(days=created_days_ago),
            valid_until=datetime.now() + timedelta(days=valid_days),
            source="mock",
            created_at=datetime.now() - timedelta(days=created_days_ago, hours=random.randint(0, 23)),
            is_active=True,
        )

        if insert_deal(deal):
            deals_created += 1

    print(f"Successfully created {deals_created} deals!")


if __name__ == "__main__":
    num = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    generate_mock_deals(num)
