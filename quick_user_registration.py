#!/usr/bin/env python3
"""
Quick User Registration Script for UniNest
Simple script to register a batch of predefined users quickly for testing.
"""

import requests
import json
import time
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_BASE_URL = os.getenv('VITE_API_BASE_URL', 'http://localhost:8000')
REGISTRATION_ENDPOINT = f"{API_BASE_URL}/api/v1/auth/register"

# Predefined test users
TEST_USERS = [
    # Tenant users
    {
        "email": "alice.chen@cmu.edu",
        "username": "alicechen",
        "password": "StudentPass123!",
        "confirm_password": "StudentPass123!",
        "user_type": "tenant"
    },
    {
        "email": "bob.martinez@gmail.com",
        "username": "bobmartinez",
        "password": "StudentPass123!",
        "confirm_password": "StudentPass123!",
        "user_type": "tenant"
    },
    {
        "email": "carol.wang@andrew.cmu.edu",
        "username": "carolwang",
        "password": "StudentPass123!",
        "confirm_password": "StudentPass123!",
        "user_type": "tenant"
    },
    {
        "email": "david.kim@cmu.edu",
        "username": "davidkim",
        "password": "StudentPass123!",
        "confirm_password": "StudentPass123!",
        "user_type": "tenant"
    },
    {
        "email": "emma.johnson@gmail.com",
        "username": "emmajohnson",
        "password": "StudentPass123!",
        "confirm_password": "StudentPass123!",
        "user_type": "tenant"
    },
    
    # Landlord users
    {
        "email": "john.smith@properties.com",
        "username": "johnsmith_realty",
        "password": "LandlordPass123!",
        "confirm_password": "LandlordPass123!",
        "user_type": "landlord"
    },
    {
        "email": "sarah.wilson@realty.com",
        "username": "sarahwilson_pm",
        "password": "LandlordPass123!",
        "confirm_password": "LandlordPass123!",
        "user_type": "landlord"
    },
    {
        "email": "mike.brown@company.com",
        "username": "mikebrown_properties",
        "password": "LandlordPass123!",
        "confirm_password": "LandlordPass123!",
        "user_type": "landlord"
    },
]

def register_user(user_data):
    """Register a single user"""
    try:
        response = requests.post(
            REGISTRATION_ENDPOINT,
            json=user_data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 200:
            return {'success': True, 'data': response.json()}
        else:
            return {'success': False, 'error': response.text, 'status': response.status_code}
            
    except Exception as e:
        return {'success': False, 'error': str(e)}

def main():
    print("=== Quick User Registration for UniNest ===")
    print(f"API Endpoint: {REGISTRATION_ENDPOINT}")
    print(f"Total users to register: {len(TEST_USERS)}\n")
    
    # Test connection first
    try:
        health_response = requests.get(f"{API_BASE_URL}/", timeout=10)
        if health_response.status_code == 200:
            print("✓ Backend is responding")
        else:
            print("⚠ Backend responded with non-200 status")
    except Exception as e:
        print(f"✗ Cannot connect to backend: {e}")
        return
    
    successful = 0
    failed = 0
    results = []
    
    for i, user in enumerate(TEST_USERS):
        print(f"Registering {i+1}/{len(TEST_USERS)}: {user['email']} ({user['user_type']})")
        
        result = register_user(user)
        results.append({
            'email': user['email'],
            'user_type': user['user_type'],
            'success': result['success'],
            'error': result.get('error') if not result['success'] else None
        })
        
        if result['success']:
            successful += 1
            print(f"  ✓ Success")
        else:
            failed += 1
            print(f"  ✗ Failed: {result['error']}")
        
        # Small delay to avoid overwhelming the server
        time.sleep(0.5)
    
    print(f"\n=== Registration Summary ===")
    print(f"Total: {len(TEST_USERS)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Success rate: {(successful/len(TEST_USERS)*100):.1f}%")
    
    # Save results
    with open('quick_registration_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n✓ Results saved to quick_registration_results.json")
    
    # Show failed registrations
    failed_users = [r for r in results if not r['success']]
    if failed_users:
        print(f"\nFailed registrations:")
        for user in failed_users:
            print(f"- {user['email']}: {user['error']}")

if __name__ == "__main__":
    main()