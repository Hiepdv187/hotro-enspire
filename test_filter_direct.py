import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tkt.settings')
django.setup()

from ticket.models import Ticket
from tkt.templatetags.image_filters import cloudinary_image_url

ticket = Ticket.objects.get(ticket_id=788243)

print(f"Ticket image: {ticket.image}")
print(f"Image URL: {ticket.image.url}")
print()

# Test filter directly
result = cloudinary_image_url(ticket.image, 'w_800,h_600,c_limit,q_auto,f_auto')
print(f"Filter result: '{result}'")
print(f"Result type: {type(result)}")
print(f"Result length: {len(result)}")
