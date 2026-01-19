"""
Vercel serverless function entry point.
"""
from backend.main import app

# Vercel expects the app to be named 'app' or 'handler'
# FastAPI app is already named 'app' in backend/main.py
