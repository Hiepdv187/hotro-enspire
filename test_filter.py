import os
import django
from django.template import Template, Context

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tkt.settings')
django.setup()

from ticket.models import Ticket

ticket = Ticket.objects.get(ticket_id=163219)

# Test the cloudinary_image_url filter
from tkt.templatetags.image_filters import cloudinary_image_url

# Test case 1: Local file path
image_url = ticket.image.url
transformed_url = cloudinary_image_url(ticket.image, 'w_800,h_600,c_limit,q_auto,f_auto')

print("Test: cloudinary_image_url filter")
print(f"Input image URL: {image_url}")
print(f"Transformed: {transformed_url}")
print()

# Test case 2: Test template rendering
template_str = """{% load image_filters %}{{ image_url|cloudinary_image_url:'w_800,h_600,c_limit,q_auto,f_auto' }}"""
template = Template(template_str)
context = Context({'image_url': ticket.image.url})
result = template.render(context)

print("Template rendering test:")
print(f"Template: {template_str}")
print(f"Result: {result}")
