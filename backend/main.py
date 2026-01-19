from fastapi import FastAPI, Request, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
from typing import Optional
from datetime import datetime

from .config import CATEGORIES, BASE_DIR
from .deals_store import (
    get_all_deals,
    get_deal_by_id,
    search_deals,
    count_deals,
    get_merchants,
)

# Initialize FastAPI app
app = FastAPI(
    title="kort.ing",
    description="Nederlandse kortingen en deals aggregator",
    version="1.0.0",
)

# Setup templates and static files
templates_dir = BASE_DIR / "frontend" / "templates"
static_dir = BASE_DIR / "frontend" / "static"

templates = Jinja2Templates(directory=str(templates_dir))
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


# No startup needed - using JSON file storage


# Template context helper
def get_base_context(request: Request):
    return {
        "request": request,
        "categories": CATEGORIES,
        "current_year": datetime.now().year,
    }


# Routes
@app.get("/", response_class=HTMLResponse)
async def homepage(
    request: Request,
    category: Optional[str] = None,
    sort: str = Query("newest", regex="^(newest|discount|expiring|price)$"),
    page: int = Query(1, ge=1),
):
    """Homepage with deal listings"""
    per_page = 24
    offset = (page - 1) * per_page

    # Map sort options to database fields
    sort_mapping = {
        "newest": ("created_at", "desc"),
        "discount": ("discount_percentage", "desc"),
        "expiring": ("valid_until", "asc"),
        "price": ("sale_price", "asc"),
    }
    sort_by, sort_order = sort_mapping.get(sort, ("created_at", "desc"))

    deals = get_all_deals(
        category=category,
        limit=per_page,
        offset=offset,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    total_deals = count_deals(category=category)
    total_pages = (total_deals + per_page - 1) // per_page

    context = get_base_context(request)
    context.update({
        "deals": deals,
        "current_category": category or "all",
        "current_sort": sort,
        "page": page,
        "total_pages": total_pages,
        "total_deals": total_deals,
    })

    return templates.TemplateResponse("index.html", context)


@app.get("/categorie/{category_slug}", response_class=HTMLResponse)
async def category_page(
    request: Request,
    category_slug: str,
    sort: str = Query("newest", regex="^(newest|discount|expiring|price)$"),
    page: int = Query(1, ge=1),
):
    """Category page"""
    # Redirect to homepage with category filter
    return RedirectResponse(f"/?category={category_slug}&sort={sort}&page={page}")


@app.get("/deal/{deal_id}", response_class=HTMLResponse)
async def deal_page(request: Request, deal_id: str):
    """Single deal page"""
    deal = get_deal_by_id(deal_id)
    if not deal:
        return RedirectResponse("/")

    # Get related deals from same category
    related = get_all_deals(category=deal.category, limit=4)
    related = [d for d in related if d.id != deal.id][:3]

    context = get_base_context(request)
    context.update({
        "deal": deal,
        "related_deals": related,
    })

    return templates.TemplateResponse("deal.html", context)


@app.get("/zoeken", response_class=HTMLResponse)
async def search_page(
    request: Request,
    q: str = Query("", min_length=0),
):
    """Search results page"""
    deals = []
    if q:
        deals = search_deals(q)

    context = get_base_context(request)
    context.update({
        "deals": deals,
        "query": q,
        "total_results": len(deals),
    })

    return templates.TemplateResponse("search.html", context)


@app.get("/go/{deal_id}")
async def affiliate_redirect(deal_id: str):
    """Redirect to affiliate link (tracks clicks)"""
    deal = get_deal_by_id(deal_id)
    if deal:
        # In production, you'd log this click for analytics
        # For now, just redirect to the affiliate URL
        # If it's a mock URL, redirect to the merchant
        if deal.affiliate_url.startswith("https://kort.ing"):
            # Mock URL - redirect to a placeholder
            return RedirectResponse(f"https://www.google.com/search?q={deal.merchant}+{deal.title}")
        return RedirectResponse(deal.affiliate_url)
    return RedirectResponse("/")


@app.get("/api/deals")
async def api_deals(
    category: Optional[str] = None,
    sort: str = "newest",
    limit: int = Query(24, le=100),
    offset: int = Query(0, ge=0),
):
    """API endpoint for deals (for AJAX loading)"""
    sort_mapping = {
        "newest": ("created_at", "desc"),
        "discount": ("discount_percentage", "desc"),
        "expiring": ("valid_until", "asc"),
        "price": ("sale_price", "asc"),
    }
    sort_by, sort_order = sort_mapping.get(sort, ("created_at", "desc"))

    deals = get_all_deals(
        category=category,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    return {
        "deals": [deal.to_dict() for deal in deals],
        "total": count_deals(category=category),
    }


@app.get("/api/merchants")
async def api_merchants():
    """API endpoint for merchant list"""
    return {"merchants": get_merchants()}


# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}
