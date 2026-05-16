#!/usr/bin/env python3
"""
System verification script for Object Detection system.
Tests all components to ensure production readiness.
"""

import os
import sys
import subprocess
import time
import requests
import json
from pathlib import Path

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def print_test(name: str, passed: bool, message: str = ""):
    """Print test result."""
    status = f"{Colors.GREEN}✅{Colors.RESET}" if passed else f"{Colors.RED}❌{Colors.RESET}"
    msg = f" - {message}" if message else ""
    print(f"{status} {name}{msg}")

def print_section(title: str):
    """Print section header."""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BLUE}{title:^60}{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*60}{Colors.RESET}\n")

def test_dependencies():
    """Test that all required packages are installed."""
    print_section("DEPENDENCY CHECK")
    
    required_packages = [
        'fastapi', 'uvicorn', 'gradio', 'cv2', 'torch', 'ultralytics',
        'sqlalchemy', 'pydantic', 'requests', 'numpy', 'pandas', 'plotly'
    ]
    
    all_installed = True
    for package in required_packages:
        try:
            __import__(package)
            print_test(f"Package: {package}", True)
        except ImportError:
            print_test(f"Package: {package}", False, "NOT INSTALLED")
            all_installed = False
    
    return all_installed

def test_environment():
    """Test environment configuration."""
    print_section("ENVIRONMENT CHECK")
    
    env_vars = {
        'DATABASE_URL': 'Database connection string',
        'API_PORT': '8000',
        'GRADIO_PORT': '7860',
        'DEVICE': '0 or cpu',
    }
    
    all_configured = True
    for var, description in env_vars.items():
        value = os.getenv(var, 'NOT SET')
        is_set = value != 'NOT SET'
        print_test(f"Env: {var}", is_set, f"({value[:30]}...)" if is_set else "")
        if not is_set and var != 'DEVICE':
            all_configured = False
    
    return all_configured

def test_database():
    """Test database connection."""
    print_section("DATABASE CONNECTION")
    
    try:
        from backend.app.core.config import settings
        from backend.app.core.database import test_db_connection
        
        is_connected = test_db_connection()
        print_test("Database Connection", is_connected)
        
        if is_connected:
            print_test("Database URL", True, settings.DATABASE_URL[:50])
        
        return is_connected
    except Exception as e:
        print_test("Database Check", False, str(e)[:50])
        return False

def test_yolo_model():
    """Test YOLOv8 model loading."""
    print_section("YOLO MODEL CHECK")
    
    try:
        from backend.app.services.yolo_service import YOLOv8Service
        
        print("Loading YOLOv8 model... (this may take a minute on first run)")
        service = YOLOv8Service()
        
        if service._model is not None:
            print_test("Model Loading", True)
            
            info = service.get_model_info()
            if info.get('status') == 'ready':
                print_test("Model Status", True, "Ready")
                print_test(f"  - Classes: {info.get('num_classes', 0)}", True)
                print_test(f"  - Device: {info.get('device', 'unknown')}", True)
            else:
                print_test("Model Status", False, info.get('status', 'unknown'))
            
            return True
        else:
            print_test("Model Loading", False)
            return False
    except Exception as e:
        print_test("Model Loading", False, str(e)[:50])
        return False

def test_api_health(api_url: str = "http://localhost:8000"):
    """Test API health check."""
    print_section("API HEALTH CHECK")
    
    # Give server time to start
    time.sleep(1)
    
    endpoints = [
        ("/", "Root Endpoint"),
        ("/status", "Status Endpoint"),
        ("/docs", "API Documentation"),
    ]
    
    all_healthy = True
    for endpoint, description in endpoints:
        try:
            response = requests.get(f"{api_url}{endpoint}", timeout=5)
            is_ok = response.status_code == 200
            print_test(f"API{endpoint}", is_ok, f"({response.status_code})")
            all_healthy = all_healthy and is_ok
        except requests.exceptions.ConnectionError:
            print_test(f"API{endpoint}", False, "Backend not running")
            all_healthy = False
        except Exception as e:
            print_test(f"API{endpoint}", False, str(e)[:30])
            all_healthy = False
    
    return all_healthy

def test_gradio_health(gradio_url: str = "http://localhost:7860"):
    """Test Gradio frontend health."""
    print_section("GRADIO FRONTEND CHECK")
    
    try:
        response = requests.get(gradio_url, timeout=5)
        is_ok = response.status_code == 200
        print_test("Gradio Frontend", is_ok, f"({response.status_code})")
        return is_ok
    except requests.exceptions.ConnectionError:
        print_test("Gradio Frontend", False, "Not running at :7860")
        return False
    except Exception as e:
        print_test("Gradio Frontend", False, str(e)[:30])
        return False

def test_file_structure():
    """Test that all required files exist."""
    print_section("FILE STRUCTURE CHECK")
    
    required_files = [
        "backend/app/main.py",
        "backend/app/core/config.py",
        "backend/app/core/database.py",
        "backend/app/services/yolo_service.py",
        "backend/app/models/models.py",
        "backend/app/routers/detect.py",
        "frontend-gradio/app.py",
        "requirements.txt",
        ".env.example",
        "README.md",
    ]
    
    all_exist = True
    for file_path in required_files:
        exists = Path(file_path).exists()
        print_test(f"File: {file_path}", exists)
        all_exist = all_exist and exists
    
    return all_exist

def main():
    """Run all system tests."""
    print(f"\n{Colors.BLUE}🧪 OBJECT DETECTION SYSTEM VERIFICATION{Colors.RESET}\n")
    
    results = {
        "Dependencies": test_dependencies(),
        "Environment": test_environment(),
        "File Structure": test_file_structure(),
        "Database": test_database(),
        "YOLO Model": test_yolo_model(),
    }
    
    # Test running services (optional)
    print_section("RUNNING SERVICES CHECK (Optional)")
    print(f"{Colors.YELLOW}Note: These tests require services to be running{Colors.RESET}\n")
    
    try:
        api_health = test_api_health()
        results["API Health"] = api_health
    except:
        print(f"{Colors.YELLOW}Skipping API check - backend may not be running{Colors.RESET}")
    
    try:
        gradio_health = test_gradio_health()
        results["Gradio Health"] = gradio_health
    except:
        print(f"{Colors.YELLOW}Skipping Gradio check - frontend may not be running{Colors.RESET}")
    
    # Summary
    print_section("SUMMARY")
    
    for test_name, result in results.items():
        status = f"{Colors.GREEN}✅{Colors.RESET}" if result else f"{Colors.RED}❌{Colors.RESET}"
        print(f"{status} {test_name}: {'PASS' if result else 'FAIL'}")
    
    total_tests = len([r for r in results.values() if r is not None])
    passed_tests = sum(1 for r in results.values() if r is True)
    
    print(f"\n{Colors.BLUE}Results: {passed_tests}/{total_tests} tests passed{Colors.RESET}\n")
    
    if passed_tests == total_tests:
        print(f"{Colors.GREEN}✅ System is ready for operation!{Colors.RESET}\n")
        
        print("Next steps:")
        print("1. Start the backend:")
        print("   python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000")
        print("\n2. In another terminal, start the frontend:")
        print("   python frontend-gradio/app.py")
        print("\n3. Open your browser to http://localhost:7860\n")
    else:
        print(f"{Colors.RED}❌ System has issues that need attention{Colors.RESET}\n")
        print("Please check the failed tests above and refer to PRODUCTION_HARDENING.md\n")
    
    return 0 if passed_tests == total_tests else 1

if __name__ == "__main__":
    sys.exit(main())
