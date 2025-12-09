#!/usr/bin/env python
"""
Test login flow và database
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tkt.settings')
django.setup()

from django.contrib.auth import authenticate
from accounts.models import User

print("=" * 70)
print("LOGIN TEST SUMMARY")
print("=" * 70)

# 1. Test existing user login
print("\n1. TEST EXISTING USER LOGIN:")
email = "hiep18797@gmail.com"
password_test = "test123"

user = User.objects.filter(email=email).first()
if user:
    print(f"   User found: {user.email}")
    print(f"   Username: {user.username}")
    
    # Test authentication
    auth_user = authenticate(username=user.username, password=password_test)
    if auth_user:
        print(f"   ✅ Authentication SUCCESS")
    else:
        print(f"   ❌ Authentication FAILED - Wrong password")
else:
    print(f"   ❌ User not found in DB")

# 2. Check total users
print("\n2. TOTAL USERS IN DATABASE:")
total = User.objects.count()
print(f"   {total} users")

print("\n" + "=" * 70)
