from django.urls import path
from .views import InvoiceAnalyticsView, OnOfficeImagesView

urlpatterns = [
    # Example: /api/invoice/3914706511912/
    path('invoice/<str:invoice_id>/', InvoiceAnalyticsView.as_view(), name='invoice-analytics'),
    path('onoffice/images/<int:estate_id>/', OnOfficeImagesView.as_view(), name='onoffice-images'),
]