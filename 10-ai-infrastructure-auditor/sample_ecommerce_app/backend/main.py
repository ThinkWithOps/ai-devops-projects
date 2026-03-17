"""
ShopAI — Sample FastAPI Backend
Minimal demo backend for the AI Infrastructure Auditor sample workspace.
"""
from fastapi import FastAPI

app = FastAPI(title="ShopAI Backend", version="0.1.0")

PRODUCTS = [
    {"id": 1, "name": "Wireless Headphones", "price": 79.99, "category": "Electronics"},
    {"id": 2, "name": "Running Shoes", "price": 129.99, "category": "Footwear"},
    {"id": 3, "name": "Coffee Maker", "price": 49.99, "category": "Kitchen"},
    {"id": 4, "name": "Yoga Mat", "price": 34.99, "category": "Sports"},
    {"id": 5, "name": "Backpack", "price": 59.99, "category": "Accessories"},
]


@app.get("/products")
def list_products():
    """Return all available products."""
    return {"products": PRODUCTS, "total": len(PRODUCTS)}


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok"}
