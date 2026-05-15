import requests
import sys
import os
from datetime import datetime
import json

class ConsultantWebsiteAPITester:
    def __init__(self, base_url=None):
        if base_url is None:
            base_url = os.environ.get('BACKEND_URL', os.environ.get('REACT_APP_BACKEND_URL', 'http://localhost:8001')).rstrip('/')
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, response_data=None, error=None):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
        
        result = {
            "name": name,
            "success": success,
            "error": str(error) if error else None,
            "response_data": response_data
        }
        self.test_results.append(result)
        print(f"{status} - {name}")
        if error:
            print(f"    Error: {error}")

    def run_test(self, name, method, endpoint, expected_status=200, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        request_headers = {'Content-Type': 'application/json'}
        
        if self.token:
            request_headers['Authorization'] = f'Bearer {self.token}'
        
        if headers:
            request_headers.update(headers)

        try:
            if method == 'GET':
                response = requests.get(url, headers=request_headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=request_headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=request_headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=request_headers, timeout=10)

            success = response.status_code == expected_status
            response_data = None
            
            try:
                response_data = response.json()
            except:
                response_data = response.text[:200] if response.text else None

            if success:
                self.log_test(name, True, response_data)
                return True, response_data
            else:
                self.log_test(name, False, response_data, f"Expected {expected_status}, got {response.status_code}")
                return False, response_data

        except Exception as e:
            self.log_test(name, False, None, str(e))
            return False, {}

    def test_public_endpoints(self):
        """Test all public endpoints"""
        print("\n🔍 Testing Public Endpoints...")
        
        # Test all public API endpoints
        endpoints = [
            ("Public Settings", "public/settings"),
            ("Public Hero", "public/hero"),
            ("Public About", "public/about"),
            ("Public Services", "public/services"),
            ("Public Blog", "public/blog"),
            ("Public Books", "public/books"),
            ("Public Maps", "public/maps"),
            ("Public Map Locations", "public/map-locations"),
            ("Public Gallery", "public/gallery"),
            ("Public Portfolio", "public/portfolio"),
            ("Public Testimonials", "public/testimonials"),
            ("Public Sections", "public/sections")
        ]
        
        for name, endpoint in endpoints:
            self.run_test(name, "GET", endpoint)

        # Test specific blog post
        self.run_test("Public Blog Detail", "GET", "public/blog/future-of-business-consulting")

    def test_authentication(self):
        """Test authentication endpoints"""
        print("\n🔐 Testing Authentication...")
        
        # Test login with correct credentials
        login_data = {
            "email": "admin@consultant.com",
            "password": "Admin123!"
        }
        
        success, response = self.run_test("Admin Login", "POST", "auth/login", 200, login_data)
        if success and 'token' in response:
            self.token = response['token']
            print(f"    ✅ Token obtained: {self.token[:20]}...")
        else:
            print("    ❌ Failed to get authentication token")
            return False

        # Test /auth/me with token
        self.run_test("Auth Me", "GET", "auth/me")

        # Test invalid login
        invalid_login = {
            "email": "wrong@email.com",
            "password": "wrongpassword"
        }
        self.run_test("Invalid Login", "POST", "auth/login", 401, invalid_login)
        
        return True

    def test_contact_form(self):
        """Test contact form submission"""
        print("\n📧 Testing Contact Form...")
        
        contact_data = {
            "name": "Test User",
            "email": "test@example.com",
            "phone": "+1234567890",
            "subject": "Test Message",
            "message": "This is a test message from automated testing"
        }
        
        self.run_test("Contact Form Submission", "POST", "contact", 200, contact_data)

    def test_admin_endpoints(self):
        """Test admin endpoints (requires authentication)"""
        print("\n🔒 Testing Admin Endpoints...")
        
        if not self.token:
            print("❌ No authentication token available, skipping admin tests")
            return

        # Test admin dashboard
        self.run_test("Admin Dashboard", "GET", "admin/dashboard")
        
        # Test admin data retrieval
        admin_endpoints = [
            ("Admin Hero", "admin/hero"),
            ("Admin About", "admin/about"), 
            ("Admin Services", "admin/services"),
            ("Admin Blog", "admin/blog"),
            ("Admin Books", "admin/books"),
            ("Admin Maps", "admin/maps"),
            ("Admin Map Locations", "admin/map-locations"),
            ("Admin Gallery", "admin/gallery"),
            ("Admin Portfolio", "admin/portfolio"),
            ("Admin Testimonials", "admin/testimonials"),
            ("Admin Contacts", "admin/contacts"),
            ("Admin Purchases", "admin/purchases"),
            ("Admin Settings", "admin/settings")
        ]
        
        for name, endpoint in admin_endpoints:
            self.run_test(name, "GET", endpoint)

    def test_stripe_checkout_creation(self):
        """Test Stripe checkout creation (should work with test key)"""
        print("\n💳 Testing Stripe Checkout...")
        
        # First get services to find a valid service_id
        success, services_response = self.run_test("Get Services for Checkout", "GET", "public/services")
        
        if success and services_response and len(services_response) > 0:
            service_id = services_response[0].get('id')
            if service_id:
                checkout_data = {
                    "service_id": service_id,
                    "origin_url": self.base_url
                }
                self.run_test("Create Checkout Session", "POST", "checkout", 200, checkout_data)
        else:
            print("    ⚠️  No services available for checkout test")

    def test_pages(self):
        """Test static pages endpoints"""
        print("\n📄 Testing Static Pages...")
        
        pages = ["terms", "privacy"]
        for page in pages:
            self.run_test(f"Public Page - {page}", "GET", f"public/page/{page}")

    def run_all_tests(self):
        """Run all test suites"""
        print(f"🚀 Starting API Tests for Legacy Consultant Website")
        print(f"📍 Base URL: {self.base_url}")
        print(f"📍 API URL: {self.api_url}")
        print("=" * 70)

        # Run test suites
        self.test_public_endpoints()
        auth_success = self.test_authentication()
        self.test_contact_form()
        
        if auth_success:
            self.test_admin_endpoints()
        
        self.test_stripe_checkout_creation()
        self.test_pages()

        # Print summary
        print("\n" + "=" * 70)
        print(f"📊 TEST SUMMARY")
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed / self.tests_run * 100):.1f}%" if self.tests_run > 0 else "0%")
        
        # List failed tests
        failed_tests = [test for test in self.test_results if not test['success']]
        if failed_tests:
            print(f"\n❌ Failed Tests:")
            for test in failed_tests:
                print(f"  - {test['name']}: {test['error']}")
        else:
            print(f"\n🎉 All tests passed!")

        return self.tests_passed, self.tests_run, failed_tests

def main():
    tester = ConsultantWebsiteAPITester()
    passed, total, failed = tester.run_all_tests()
    
    # Return appropriate exit code
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())