import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_app_import():
    """Test that the main app can be imported successfully"""
    from main import app
    assert app is not None

def test_database_import():
    """Test that database module can be imported"""
    from database import db
    assert db is not None

def test_app_has_routes():
    """Test that app has routes configured"""
    from main import app
    assert len(app.routes) > 0

def test_basic_functionality():
    """Basic test to verify core functionality"""
    from main import get_current_user, sessions
    from fastapi import Request
    
    # Test session management
    assert isinstance(sessions, dict)
    
    # Test that functions exist
    assert callable(get_current_user)

def test_intentional_failure():
    """Test to verify CI/CD catches failures"""
    # This will fail to test CI/CD error handling
    assert False, "Intentional test failure to verify CI/CD pipeline"