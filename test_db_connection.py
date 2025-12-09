#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tkt.settings')
django.setup()

from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()

print("=" * 70)
print("SUPABASE CONNECTION DEBUG TEST")
print("=" * 70)

# 1. Check DATABASE configuration
print("\n1. DATABASE CONFIGURATION:")
print(f"   Engine: {settings.DATABASES['default']['ENGINE']}")
print(f"   Has NAME key: {'NAME' in settings.DATABASES['default']}")

if settings.DATABASES['default']['ENGINE'] == 'django.db.backends.postgresql':
    print(f"   Host: {settings.DATABASES['default'].get('HOST', 'N/A')}")
    print(f"   Port: {settings.DATABASES['default'].get('PORT', 'N/A')}")
    print(f"   User: {settings.DATABASES['default'].get('USER', 'N/A')}")

# 2. Test database connection
print("\n2. DATABASE CONNECTION TEST:")
try:
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"   Status: SUCCESS")
        print(f"   PostgreSQL: {version[0][:50]}...")
except Exception as e:
    print(f"   Status: FAILED")
    print(f"   Error: {type(e).__name__}: {str(e)[:100]}")

# 3. Check users in database
print("\n3. DATABASE USERS CHECK:")
try:
    count = User.objects.count()
    print(f"   Total users: {count}")
    if count > 0:
        sample = User.objects.first()
        print(f"   Sample: {sample.email} ({sample.first_name} {sample.last_name})")
except Exception as e:
    print(f"   Error: {str(e)[:100]}")

# 4. Check API Configuration
print("\n4. API CONFIGURATION:")
api_url = getattr(settings, 'USERS_API_URL', 'NOT SET')
api_token = getattr(settings, 'API_TOKEN', 'NOT SET')
print(f"   USERS_API_URL: {api_url}")
if api_token != 'NOT SET':
    print(f"   API_TOKEN: ***{api_token[-15:]}")
else:
    print(f"   API_TOKEN: NOT SET")

# 5. Test API Connection
print("\n5. API CONNECTION TEST:")
if api_url != 'NOT SET' and api_token != 'NOT SET':
    try:
        import requests
        response = requests.post(
            api_url,
            data={'access_token': api_token},
            timeout=15
        )
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            users = data.get('users', [])
            print(f"   API Result: SUCCESS")
            print(f"   Users count: {len(users)}")
            if users:
                print(f"   First user: {users[0].get('email')}")
        else:
            print(f"   API Result: FAILED (Status {response.status_code})")
            try:
                print(f"   Response: {response.text[:200]}")
            except:
                pass
    except Exception as e:
        print(f"   API Result: ERROR")
        print(f"   Error: {type(e).__name__}: {str(e)[:100]}")
else:
    print(f"   Skipped - API not configured")

print("\n" + "=" * 70)
