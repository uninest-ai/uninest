#!/usr/bin/env python3
"""
Synthetic User Dataset Generator for UniNest
This script generates and registers realistic synthetic users for testing and development.
"""

import requests
import json
import random
import time
from typing import List, Dict
from faker import Faker
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
API_BASE_URL = os.getenv('VITE_API_BASE_URL', 'http://localhost:8000')
REGISTRATION_ENDPOINT = f"{API_BASE_URL}/api/v1/auth/register"

# Initialize Faker for generating realistic data
fake = Faker()

class SyntheticUserGenerator:
    """Generate realistic synthetic users for UniNest platform"""
    
    def __init__(self):
        self.generated_emails = set()
        self.generated_usernames = set()
        
        # Common CMU/Pittsburgh student characteristics
        self.cmu_departments = [
            'Computer Science', 'Electrical Engineering', 'Mechanical Engineering',
            'Business Administration', 'Design', 'Drama', 'Music', 'Psychology',
            'Chemistry', 'Physics', 'Mathematics', 'Statistics', 'Robotics',
            'Machine Learning', 'Human-Computer Interaction', 'Architecture'
        ]
        
        self.student_year_levels = ['Freshman', 'Sophomore', 'Junior', 'Senior', 'Graduate', 'PhD']
        
        # Landlord company types
        self.landlord_companies = [
            'Property Management', 'Real Estate', 'Rental Solutions', 'Housing Partners',
            'Student Housing', 'Residential Services', 'Property Solutions', 'Rental Group',
            'Urban Properties', 'Campus Housing', 'Metro Rentals', 'City Properties'
        ]
        
        # Common Pittsburgh neighborhoods
        self.pittsburgh_areas = [
            'Oakland', 'Shadyside', 'Squirrel Hill', 'Bloomfield', 'Lawrenceville',
            'Greenfield', 'Point Breeze', 'Friendship', 'East Liberty', 'Regent Square'
        ]

    def generate_tenant_user(self) -> Dict:
        """Generate a realistic tenant user profile"""
        first_name = fake.first_name()
        last_name = fake.last_name()
        
        # Generate unique email and username
        email = self._generate_unique_email(first_name, last_name)
        username = self._generate_unique_username(first_name, last_name)
        
        # Student characteristics
        department = random.choice(self.cmu_departments)
        year_level = random.choice(self.student_year_levels)
        
        return {
            'email': email,
            'username': username,
            'password': 'TempPass123!',  # Strong password that meets validation
            'confirm_password': 'TempPass123!',
            'user_type': 'tenant',
            'profile_data': {
                'first_name': first_name,
                'last_name': last_name,
                'department': department,
                'year_level': year_level,
                'budget_range': self._generate_student_budget(),
                'preferred_location': random.choice(self.pittsburgh_areas),
                'lifestyle_preferences': self._generate_lifestyle_preferences()
            }
        }

    def generate_landlord_user(self) -> Dict:
        """Generate a realistic landlord user profile"""
        # Use business-oriented names for landlords
        first_name = fake.first_name()
        last_name = fake.last_name()
        company_type = random.choice(self.landlord_companies)
        
        email = self._generate_unique_email(first_name, last_name, business=True)
        username = self._generate_unique_username(first_name, last_name, business=True)
        
        return {
            'email': email,
            'username': username,
            'password': 'LandlordPass123!',
            'confirm_password': 'LandlordPass123!',
            'user_type': 'landlord',
            'profile_data': {
                'first_name': first_name,
                'last_name': last_name,
                'company_name': f"{last_name} {company_type}",
                'contact_phone': fake.phone_number(),
                'areas_served': random.sample(self.pittsburgh_areas, random.randint(2, 5)),
                'experience_years': random.randint(2, 25),
                'property_types': random.sample(['apartment', 'house', 'condo', 'townhouse'], random.randint(1, 3))
            }
        }

    def _generate_unique_email(self, first_name: str, last_name: str, business: bool = False) -> str:
        """Generate unique email address"""
        base_patterns = [
            f"{first_name.lower()}.{last_name.lower()}",
            f"{first_name.lower()}{last_name.lower()}",
            f"{first_name[0].lower()}{last_name.lower()}",
            f"{first_name.lower()}{last_name[0].lower()}",
            f"{first_name.lower()}.{last_name.lower()}{random.randint(1, 99)}"
        ]
        
        domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com']
        if business:
            domains.extend(['company.com', 'properties.com', 'realty.com'])
        else:
            domains.extend(['andrew.cmu.edu', 'cmu.edu'])  # CMU email domains
            
        for pattern in base_patterns:
            email = f"{pattern}@{random.choice(domains)}"
            if email not in self.generated_emails:
                self.generated_emails.add(email)
                return email
                
        # Fallback with random number
        email = f"{first_name.lower()}.{last_name.lower()}{random.randint(100, 999)}@{random.choice(domains)}"
        self.generated_emails.add(email)
        return email

    def _generate_unique_username(self, first_name: str, last_name: str, business: bool = False) -> str:
        """Generate unique username"""
        patterns = [
            f"{first_name.lower()}{last_name.lower()}",
            f"{first_name.lower()}_{last_name.lower()}",
            f"{first_name[0].lower()}{last_name.lower()}",
            f"{first_name.lower()}{last_name[0].lower()}",
            f"{first_name.lower()}{random.randint(10, 99)}"
        ]
        
        if business:
            patterns.extend([
                f"{last_name.lower()}_properties",
                f"{first_name.lower()}_realty",
                f"{last_name.lower()}_rentals"
            ])
        
        for pattern in patterns:
            if pattern not in self.generated_usernames:
                self.generated_usernames.add(pattern)
                return pattern
                
        # Fallback
        username = f"{first_name.lower()}{last_name.lower()}{random.randint(100, 999)}"
        self.generated_usernames.add(username)
        return username

    def _generate_student_budget(self) -> Dict:
        """Generate realistic student budget ranges"""
        budgets = [
            {'min': 600, 'max': 900, 'category': 'Budget'},
            {'min': 900, 'max': 1300, 'category': 'Moderate'},
            {'min': 1300, 'max': 1800, 'category': 'Comfortable'},
            {'min': 1800, 'max': 2500, 'category': 'Premium'}
        ]
        return random.choice(budgets)

    def _generate_lifestyle_preferences(self) -> List[str]:
        """Generate realistic lifestyle preferences"""
        all_preferences = [
            'quiet_study_environment', 'social_activities', 'pet_friendly',
            'gym_access', 'parking_needed', 'public_transport_access',
            'cooking_facilities', 'laundry_in_unit', 'outdoor_space',
            'roommate_friendly', 'close_to_campus', 'nightlife_nearby'
        ]
        return random.sample(all_preferences, random.randint(3, 7))

    def generate_user_dataset(self, total_users: int, tenant_ratio: float = 0.8) -> List[Dict]:
        """Generate a complete dataset of synthetic users"""
        dataset = []
        num_tenants = int(total_users * tenant_ratio)
        num_landlords = total_users - num_tenants
        
        print(f"Generating {num_tenants} tenant users and {num_landlords} landlord users...")
        
        # Generate tenants
        for i in range(num_tenants):
            user = self.generate_tenant_user()
            dataset.append(user)
            if (i + 1) % 10 == 0:
                print(f"Generated {i + 1}/{num_tenants} tenants")
        
        # Generate landlords
        for i in range(num_landlords):
            user = self.generate_landlord_user()
            dataset.append(user)
            if (i + 1) % 5 == 0:
                print(f"Generated {i + 1}/{num_landlords} landlords")
        
        return dataset

