from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from API.views import RootView

urlpatterns = [
    path('', RootView.as_view(), name='root'),
    path('admin/', admin.site.urls),
    path('api/', include('API.urls')),
]

# Serve static assets (e.g., DRF browsable API CSS/JS) when deployed without a CDN
urlpatterns += staticfiles_urlpatterns()


