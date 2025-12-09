import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tkt.settings')
django.setup()

from ticket.models import Ticket
import requests

ticket = Ticket.objects.get(ticket_id=163219)
print(f'Ticket ID: {ticket.ticket_id}')
print(f'Image field value: {ticket.image}')
print(f'Image name: {ticket.image.name}')
print(f'Image URL: {ticket.image.url}')
print()

# Test if URL is accessible
url = ticket.image.url
print(f'Testing URL access: {url}')
try:
    response = requests.head(url, timeout=5, allow_redirects=True)
    print(f'Response status: {response.status_code}')
except Exception as e:
    print(f'Error: {e}')

print()
print('Full URL breakdown:')
if '/upload/' in url:
    parts = url.split('/upload/')
    print(f'  Base: {parts[0]}/upload/')
    print(f'  Path: {parts[1]}')
else:
    print(f'  URL does not contain /upload/ - may not be Cloudinary format')
