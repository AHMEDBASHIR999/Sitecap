from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from API.views import RootView, PilgrimScheduleView, FileUploadView

urlpatterns = [
    path('', PilgrimScheduleView.as_view(), name='pilgrim-schedule-home'),
    path('file-upload/', FileUploadView.as_view(), name='file-upload'),
    path('admin/', admin.site.urls),
    path('api/', include('API.urls')),
    path('api-info/', RootView.as_view(), name='root'),  # Old API info endpoint
]

# Serve static assets (e.g., DRF browsable API CSS/JS) when deployed without a CDN
urlpatterns += staticfiles_urlpatterns()


