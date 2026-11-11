from django.urls import path
from .views import InvoiceAnalyticsView, OnOfficeImagesView
from .ahmedtest_views import VibeJoinView, VibeSendView, VibeSyncView, VibeLeaveView

urlpatterns = [
    # Example: /api/invoice/3914706511912/
    path('invoice/<str:invoice_id>/', InvoiceAnalyticsView.as_view(), name='invoice-analytics'),
    path('onoffice/images/<int:estate_id>/', OnOfficeImagesView.as_view(), name='onoffice-images'),
    
    # AhmedTest Realtime Vibration API Endpoints
    path('ahmedtest/join/', VibeJoinView.as_view(), name='ahmedtest-join'),
    path('ahmedtest/send/', VibeSendView.as_view(), name='ahmedtest-send'),
    path('ahmedtest/sync/', VibeSyncView.as_view(), name='ahmedtest-sync'),
    path('ahmedtest/leave/', VibeLeaveView.as_view(), name='ahmedtest-leave'),
]
