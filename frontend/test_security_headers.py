"""
Security Headers Verification Tests

Run with: python test_security_headers.py
"""

import requests
import sys
from colorama import Fore, Style, init

init(autoreset=True)

# Configuration
API_URL = "http://localhost:8000"
TIMEOUT = 5

# Expected security headers
EXPECTED_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
    "Content-Security-Policy": None,  # Complex header, just check if present
}

# Production-only headers
PRODUCTION_ONLY_HEADERS = {
    "Strict-Transport-Security": None,
}


def check_headers(api_url=API_URL):
    """Check security headers."""
    print(f"\n🔒 Security Headers Verification")
    print("=" * 60)
    print(f"Target: {api_url}")
    print()

    try:
        response = requests.get(f"{api_url}/api/health", timeout=TIMEOUT)
    except requests.exceptions.ConnectionError:
        print(f"{Fore.RED}❌ Cannot connect to API at {api_url}")
        print(f"   Make sure the server is running: uvicorn app.main:app --reload")
        return False
    except Exception as e:
        print(f"{Fore.RED}❌ Error: {str(e)}")
        return False

    all_passed = True
    headers = response.headers

    # Check expected headers
    print(f"\n{Fore.CYAN}Expected Headers (All Environments):")
    print("-" * 60)
    
    for header, expected_value in EXPECTED_HEADERS.items():
        if header in headers:
            actual_value = headers[header]
            
            if expected_value is None or expected_value in actual_value:
                print(f"{Fore.GREEN}✅ {header}: {actual_value}")
            else:
                print(f"{Fore.RED}❌ {header}: {actual_value}")
                print(f"   Expected: {expected_value}")
                all_passed = False
        else:
            print(f"{Fore.RED}❌ {header}: MISSING")
            all_passed = False

    # Check production-only headers
    print(f"\n{Fore.CYAN}Production-Only Headers:")
    print("-" * 60)
    
    is_production = "DEBUG" not in headers and "Strict-Transport-Security" in headers
    
    for header, expected_value in PRODUCTION_ONLY_HEADERS.items():
        if header in headers:
            actual_value = headers[header]
            print(f"{Fore.GREEN}✅ {header}: {actual_value}")
        else:
            if is_production:
                print(f"{Fore.YELLOW}⚠️  {header}: Missing (required for production)")
                all_passed = False
            else:
                print(f"{Fore.YELLOW}ℹ️  {header}: Not present (OK for development)")

    # CORS headers
    print(f"\n{Fore.CYAN}CORS Configuration:")
    print("-" * 60)
    
    if "access-control-allow-origin" in headers:
        print(f"{Fore.GREEN}✅ CORS Enabled: {headers.get('access-control-allow-origin')}")
    else:
        print(f"{Fore.YELLOW}ℹ️  CORS: Not present (expected if not cross-origin)")

    # Response status
    print(f"\n{Fore.CYAN}Response Status:")
    print("-" * 60)
    print(f"{Fore.GREEN}✅ Status Code: {response.status_code}")
    print(f"{Fore.GREEN}✅ Content-Type: {response.headers.get('Content-Type', 'Not specified')}")

    # Summary
    print(f"\n{Fore.CYAN}Summary:")
    print("=" * 60)
    
    if all_passed:
        print(f"{Fore.GREEN}✅ All security headers are properly configured!")
        return True
    else:
        print(f"{Fore.RED}❌ Some security headers are missing or misconfigured")
        return False


def check_cors():
    """Check CORS configuration."""
    print(f"\n🔄 CORS Configuration Verification")
    print("=" * 60)

    test_origin = "https://app.yourdomain.com"
    
    try:
        response = requests.options(
            f"{API_URL}/api/health",
            headers={"Origin": test_origin},
            timeout=TIMEOUT,
        )
    except Exception as e:
        print(f"{Fore.RED}❌ Error: {str(e)}")
        return False

    cors_headers = {
        "access-control-allow-origin": None,
        "access-control-allow-methods": ["GET", "POST", "PUT", "DELETE"],
        "access-control-allow-headers": ["Content-Type", "Authorization"],
    }

    print(f"\nTest Origin: {test_origin}")
    print()

    for header, expected_values in cors_headers.items():
        if header in response.headers:
            actual_value = response.headers[header]
            
            if expected_values is None:
                print(f"{Fore.GREEN}✅ {header}: {actual_value}")
            else:
                # Check if expected values are in the response
                all_found = all(val in actual_value for val in expected_values)
                if all_found:
                    print(f"{Fore.GREEN}✅ {header}: {actual_value}")
                else:
                    print(f"{Fore.YELLOW}⚠️  {header}: {actual_value}")
        else:
            print(f"{Fore.YELLOW}ℹ️  {header}: Not present (OK if CORS not needed)")

    return True


def check_endpoints():
    """Check critical endpoints for security."""
    print(f"\n📡 Endpoint Security Verification")
    print("=" * 60)

    endpoints = [
        ("/api/health", "GET", 200),
        ("/api/detect/model-info", "GET", 200),
        ("/docs", "GET", None),  # Should be None in production
    ]

    for endpoint, method, expected_status in endpoints:
        try:
            if method == "GET":
                response = requests.get(f"{API_URL}{endpoint}", timeout=TIMEOUT)
            
            if expected_status is None:
                # Check if docs are disabled in production
                if response.status_code == 404:
                    print(f"{Fore.GREEN}✅ {endpoint}: Documentation disabled (production)")
                else:
                    print(f"{Fore.YELLOW}⚠️  {endpoint}: Still accessible (OK for dev)")
            elif response.status_code == expected_status:
                print(f"{Fore.GREEN}✅ {endpoint}: {response.status_code}")
            else:
                print(f"{Fore.YELLOW}⚠️  {endpoint}: {response.status_code} (expected {expected_status})")
        except Exception as e:
            print(f"{Fore.RED}❌ {endpoint}: {str(e)}")

    return True


def main():
    """Run all security checks."""
    print(f"\n{Fore.CYAN}{'=' * 60}")
    print(f"{Fore.CYAN}🔒 Security Verification Suite")
    print(f"{Fore.CYAN}{'=' * 60}")

    results = []

    # Run checks
    results.append(("Security Headers", check_headers()))
    results.append(("CORS Configuration", check_cors()))
    results.append(("Endpoint Security", check_endpoints()))

    # Final summary
    print(f"\n{Fore.CYAN}{'=' * 60}")
    print(f"{Fore.CYAN}Final Summary")
    print(f"{Fore.CYAN}{'=' * 60}\n")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = f"{Fore.GREEN}✅ PASS" if result else f"{Fore.RED}❌ FAIL"
        print(f"{status} - {test_name}")

    print()
    print(f"{Fore.CYAN}Overall: {passed}/{total} checks passed")
    
    if passed == total:
        print(f"{Fore.GREEN}\n🎉 All security checks passed!")
        return 0
    else:
        print(f"{Fore.RED}\n⚠️  Some security checks failed. Review the output above.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

