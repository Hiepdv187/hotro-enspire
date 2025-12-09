import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tkt.settings')
django.setup()

from django.template import Template, Context
from ticket.models import Ticket

ticket = Ticket.objects.get(ticket_id=788243)

# Test template rendering
template_str = """
{% load image_filters %}
Ticket ID: {{ ticket.ticket_id }}
Has image field: {{ ticket.image }}
Image boolean: {% if ticket.image %}YES{% else %}NO{% endif %}
Image URL: {{ ticket.image.url }}
Image name: {{ ticket.image.name }}

HTML that will render:
{% if ticket.image %}
<div class="image-item">
    <a href="{{ ticket.image.url }}">
        <img src="{{ ticket.image.url|cloudinary_image_url:'w_800,h_600,c_limit,q_auto,f_auto' }}" alt="Image">
    </a>
</div>
{% else %}
<p>NO IMAGE</p>
{% endif %}
"""

template = Template(template_str)
context = Context({'ticket': ticket})
result = template.render(context)

print(result)
