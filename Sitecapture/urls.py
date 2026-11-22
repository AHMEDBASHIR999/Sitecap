from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from API.views import RootView, PilgrimScheduleView, FileUploadView, VoucherDataEntryView
from API.views_ebay import EbayResearchPageView, EbayResearchRunAPIView, EbayTestConnectionAPIView, EbayExportReportView, EbayModelStatusAPIView

urlpatterns = [
    path('', PilgrimScheduleView.as_view(), name='pilgrim-schedule-home'),
    path('file-upload/', FileUploadView.as_view(), name='file-upload'),
    path('voucher-entry/', VoucherDataEntryView.as_view(), name='voucher-entry'),
    path('ebay-research/', EbayResearchPageView.as_view(), name='ebay-research'),
    path('ebayresearch/', EbayResearchPageView.as_view(), name='ebayresearch'),
    # Direct research API endpoints
    path('ebay-research/api/run/', EbayResearchRunAPIView.as_view(), name='ebay-research-run'),
    path('ebay-research/api/test/', EbayTestConnectionAPIView.as_view(), name='ebay-research-test'),
    path('ebay-research/api/export/', EbayExportReportView.as_view(), name='ebay-research-export'),
    path('ebay-research/api/status/', EbayModelStatusAPIView.as_view(), name='ebay-research-status'),
    path('admin/', admin.site.urls),
    path('api/', include('API.urls')),
    path('api-info/', RootView.as_view(), name='root'),  # Old API info endpoint
]

# Serve static assets (e.g., DRF browsable API CSS/JS) when deployed without a CDN
urlpatterns += staticfiles_urlpatterns()


