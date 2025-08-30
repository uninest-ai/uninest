#!/usr/bin/env python3
"""
Test User Registration Script for UniNest
Simple script to register test users without external dependencies.
"""

import json
import time
import urllib.request
import urllib.parse
import urllib.error

# Configuration - Update these based on your setup
API_BASE_URL = 'http://3.145.189.113:8000'  # Using production server
REGISTRATION_ENDPOINT = f"{API_BASE_URL}/api/v1/auth/register"

# Test users data
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
    """Register a single user using urllib"""
    try:
        # Prepare the data
        data = json.dumps(user_data).encode('utf-8')
        
        # Create the request
        req = urllib.request.Request(
            REGISTRATION_ENDPOINT,
            data=data,
            headers={
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
        )
        
        # Make the request
        with urllib.request.urlopen(req, timeout=30) as response:
            response_data = response.read().decode('utf-8')
            return {
                'success': True,
                'data': json.loads(response_data),
                'status_code': response.getcode()
            }
            
    except urllib.error.HTTPError as e:
        error_data = e.read().decode('utf-8')
        return {
            'success': False,
            'error': error_data,
            'status_code': e.code
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'status_code': None
        }

def test_connection():
    """Test if the backend is reachable"""
    try:
        with urllib.request.urlopen(f"{API_BASE_URL}/", timeout=10) as response:
            return response.getcode() == 200
    except:
        return False

def main():
    print("=== UniNest Test User Registration ===")
    print(f"Backend URL: {API_BASE_URL}")
    print(f"Registration Endpoint: {REGISTRATION_ENDPOINT}")
    print(f"Total users to register: {len(TEST_USERS)}\n")
    
    # Test connection
    print("Testing backend connection...")
    if test_connection():
        print("✓ Backend is reachable\n")
    else:
        print("✗ Cannot reach backend. Please check:")
        print("  1. Backend is running")
        print("  2. API_BASE_URL is correct")
        print("  3. No firewall blocking the connection\n")
        return
    
    successful = 0
    failed = 0
    results = []
    
    print("Starting user registration...\n")
    
    for i, user in enumerate(TEST_USERS):
        print(f"[{i+1}/{len(TEST_USERS)}] Registering: {user['email']} ({user['user_type']})")
        
        result = register_user(user)
        
        result_summary = {
            'email': user['email'],
            'username': user['username'],
            'user_type': user['user_type'],
            'success': result['success'],
            'status_code': result.get('status_code'),
            'error': result.get('error') if not result['success'] else None
        }
        results.append(result_summary)
        
        if result['success']:
            successful += 1
            user_id = result['data'].get('id', 'N/A')
            print(f"  ✓ Success (User ID: {user_id})")
        else:
            failed += 1
            error_msg = result['error']
            if result['status_code'] == 400 and 'already registered' in error_msg:
                print(f"  ⚠ User already exists")
            else:
                print(f"  ✗ Failed: {error_msg}")
        
        # Small delay between registrations
        time.sleep(0.5)
    
    # Print summary
    print(f"\n{'='*50}")
    print(f"REGISTRATION SUMMARY")
    print(f"{'='*50}")
    print(f"Total users processed: {len(TEST_USERS)}")
    print(f"Successfully registered: {successful}")
    print(f"Failed registrations: {failed}")
    print(f"Success rate: {(successful/len(TEST_USERS)*100):.1f}%")
    
    # Show tenant/landlord breakdown
    tenant_success = sum(1 for r in results if r['success'] and r['user_type'] == 'tenant')
    landlord_success = sum(1 for r in results if r['success'] and r['user_type'] == 'landlord')
    print(f"Tenants registered: {tenant_success}")
    print(f"Landlords registered: {landlord_success}")
    
    # Save detailed results
    results_file = 'user_registration_results.json'
    with open(results_file, 'w') as f:
        json.dump({
            'summary': {
                'total': len(TEST_USERS),
                'successful': successful,
                'failed': failed,
                'success_rate': (successful/len(TEST_USERS)*100)
            },
            'results': results
        }, f, indent=2)
    
    print(f"\n✓ Detailed results saved to: {results_file}")
    
    # Show any failures
    failed_registrations = [r for r in results if not r['success']]
    if failed_registrations:
        print(f"\nFAILED REGISTRATIONS:")
        for failure in failed_registrations:
            print(f"- {failure['email']}: {failure['error']}")
    
    print(f"\n🎉 Registration process completed!")

if __name__ == "__main__":
    main()