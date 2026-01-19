from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from .utils import get_bol_access_token, fetch_invoice_spec, calculate_invoice_totals
import pandas as pd
import re
from datetime import datetime


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


class PilgrimScheduleView(View):
    """
    Landing page for Pilgrim Travel Schedules with security code protection.
    GET: Display the index page
    POST: Generate schedules based on input date
    """
    
    # Configuration - Easy to change
    SECURITY_CODE = "9890"
    GOOGLE_SHEET_CSV_URL = (
        "https://docs.google.com/spreadsheets/d/"
        "1F475ZKlJ3OdcMmqnaVJki91OlOikX78mHwKa1fPCD9s"
        "/export?format=csv"
    )
    
    def get(self, request):
        """Display the landing page"""
        return render(request, 'API/pilgrim_schedule.html')
    
    def post(self, request):
        """Handle security code check and schedule generation"""
        action = request.POST.get('action')
        
        # Action 1: Check security code
        if action == 'check_code':
            code = request.POST.get('security_code', '')
            if code == self.SECURITY_CODE:
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'success': False, 'error': 'Invalid security code'})
        
        # Action 2: Generate schedules
        elif action == 'generate_schedule':
            try:
                input_date_raw = request.POST.get('date', '')
                
                if not input_date_raw:
                    return JsonResponse({'success': False, 'error': 'Date is required'})
                
                # Generate the schedule using the original logic
                schedule_output = self._generate_schedule(input_date_raw)
                
                return JsonResponse({'success': True, 'schedule': schedule_output})
            
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})
        
        return JsonResponse({'success': False, 'error': 'Invalid action'})
    
    def _generate_schedule(self, input_date_raw):
        """
        Generate schedules based on input date.
        This is the original logic from Jupyter notebook - DO NOT DISTURB
        """
        # Read Google Sheet into pandas
        df = pd.read_csv(self.GOOGLE_SHEET_CSV_URL, dtype=str)
        
        # ==========================
        # PARSE INPUT DATE (ROBUST)
        # ==========================
        m = re.search(r"(\d{1,2})", input_date_raw)
        if not m:
            raise ValueError("Invalid input date. Use like: 13-Jan or JAN-13")
        
        input_day = int(m.group(1))
        
        m2 = re.search(r"([A-Za-z]+)", input_date_raw)
        if not m2:
            raise ValueError("Month missing in input")
        
        input_month = m2.group(1)[:3].title()   # Jan, Feb, etc.
        
        # ==========================
        # CLEAN MONTH COLUMN
        # ==========================
        df["MONTH_CLEAN"] = (
            df["MONTH"]
            .str.strip()
            .str[:3]
            .str.title()
        )
        
        # ==========================
        # GENERIC DAY EXTRACTOR
        # ==========================
        def extract_day(series):
            return (
                series
                .str.strip()
                .str.extract(r"(\d{1,2})")[0]
                .astype(float)
            )
        
        # ==========================
        # EXTRACT DAY FROM DATE COLUMNS
        # ==========================
        df["DAY_MAIN"] = extract_day(df["DATE / التاريخ"])
        df["DAY_CHOUT_1"] = (df["CH OUT / خروج"])
        df["DAY_CHECKOUT"] = (df["CHECKOUT"])
        df["DAY_CHOUT_2"] = (df["CH OUT"])
        df["DAY_DP"] = extract_day(df["DP DATE / مغادره تاريخ"])
        
        # ==========================
        # SCHEDULE BUILDER
        # ==========================
        def build_schedule(df_f, title, m, static_time=None, static_route=None):
            if df_f.empty:
                return f"\n {title} \n\nNO MOVEMENTS\n"
            
            out = [f"\n {title} \n"]
            for idx, (_, r) in enumerate(df_f.iterrows(), 1):
                # Handle time: if 'time' key exists in mapping, use column data
                # Otherwise use only static_time (for f2 schedule)
                if 'time' in m:
                    time_display = f"{r[m['time']]} {static_time if static_time else ''}"
                else:
                    time_display = static_time if static_time else ""
                
                flight_info = f"Flight    : {r[m['flight']]}\n" if 'flight' in m and r[m['flight']] else ""
                pickup_info = f"Pickup    : {r[m['pickup']]}\n" if 'pickup' in m else ""
                
                out.append(
                    f"""
Route     : *{static_route}*
Booking   : {r[m['booking']]}
Time      : {time_display}
{flight_info}{pickup_info}Drop      : {r[m['drop']]}
Client    : {r[m['client']]}
Mobile    : {r[m['mobile']]}
Agent     : {r[m['agent']]}
----------------------------------
"""
                )
            return "".join(out)
        
        # ==========================
        # FILTER 1 – JED → MAKKAH
        # ==========================
        f1 = df[
            (df["MONTH_CLEAN"] == input_month) &
            (df["DAY_MAIN"] == input_day)
        ]
        
        # ==========================
        # FILTER 2 – MAKKAH → MADINAH
        # ==========================
        f2 = df[df["DAY_CHOUT_1"] == input_date_raw] 
        
        # ==========================
        # FILTER 3 – MADINAH → AIRPORT
        # ==========================
        f3 = df[df["DAY_CHECKOUT"] == input_date_raw]
        
        # ==========================
        # FILTER 4 – MAKKAH → JED
        # ==========================
        f4 = df[df["DAY_CHOUT_2"] == input_date_raw]
        
        # ==========================
        # BUILD FINAL OUTPUT
        # ==========================
        final_output = (
            build_schedule(
                f1,
                "SCHEDULE 1 – JED → MAKKAH",
                {
                    "booking": "TR / مواصلات",
                    "time": "ETA/ موعدالوصول",
                    "drop": "MAKKA HOTEL / مكة فندق",
                    "client": "FAMILY NAME",
                    "mobile": "MOBILE NO.",
                    "agent": "AGENT NAME / اسم وكيل",
                    "flight": "FLIGHT/ رقم رحلة\n"
                }
                ,
                static_route="JED → MAKKAH"
            )
            +
            build_schedule(
                f2,
                "SCHEDULE 2 – MAKKAH → MADINAH",
                {
                    "booking": "TR / مواصلات",
                    "pickup": "MAKKA HOTEL / مكة فندق",
                    "drop": "MEDINAH HOTEL / مدينه فندق",
                    "client": "FAMILY NAME",
                    "mobile": "MOBILE NO.",
                    "agent": "AGENT NAME / اسم وكيل"
                },
                static_time="10:00 AM",
                static_route="MAKKAH → MADINAH"
            )
            +
            build_schedule(
                f3,
                "SCHEDULE 3 – MADINAH → AIRPORT",
                {
                    "booking": "TR / مواصلات",
                    "pickup": "MEDINAH HOTEL / مدينه فندق",
                    "time": "TIME  TO GO AIRPOT / التوقيت ",
                    "flight": "FLIGHT TIME / الوقت الرحلة/DEP",
                    "drop": "FROM / من/AIRPORT",
                    "client": "FAMILY NAME",
                    "mobile": "MOBILE NO.",
                    "agent": "AGENT NAME / اسم وكيل",
                    
                },
                static_route="MADINAH → AIRPORT"
            )
            +
            build_schedule(
                f4,
                "SCHEDULE 4 – MAKKAH → JED",
                {
                    "booking": "TR / مواصلات",
                    "pickup": 21,#column v 
                    "time": "TIME  TO GO AIRPOT / التوقيت ",
                    "drop": "FROM / من/AIRPORT",
                    "client": "FAMILY NAME",
                    "mobile": "MOBILE NO.",
                    "agent": "AGENT NAME / اسم وكيل",
                    "flight": "FLIGHT TIME / الوقت الرحلة/DEP"
                },
                static_time="TO GO AIRPORT",
                static_route="MAKKAH → JED"

            )
        )
        
        # Add header with date
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        header = f"""
                                                          
*Schedule For {input_date_raw.upper()}*                                         
                                                         
"""
        
        return header + final_output
