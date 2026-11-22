from django.urls import path
from .views import InvoiceAnalyticsView, OnOfficeImagesView
from .views_ebay import EbayResearchRunAPIView, EbayTestConnectionAPIView, EbayExportReportView, EbayModelStatusAPIView

urlpatterns = [
    # Example: /api/invoice/3914706511912/
    path('invoice/<str:invoice_id>/', InvoiceAnalyticsView.as_view(), name='invoice-analytics'),
    path('onoffice/images/<int:estate_id>/', OnOfficeImagesView.as_view(), name='onoffice-images'),
    path('ebay-research/run/', EbayResearchRunAPIView.as_view(), name='api-ebay-research-run'),
    path('ebay-research/test/', EbayTestConnectionAPIView.as_view(), name='api-ebay-test-connection'),
    path('ebay-research/export/', EbayExportReportView.as_view(), name='api-ebay-export-report'),
    path('ebay-research/status/', EbayModelStatusAPIView.as_view(), name='api-ebay-model-status'),
]