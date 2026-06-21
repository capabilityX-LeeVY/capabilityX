"""
API module for FastAPI server and routes
"""
from .server import app, create_app
from .routes import router

__all__ = ['app', 'create_app', 'router']
