from django.urls import path
from .views import InvoiceAnalyticsView, PilgrimScheduleView

urlpatterns = [
    # Pilgrim Travel Schedules - Landing Page
    path('', PilgrimScheduleView.as_view(), name='pilgrim-schedule'),
    
    # Example: /api/invoice/3914706511912/
    path('invoice/<str:invoice_id>/', InvoiceAnalyticsView.as_view(), name='invoice-analytics'),
]