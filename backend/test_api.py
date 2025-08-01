#!/usr/bin/env python3
"""
GrantThrive API Test Script
Comprehensive testing of authentication and grant management endpoints
"""
import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"

def test_authentication():
    """Test user authentication"""
    print("🔐 Testing Authentication...")
    
    # Test login
    login_data = {
        "email": "admin@grantthrive.com",
        "password": "securepassword123"
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/auth/login/json", json=login_data)
    if response.status_code == 200:
        token_data = response.json()
        print("✅ Login successful")
        return token_data["access_token"]
    else:
        print(f"❌ Login failed: {response.text}")
        return None

def test_grants(token):
    """Test grant management endpoints"""
    print("\n📋 Testing Grant Management...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test public grants list (should work without auth)
    response = requests.get(f"{BASE_URL}/api/v1/grants/")
    print(f"Public grants list: {response.status_code}")
    
    # Test featured grants
    response = requests.get(f"{BASE_URL}/api/v1/grants/featured")
    print(f"Featured grants: {response.status_code}")
    
    # Test open grants
    response = requests.get(f"{BASE_URL}/api/v1/grants/open")
    print(f"Open grants: {response.status_code}")
    
    # Create a grant (requires authentication)
    grant_data = {
        "title": "Community Development Grant 2025",
        "description": "Supporting local community development projects that enhance quality of life",
        "objectives": "Improve community infrastructure and social cohesion",
        "eligibility_criteria": "Registered community organizations and NFPs",
        "category": "community",
        "total_funding": 100000,
        "min_amount": 5000,
        "max_amount": 25000,
        "application_open_date": "2025-08-01T00:00:00",
        "application_close_date": "2025-09-30T23:59:59",
        "decision_date": "2025-10-31T00:00:00",
        "organization_id": 1,
        "organization_name": "Mount Isa Council",
        "contact_email": "grants@mountisa.qld.gov.au",
        "contact_person": "Grant Manager",
        "required_documents": ["Project proposal", "Budget breakdown", "Organization registration"]
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/grants/", json=grant_data, headers=headers)
    if response.status_code == 201:
        grant = response.json()
        print("✅ Grant created successfully")
        print(f"   Grant ID: {grant['id']}")
        print(f"   Grant Slug: {grant['slug']}")
        return grant["id"]
    else:
        print(f"❌ Grant creation failed: {response.text}")
        return None

def test_applications(token, grant_id):
    """Test application management endpoints"""
    print("\n📝 Testing Application Management...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    if not grant_id:
        print("❌ No grant ID available for application testing")
        return
    
    # Create an application
    application_data = {
        "project_title": "Community Garden Initiative",
        "project_description": "Establishing a community garden to promote sustainable living and community engagement",
        "requested_amount": 15000,
        "project_duration": "12 months",
        "organization_name": "Green Community Association",
        "abn_acn": "12345678901",
        "grant_id": grant_id,
        "form_data": {
            "project_location": "Central Park",
            "expected_participants": 50,
            "sustainability_plan": "Long-term community management"
        }
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/applications/", json=application_data, headers=headers)
    if response.status_code == 201:
        application = response.json()
        print("✅ Application created successfully")
        print(f"   Application ID: {application['id']}")
        print(f"   Reference Number: {application['reference_number']}")
        return application["id"]
    else:
        print(f"❌ Application creation failed: {response.text}")
        return None

def test_user_management(token):
    """Test user management endpoints"""
    print("\n👥 Testing User Management...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get current user info
    response = requests.get(f"{BASE_URL}/api/v1/auth/me", headers=headers)
    if response.status_code == 200:
        user = response.json()
        print("✅ Current user info retrieved")
        print(f"   User: {user['first_name']} {user['last_name']}")
        print(f"   Role: {user['role']}")
    else:
        print(f"❌ Failed to get user info: {response.text}")

def test_statistics(token):
    """Test statistics endpoints"""
    print("\n📊 Testing Statistics...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test grant statistics
    response = requests.get(f"{BASE_URL}/api/v1/grants/stats/summary", headers=headers)
    if response.status_code == 200:
        stats = response.json()
        print("✅ Grant statistics retrieved")
        print(f"   Total grants: {stats.get('total_grants', 0)}")
    else:
        print(f"❌ Failed to get grant stats: {response.text}")
    
    # Test application statistics
    response = requests.get(f"{BASE_URL}/api/v1/applications/stats/summary", headers=headers)
    if response.status_code == 200:
        stats = response.json()
        print("✅ Application statistics retrieved")
        print(f"   Total applications: {stats.get('total_applications', 0)}")
    else:
        print(f"❌ Failed to get application stats: {response.text}")

def main():
    """Run all API tests"""
    print("🚀 Starting GrantThrive API Tests\n")
    
    # Test authentication
    token = test_authentication()
    if not token:
        print("❌ Authentication failed - stopping tests")
        return
    
    # Test grant management
    grant_id = test_grants(token)
    
    # Test application management
    application_id = test_applications(token, grant_id)
    
    # Test user management
    test_user_management(token)
    
    # Test statistics
    test_statistics(token)
    
    print("\n🎉 API Tests Completed!")

if __name__ == "__main__":
    main()