class UserRegistrationService:
    """Service to register synthetic users via API"""
    
    def __init__(self, api_base_url: str):
        self.api_base_url = api_base_url
        self.registration_endpoint = f"{api_base_url}/api/v1/auth/register"
        
    def register_user(self, user_data: Dict) -> Dict:
        """Register a single user via API"""
        # Prepare registration payload
        payload = {
            'email': user_data['email'],
            'username': user_data['username'],
            'password': user_data['password'],
            'confirm_password': user_data['confirm_password'],
            'user_type': user_data['user_type']
        }
        
        try:
            response = requests.post(
                self.registration_endpoint,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'user_id': response.json().get('id'),
                    'email': user_data['email'],
                    'user_type': user_data['user_type'],
                    'profile_data': user_data.get('profile_data', {})
                }
            else:
                return {
                    'success': False,
                    'error': response.text,
                    'status_code': response.status_code,
                    'email': user_data['email']
                }
                
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'email': user_data['email']
            }

    def register_user_batch(self, users: List[Dict], delay: float = 0.5) -> Dict:
        """Register multiple users with progress tracking"""
        results = {
            'total': len(users),
            'successful': 0,
            'failed': 0,
            'successes': [],
            'failures': []
        }
        
        print(f"Registering {len(users)} users...")
        
        for i, user in enumerate(users):
            print(f"Registering user {i+1}/{len(users)}: {user['email']}")
            
            result = self.register_user(user)
            
            if result['success']:
                results['successful'] += 1
                results['successes'].append(result)
                print(f"✓ Successfully registered {user['email']}")
            else:
                results['failed'] += 1
                results['failures'].append(result)
                print(f"✗ Failed to register {user['email']}: {result.get('error', 'Unknown error')}")
            
            # Add delay to avoid overwhelming the server
            time.sleep(delay)
        
        return results

