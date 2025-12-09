#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tkt.settings')
django.setup()

from django.contrib.auth import get_user_model, authenticate
import requests
from django.conf import settings

User = get_user_model()

print("=" * 70)
print("LOGIN FLOW TEST - SIMULATE USER LOGIN")
print("=" * 70)

# Test email
test_email = input("\nNhập email để test login: ").strip()

if not test_email:
    print("Email không được để trống!")
    sys.exit(1)

print(f"\n1. CHECKING IF USER EXISTS IN LOCAL DB:")
local_user = User.objects.filter(email=test_email).first()
if local_user:
    print(f"   ✅ User exists in DB: {test_email}")
    print(f"      Username: {local_user.username}")
    print(f"      First name: {local_user.first_name}")
    print(f"      Last name: {local_user.last_name}")
else:
    print(f"   ❌ User NOT in DB: {test_email}")

print(f"\n2. CHECKING IF USER EXISTS IN API:")
try:
    api_url = settings.USERS_API_URL
    api_token = settings.API_TOKEN
    
    response = requests.post(
        api_url,
        data={'access_token': api_token},
        timeout=15
    )
    
    if response.status_code == 200:
        api_users = response.json().get('users', [])
        api_user = next((u for u in api_users if u.get('email', '').lower() == test_email.lower()), None)
        
        if api_user:
            print(f"   ✅ User exists in API: {test_email}")
            print(f"      First name: {api_user.get('first_name', 'N/A')}")
            print(f"      Last name: {api_user.get('last_name', 'N/A')}")
            print(f"      Email: {api_user.get('email')}")
            print(f"      Keys in API: {list(api_user.keys())}")
        else:
            print(f"   ❌ User NOT in API: {test_email}")
    else:
        print(f"   ❌ API Error: Status {response.status_code}")
except Exception as e:
    print(f"   ❌ API Error: {str(e)}")

print(f"\n3. TEST AUTHENTICATION:")
test_password = input("Nhập mật khẩu để test: ").strip()

if not test_password:
    print("Mật khẩu không được để trống!")
else:
    # Scenario 1: User exists locally
    if local_user:
        print(f"\n   Scenario A: User exists in local DB")
        result = authenticate(username=local_user.username, password=test_password)
        if result:
            print(f"   ✅ Authentication SUCCESS with local password")
        else:
            print(f"   ❌ Authentication FAILED - Password incorrect")
    else:
        print(f"\n   Scenario B: User does NOT exist in local DB")
        print(f"   Would create new user with:")
        print(f"      - username: {test_email}")
        print(f"      - password: {test_password}")

print("\n" + "=" * 70)
