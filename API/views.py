from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .utils import get_bol_access_token, fetch_invoice_spec, calculate_invoice_totals


class RootView(APIView):
    """
    Root endpoint that provides API information and health check.
    GET /
    """
    
    def get(self, request):
        return Response({
            "message": "Sitecap API is running",
            "version": "1.0.0",
            "endpoints": {
                "invoice_analytics": "/api/invoice/<invoice_id>/",
                "admin": "/admin/"
            },
            "health": "ok"
        }, status=status.HTTP_200_OK)


class InvoiceAnalyticsView(APIView):
    """
    GET /api/invoice/<invoice_id>/
    Optional Query Param: ?ean=8720929627028
    """
    
    def get(self, request, invoice_id):
        # 1. Get Authentication
        token = get_bol_access_token()
        if not token:
            return Response(
                {"error": "Failed to authenticate with Bol.com"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # 2. Fetch Data
        invoice_json = fetch_invoice_spec(invoice_id, token)
        if not invoice_json:
            return Response(
                {"error": "Invoice not found or API error"}, 
                status=status.HTTP_404_NOT_FOUND
            )

        # 3. Check for specific EAN filter in URL
        target_ean = request.query_params.get('ean', None)

        # 4. Calculate
        # This function handles the logic we built
        analytics_data = calculate_invoice_totals(invoice_json, target_ean=target_ean)

        if not analytics_data:
            return Response(
                {"message": "No data found for the criteria."}, 
                status=status.HTTP_200_OK
            )

        # 5. Return JSON Response
        return Response({
            "invoice_id": invoice_id,
            "filter_ean": target_ean if target_ean else "ALL",
            "results": analytics_data
        }, status=status.HTTP_200_OK)