def main():
    """Main function to generate and register synthetic users"""
    print("=== UniNest Synthetic User Generator ===\n")
    
    # Configuration
    total_users = int(input("How many users to generate? (default: 50): ") or 50)
    tenant_ratio = float(input("Tenant ratio (0-1, default: 0.8): ") or 0.8)
    register_users = input("Register users to the website? (y/n, default: y): ").lower().strip() != 'n'
    
    # Generate users
    print(f"\n1. Generating synthetic user dataset...")
    generator = SyntheticUserGenerator()
    users = generator.generate_user_dataset(total_users, tenant_ratio)
    
    # Save to file
    output_file = 'synthetic_users_dataset.json'
    with open(output_file, 'w') as f:
        json.dump(users, f, indent=2, default=str)
    print(f"✓ Dataset saved to {output_file}")
    
    if register_users:
        print(f"\n2. Registering users to {API_BASE_URL}...")
        registration_service = UserRegistrationService(API_BASE_URL)
        results = registration_service.register_user_batch(users)
        
        # Print summary
        print(f"\n=== Registration Summary ===")
        print(f"Total users: {results['total']}")
        print(f"Successfully registered: {results['successful']}")
        print(f"Failed registrations: {results['failed']}")
        print(f"Success rate: {(results['successful']/results['total']*100):.1f}%")
        
        # Save results
        results_file = 'registration_results.json'
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"✓ Registration results saved to {results_file}")
        
        if results['failures']:
            print(f"\nFailed registrations:")
            for failure in results['failures'][:5]:  # Show first 5 failures
                print(f"- {failure['email']}: {failure.get('error', 'Unknown error')}")
    
    print(f"\n✓ Process completed! Generated {total_users} synthetic users.")
    
    # Display sample users
    print(f"\n=== Sample Generated Users ===")
    for i, user in enumerate(users[:3]):
        print(f"\nUser {i+1} ({user['user_type']}):")
        print(f"  Email: {user['email']}")
        print(f"  Username: {user['username']}")
        if 'profile_data' in user:
            profile = user['profile_data']
            if user['user_type'] == 'tenant':
                print(f"  Department: {profile.get('department', 'N/A')}")
                print(f"  Budget: ${profile.get('budget_range', {}).get('min', 'N/A')}-${profile.get('budget_range', {}).get('max', 'N/A')}")
            else:
                print(f"  Company: {profile.get('company_name', 'N/A')}")

if __name__ == "__main__":
    main()