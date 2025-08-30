#!/usr/bin/env python3
"""
Test User Login Script
Verify that registered users can successfully log in to the UniNest platform.
"""

import json
import urllib.request
import urllib.parse
import urllib.error

API_BASE_URL = 'http://3.145.189.113:8000'
LOGIN_ENDPOINT = f"{API_BASE_URL}/api/v1/auth/login"

# Test credentials from registration
TEST_CREDENTIALS = [
    {"email": "alice.chen@cmu.edu", "password": "StudentPass123!", "type": "tenant"},
    {"email": "bob.martinez@gmail.com", "password": "StudentPass123!", "type": "tenant"},
    {"email": "john.smith@properties.com", "password": "LandlordPass123!", "type": "landlord"},
    {"email": "sarah.wilson@realty.com", "password": "LandlordPass123!", "type": "landlord"},
]

def test_login(email, password):
    """Test login for a user"""
    try:
        # Prepare form data
        data = urllib.parse.urlencode({
            'username': email,  # FastAPI OAuth2 uses 'username' field
            'password': password
        }).encode('utf-8')
        
        # Create request
        req = urllib.request.Request(
            LOGIN_ENDPOINT,
            data=data,
            headers={
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json'
            }
        )
        
        # Make request
        with urllib.request.urlopen(req, timeout=30) as response:
            response_data = response.read().decode('utf-8')
            result = json.loads(response_data)
            return {
                'success': True,
                'access_token': result.get('access_token'),
                'token_type': result.get('token_type'),
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

def main():
    print("=== UniNest User Login Test ===")
    print(f"Login Endpoint: {LOGIN_ENDPOINT}")
    print(f"Testing {len(TEST_CREDENTIALS)} users...\n")
    
    successful_logins = 0
    failed_logins = 0
    results = []
    
    for i, cred in enumerate(TEST_CREDENTIALS):
        print(f"[{i+1}/{len(TEST_CREDENTIALS)}] Testing login: {cred['email']} ({cred['type']})")
        
        result = test_login(cred['email'], cred['password'])
        
        result_summary = {
            'email': cred['email'],
            'user_type': cred['type'],
            'success': result['success'],
            'status_code': result.get('status_code'),
            'has_token': bool(result.get('access_token')) if result['success'] else False,
            'error': result.get('error') if not result['success'] else None
        }
        results.append(result_summary)
        
        if result['success']:
            successful_logins += 1
            token_preview = result['access_token'][:20] + "..." if result.get('access_token') else "None"
            print(f"  ✓ Login successful - Token: {token_preview}")
        else:
            failed_logins += 1
            print(f"  ✗ Login failed: {result['error']}")
    
    # Print summary
    print(f"\n{'='*50}")
    print(f"LOGIN TEST SUMMARY")
    print(f"{'='*50}")
    print(f"Total logins tested: {len(TEST_CREDENTIALS)}")
    print(f"Successful logins: {successful_logins}")
    print(f"Failed logins: {failed_logins}")
    print(f"Success rate: {(successful_logins/len(TEST_CREDENTIALS)*100):.1f}%")
    
    # Show user type breakdown
    tenant_success = sum(1 for r in results if r['success'] and r['user_type'] == 'tenant')
    landlord_success = sum(1 for r in results if r['success'] and r['user_type'] == 'landlord')
    print(f"Tenant logins successful: {tenant_success}")
    print(f"Landlord logins successful: {landlord_success}")
    
    # Save results
    results_file = 'login_test_results.json'
    with open(results_file, 'w') as f:
        json.dump({
            'summary': {
                'total': len(TEST_CREDENTIALS),
                'successful': successful_logins,
                'failed': failed_logins,
                'success_rate': (successful_logins/len(TEST_CREDENTIALS)*100)
            },
            'results': results
        }, f, indent=2)
    
    print(f"\n✓ Login test results saved to: {results_file}")
    
    # Show failures
    failed_logins_list = [r for r in results if not r['success']]
    if failed_logins_list:
        print(f"\nFAILED LOGINS:")
        for failure in failed_logins_list:
            print(f"- {failure['email']}: {failure['error']}")
    
    print(f"\n🎉 Login testing completed!")

if __name__ == "__main__":
    main()