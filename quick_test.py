#!/usr/bin/env python
"""Quick login test script"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tkt.settings')
django.setup()

from django.contrib.auth import get_user_model
import requests
from django.conf import settings

User = get_user_model()

# Check user in DB
email = "hiep18797@gmail.com"
user = User.objects.filter(email=email).first()

print(f"User in DB: {user.username if user else 'NO'}")

# Check user in API
api_url = settings.USERS_API_URL
api_token = settings.API_TOKEN

response = requests.post(api_url, data={'access_token': api_token}, timeout=15)
if response.status_code == 200:
    api_users = response.json().get('users', [])
    api_user = next((u for u in api_users if u.get('email', '').lower() == email.lower()), None)
    if api_user:
        print(f"User in API: YES")
        print(f"API email: {api_user.get('email')}")
    else:
        print(f"User in API: NO")
