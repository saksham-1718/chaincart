"""
WSGI config for backend project.
"""

import os
import sys
import traceback

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

print("🚀 Starting Django WSGI application...")

try:
    application = get_wsgi_application()
    print("✅ Django application loaded successfully.")
except Exception:
    print("❌ Django failed to start. Traceback below:")
    traceback.print_exc()
    sys.stdout.flush()
