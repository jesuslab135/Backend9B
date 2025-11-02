"""
Authentication Endpoints Testing
=================================
Tests for Login and Register endpoints with the new service layer architecture.

Design Pattern Validation:
- Service Layer Pattern: Business logic in services
- Factory Pattern: User creation via UserFactory
- Strategy Pattern: Authentication via AuthenticationService

Usage:
    python test_authentication.py
"""

import requests
import json
from typing import Dict


class AuthenticationTester:
    """Test suite for authentication endpoints."""
    
    def __init__(self, base_url: str = "http://localhost:8000/api"):
        """
        Initialize tester.
        
        Args:
            base_url: Base URL for API (default: http://localhost:8000/api)
        """
        self.base_url = base_url
        self.register_url = f"{base_url}/usuarios/register/"
        self.login_url = f"{base_url}/usuarios/login/"
        self.test_results = []
    
    def print_section(self, title: str):
        """Print formatted section header."""
        print("\n" + "="*60)
        print(f"  {title}")
        print("="*60)
    
    def print_test(self, name: str, passed: bool, details: str = ""):
        """Print test result."""
        status = "[✓]" if passed else "[✗]"
        print(f"\n{status} {name}")
        if details:
            print(f"    {details}")
        self.test_results.append((name, passed))
    
    def test_register_consumidor(self) -> Dict:
        """
        Test: Register a new consumidor.
        
        Expected: 201 Created with user_id, email, rol
        Note: Health fields (edad, peso, altura, genero) not included in registration
        """
        self.print_section("TEST 1: Register Consumidor")
        
        data = {
            "nombre": "Test Consumer",
            "email": "consumer123@test.com",
            "password": "Secur32ePass123",
            "telefono": "1234567890",
            "rol": "consumidor"
        }
        
        print("\nRequest:")
        print(f"POST {self.register_url}")
        print(json.dumps(data, indent=2))
        
        try:
            response = requests.post(self.register_url, json=data)
            print(f"\nResponse: {response.status_code}")
            response_data = response.json()
            print(json.dumps(response_data, indent=2))
            
            # Validation
            success = (
                response.status_code == 201 and
                'user_id' in response_data and
                response_data.get('rol') == 'consumidor'
            )
            
            self.print_test(
                "Register Consumidor",
                success,
                f"User ID: {response_data.get('user_id')}" if success else response_data.get('error', 'Unknown error')
            )
            
            return response_data
        
        except Exception as e:
            self.print_test("Register Consumidor", False, str(e))
            return {}
    
    def test_register_administrador(self) -> Dict:
        """
        Test: Register a new administrador.
        
        Expected: 201 Created with user_id, email, rol
        Note: No area_responsable field
        """
        self.print_section("TEST 2: Register Administrador")
        
        data = {
            "nombre": "Test Admin",
            "email": "admin321@test.com",
            "password": "Admin321Pass456",
            "telefono": "0987654321",
            "rol": "administrador"
        }
        
        print("\nRequest:")
        print(f"POST {self.register_url}")
        print(json.dumps(data, indent=2))
        
        try:
            response = requests.post(self.register_url, json=data)
            print(f"\nResponse: {response.status_code}")
            response_data = response.json()
            print(json.dumps(response_data, indent=2))
            
            # Validation
            success = (
                response.status_code == 201 and
                'user_id' in response_data and
                response_data.get('rol') == 'administrador'
            )
            
            self.print_test(
                "Register Administrador",
                success,
                f"User ID: {response_data.get('user_id')}" if success else response_data.get('error', 'Unknown error')
            )
            
            return response_data
        
        except Exception as e:
            self.print_test("Register Administrador", False, str(e))
            return {}
    
    def test_register_duplicate_email(self):
        """
        Test: Attempt to register with duplicate email.
        
        Expected: 400 Bad Request with validation error
        """
        self.print_section("TEST 3: Duplicate Email Validation")
        
        data = {
            "nombre": "Duplicate User",
            "email": "consumer123@test.com",  # Same as first test
            "password": "AnotherPass789",
            "rol": "consumidor"
        }
        
        print("\nRequest:")
        print(f"POST {self.register_url}")
        print(json.dumps(data, indent=2))
        
        try:
            response = requests.post(self.register_url, json=data)
            print(f"\nResponse: {response.status_code}")
            response_data = response.json()
            print(json.dumps(response_data, indent=2))
            
            # Validation: Should fail with 400
            success = response.status_code == 400
            
            self.print_test(
                "Duplicate Email Validation",
                success,
                "Correctly rejected duplicate email" if success else "Should have rejected duplicate"
            )
        
        except Exception as e:
            self.print_test("Duplicate Email Validation", False, str(e))
    
    def test_register_validation_errors(self):
        """
        Test: Register with invalid data (weak password).
        
        Expected: 400 Bad Request with validation errors
        """
        self.print_section("TEST 4: Field Validation")
        
        data = {
            "nombre": "Invalid User",
            "email": "invalid@test.com",
            "password": "123",  # Too short
            "rol": "consumidor"
        }
        
        print("\nRequest:")
        print(f"POST {self.register_url}")
        print(json.dumps(data, indent=2))
        
        try:
            response = requests.post(self.register_url, json=data)
            print(f"\nResponse: {response.status_code}")
            response_data = response.json()
            print(json.dumps(response_data, indent=2))
            
            # Validation: Should fail with 400
            success = response.status_code == 400
            
            self.print_test(
                "Field Validation",
                success,
                "Correctly rejected invalid fields" if success else "Should have rejected invalid data"
            )
        
        except Exception as e:
            self.print_test("Field Validation", False, str(e))
    
    def test_login_success(self):
        """
        Test: Login with valid credentials.
        
        Expected: 200 OK with user data
        Note: Consumidor fields (edad, peso, altura, genero, bmi) will be NULL 
              since they weren't provided during registration
        """
        self.print_section("TEST 5: Login Success")
        
        data = {
            "email": "consumer@test.com",
            "password": "SecurePass123"
        }
        
        print("\nRequest:")
        print(f"POST {self.login_url}")
        print(json.dumps(data, indent=2))
        
        try:
            response = requests.post(self.login_url, json=data)
            print(f"\nResponse: {response.status_code}")
            response_data = response.json()
            print(json.dumps(response_data, indent=2))
            
            # Validation
            success = (
                response.status_code == 200 and
                'user_id' in response_data and
                'consumidor_id' in response_data  # For consumidor
            )
            
            self.print_test(
                "Login Success",
                success,
                f"Logged in as: {response_data.get('nombre')}" if success else response_data.get('error', 'Unknown error')
            )
        
        except Exception as e:
            self.print_test("Login Success", False, str(e))
    
    def test_login_wrong_password(self):
        """
        Test: Login with wrong password.
        
        Expected: 401 Unauthorized
        """
        self.print_section("TEST 6: Wrong Password")
        
        data = {
            "email": "consumer@test.com",
            "password": "WrongPassword123"
        }
        
        print("\nRequest:")
        print(f"POST {self.login_url}")
        print(json.dumps(data, indent=2))
        
        try:
            response = requests.post(self.login_url, json=data)
            print(f"\nResponse: {response.status_code}")
            response_data = response.json()
            print(json.dumps(response_data, indent=2))
            
            # Validation: Should fail with 401
            success = response.status_code == 401
            
            self.print_test(
                "Wrong Password",
                success,
                "Correctly rejected wrong password" if success else "Should have rejected wrong password"
            )
        
        except Exception as e:
            self.print_test("Wrong Password", False, str(e))
    
    def test_login_user_not_found(self):
        """
        Test: Login with non-existent email.
        
        Expected: 401 Unauthorized
        """
        self.print_section("TEST 7: User Not Found")
        
        data = {
            "email": "nonexistent@test.com",
            "password": "AnyPassword123"
        }
        
        print("\nRequest:")
        print(f"POST {self.login_url}")
        print(json.dumps(data, indent=2))
        
        try:
            response = requests.post(self.login_url, json=data)
            print(f"\nResponse: {response.status_code}")
            response_data = response.json()
            print(json.dumps(response_data, indent=2))
            
            # Validation: Should fail with 401
            success = response.status_code == 401
            
            self.print_test(
                "User Not Found",
                success,
                "Correctly rejected non-existent user" if success else "Should have rejected non-existent user"
            )
        
        except Exception as e:
            self.print_test("User Not Found", False, str(e))
    
    def print_summary(self):
        """Print test summary."""
        self.print_section("TEST SUMMARY")
        
        total = len(self.test_results)
        passed = sum(1 for _, result in self.test_results if result)
        failed = total - passed
        
        print(f"\nTotal Tests: {total}")
        print(f"Passed: {passed} [✓]")
        print(f"Failed: {failed} [✗]")
        print(f"Success Rate: {(passed/total*100):.1f}%\n")
        
        if failed > 0:
            print("Failed Tests:")
            for name, result in self.test_results:
                if not result:
                    print(f"  - {name}")
    
    def run_all_tests(self):
        """Run complete test suite."""
        print("\n" + "█"*60)
        print("  AUTHENTICATION ENDPOINTS TEST SUITE")
        print("  Testing Service Layer Architecture")
        print("█"*60)
        
        # Registration tests
        self.test_register_consumidor()
        self.test_register_administrador()
        self.test_register_duplicate_email()
        self.test_register_validation_errors()
        
        # Login tests
        self.test_login_success()
        self.test_login_wrong_password()
        self.test_login_user_not_found()
        
        # Summary
        self.print_summary()


def main():
    """Main execution."""
    import sys
    
    # Check if custom URL provided
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000/api"
    
    print(f"\nBase URL: {base_url}")
    print("Make sure the Django server is running!")
    print("Run: python manage.py runserver\n")
    
    tester = AuthenticationTester(base_url)
    tester.run_all_tests()


if __name__ == "__main__":
    main()
