from django.urls import path
from .views import InvoiceAnalyticsView

urlpatterns = [
    # Example: /api/invoice/3914706511912/
    path('invoice/<str:invoice_id>/', InvoiceAnalyticsView.as_view(), name='invoice-analytics'),
]