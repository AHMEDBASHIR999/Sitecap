import os

from django.core.wsgi import get_wsgi_application

# Ensure Django uses the correct settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Sitecapture.settings")

# Vercel looks for `app` as the WSGI entrypoint
app = get_wsgi_application()

import os

from django.core.wsgi import get_wsgi_application

# Point Django to the correct settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Sitecapture.settings")

# Vercel's Python runtime will look for `app` as the WSGI entrypoint
app = get_wsgi_application()


