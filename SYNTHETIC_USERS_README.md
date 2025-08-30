# Synthetic User Dataset Generator for UniNest

This directory contains tools for generating and registering synthetic users for testing and development purposes.

## Files Overview

### 1. `register_test_users.py` (Recommended - No Dependencies)
Simple script that registers 8 predefined test users. Uses only Python standard library.

**Usage:**
```bash
python3 register_test_users.py
```

**Features:**
- 5 tenant users (students)  
- 3 landlord users (property managers)
- No external dependencies required
- Built-in connection testing
- Detailed success/failure reporting

### 2. `create_synthetic_users.py` (Advanced - Requires Dependencies)
Advanced script that generates large datasets of realistic synthetic users.

**Dependencies:**
```bash
pip install requests faker python-dotenv
```

**Usage:**
```bash
python3 create_synthetic_users.py
```

**Features:**
- Generate any number of users (default: 50)
- Realistic names, emails, and profiles
- CMU-specific details (departments, email domains)
- Customizable tenant/landlord ratio
- Saves dataset to JSON file
- Optional batch registration

### 3. `quick_user_registration.py` (Alternative)
Similar to `register_test_users.py` but requires the `requests` and `python-dotenv` libraries.

## Quick Start

### Step 1: Ensure Backend is Running
Make sure your UniNest backend is running on `http://localhost:8000` (or update the URL in the scripts).

```bash
# Using Docker
docker-compose up backend

# Or manual start
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Step 2: Register Test Users
```bash
python3 register_test_users.py
```

This will register 8 test users:
- **Tenants**: alice.chen@cmu.edu, bob.martinez@gmail.com, carol.wang@andrew.cmu.edu, david.kim@cmu.edu, emma.johnson@gmail.com
- **Landlords**: john.smith@properties.com, sarah.wilson@realty.com, mike.brown@company.com

All passwords are: `StudentPass123!` for tenants, `LandlordPass123!` for landlords.

## Test Users Details

### Tenant Users
| Email | Username | Password | Type |
|-------|----------|----------|------|
| alice.chen@cmu.edu | alicechen | StudentPass123! | tenant |
| bob.martinez@gmail.com | bobmartinez | StudentPass123! | tenant |
| carol.wang@andrew.cmu.edu | carolwang | StudentPass123! | tenant |
| david.kim@cmu.edu | davidkim | StudentPass123! | tenant |
| emma.johnson@gmail.com | emmajohnson | StudentPass123! | tenant |

### Landlord Users
| Email | Username | Password | Type |
|-------|----------|----------|------|
| john.smith@properties.com | johnsmith_realty | LandlordPass123! | landlord |
| sarah.wilson@realty.com | sarahwilson_pm | LandlordPass123! | landlord |
| mike.brown@company.com | mikebrown_properties | LandlordPass123! | landlord |

## Configuration

### Changing Backend URL
Edit the `API_BASE_URL` variable in the scripts:

```python
API_BASE_URL = 'http://your-backend-url:8000'
```

### Environment Variables
For `create_synthetic_users.py`, you can set:
```bash
export VITE_API_BASE_URL=http://localhost:8000
```

## Advanced Usage

### Generate Large Dataset
```bash
python3 create_synthetic_users.py
# Follow prompts:
# - Number of users: 100
# - Tenant ratio: 0.8 (80% tenants, 20% landlords)
# - Register users: y
```

### Generate Without Registration
```bash
python3 create_synthetic_users.py
# Choose 'n' when asked about registration
# This will only generate the JSON dataset file
```

## Output Files

- `user_registration_results.json`: Registration results from `register_test_users.py`
- `synthetic_users_dataset.json`: Generated user data from `create_synthetic_users.py`
- `registration_results.json`: Registration results from `create_synthetic_users.py`

## Troubleshooting

### Backend Connection Issues
1. Verify backend is running: `curl http://localhost:8000/`
2. Check firewall settings
3. Ensure correct URL in script configuration

### Registration Failures
Common issues:
- **"Email already registered"**: User already exists (expected on re-runs)
- **Password validation errors**: Check password requirements in backend
- **Network timeout**: Backend may be slow or overloaded

### Password Requirements
Passwords must meet these requirements:
- At least 8 characters
- At least one uppercase letter
- At least one digit
- Confirm password must match

## Database Verification

After registration, verify users in your database:

```sql
-- Check registered users
SELECT id, email, username, user_type, created_at FROM users ORDER BY created_at DESC;

-- Check tenant profiles
SELECT u.email, tp.budget, tp.preferred_location 
FROM users u 
JOIN tenant_profiles tp ON u.id = tp.user_id 
WHERE u.user_type = 'tenant';

-- Check landlord profiles  
SELECT u.email, lp.company_name, lp.contact_phone
FROM users u
JOIN landlord_profiles lp ON u.id = lp.user_id
WHERE u.user_type = 'landlord';
```

## Testing Login

You can test login with any registered user:

```bash
# Test login endpoint
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=alice.chen@cmu.edu&password=StudentPass123!"
```

## Security Notes

- **Test Environment Only**: These scripts are for development/testing only
- **Default Passwords**: All users use predictable passwords
- **Reset for Production**: Never use these scripts in production environments
- **Database Cleanup**: Consider clearing test data before production deployment

## Support

If you encounter issues:
1. Check backend logs for detailed error messages
2. Verify API endpoints are accessible
3. Ensure database is properly configured
4. Check password validation requirements match script expectations