"""
Debug script để kiểm tra Supabase database connection
Chạy: python manage.py shell < debug_supabase.py
hoặc copy các lệnh vào Django shell
"""

import os
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()

print("=" * 60)
print("SUPABASE CONNECTION DEBUG")
print("=" * 60)

# 1. Kiểm tra DATABASE_URL
print("\n1. DATABASE_URL Configuration:")
print(f"   DATABASE_URL: {settings.DATABASES['default']['ENGINE']}")
print(f"   Database Name: {settings.DATABASES['default'].get('NAME', 'N/A')}")

if 'HOST' in settings.DATABASES['default']:
    print(f"   Host: {settings.DATABASES['default']['HOST']}")
if 'PORT' in settings.DATABASES['default']:
    print(f"   Port: {settings.DATABASES['default']['PORT']}")
if 'USER' in settings.DATABASES['default']:
    print(f"   User: {settings.DATABASES['default']['USER']}")

# 2. Kiểm tra kết nối database
print("\n2. Database Connection Test:")
try:
    from django.db import connection
    cursor = connection.cursor()
    cursor.execute("SELECT 1")
    print("   ✅ Database connection: SUCCESS")
except Exception as e:
    print(f"   ❌ Database connection: FAILED")
    print(f"   Error: {str(e)}")

# 3. Kiểm tra users trong database
print("\n3. Users in Database:")
try:
    total_users = User.objects.count()
    print(f"   Total users: {total_users}")
    
    if total_users > 0:
        print("\n   Sample users:")
        for user in User.objects.all()[:5]:
            print(f"   - {user.email} ({user.first_name} {user.last_name})")
except Exception as e:
    print(f"   ❌ Error: {str(e)}")

# 4. Kiểm tra API credentials
print("\n4. API Configuration:")
api_url = getattr(settings, 'USERS_API_URL', None)
api_token = getattr(settings, 'API_TOKEN', None)

print(f"   API URL: {api_url}")
print(f"   API Token: {'***' + api_token[-10:] if api_token else 'NOT SET'}")

# 5. Kiểm tra API connection
print("\n5. API Connection Test:")
if api_url and api_token:
    try:
        import requests
        response = requests.post(
            api_url,
            data={'access_token': api_token},
            timeout=10
        )
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            users_count = len(data.get('users', []))
            print(f"   ✅ API connection: SUCCESS")
            print(f"   Users from API: {users_count}")
            
            # Sample API users
            if users_count > 0:
                print("\n   Sample API users:")
                for user in data.get('users', [])[:3]:
                    print(f"   - {user.get('email')} ({user.get('first_name')} {user.get('last_name')})")
        else:
            print(f"   ❌ API connection: FAILED (Status {response.status_code})")
    except Exception as e:
        print(f"   ❌ API connection: FAILED")
        print(f"   Error: {str(e)}")
else:
    print("   ❌ API credentials not configured")

# 6. Kiểm tra SUPABASE configuration
print("\n6. Supabase Configuration:")
supabase_url = getattr(settings, 'SUPABASE_URL', os.getenv('SUPABASE_URL'))
supabase_key = getattr(settings, 'SUPABASE_KEY', os.getenv('SUPABASE_KEY'))

print(f"   Supabase URL: {supabase_url}")
print(f"   Supabase Key: {'***' + (supabase_key[-10:] if supabase_key else 'NOT SET')}")

print("\n" + "=" * 60)
print("END DEBUG")
print("=" * 60)
