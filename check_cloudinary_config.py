import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tkt.settings')
django.setup()

import cloudinary
from django.conf import settings

print("=== Cloudinary Configuration ===")
print(f"CLOUDINARY_CONFIGURED: {settings.CLOUDINARY_CONFIGURED}")
print(f"cloudinary.config().cloud_name: {cloudinary.config().cloud_name}")
print(f"cloudinary.config().api_key: {cloudinary.config().api_key[:10]}..." if cloudinary.config().api_key else "None")
print()
print("=== Django Settings ===")
print(f"DEFAULT_FILE_STORAGE: {settings.DEFAULT_FILE_STORAGE}")
print(f"MEDIA_URL: {settings.MEDIA_URL}")
print()

# Try uploading a test image and getting its URL
from ticket.models import Ticket
from django.core.files.base import ContentFile
from PIL import Image
from io import BytesIO

# Create a simple test image
img = Image.new('RGB', (100, 100), color='red')
img_io = BytesIO()
img.save(img_io, format='PNG')
img_io.seek(0)

# Create test image file
test_image = ContentFile(img_io.getvalue(), name='test_image.png')

# Test URL generation
print(f"Test image name: {test_image.name}")
