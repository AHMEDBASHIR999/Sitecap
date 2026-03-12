from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from .utils import get_bol_access_token, fetch_invoice_spec, calculate_invoice_totals
import pandas as pd
import re
import requests
from datetime import datetime
import os
import time
import hmac
import hashlib
import base64
import json


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
                
                # Handle pickup - can be string (column name) or int (column index)
                if 'pickup' in m:
                    pickup_value = r.iloc[m['pickup']] if isinstance(m['pickup'], int) else r[m['pickup']]
                    pickup_info = f"Pickup    : {pickup_value}\n"
                else:
                    pickup_info = ""
                
                # Handle mobile with + prefix, safely handle None/nan values
                if 'mobile' in m:
                    mobile_value = r[m['mobile']]
                    if mobile_value and str(mobile_value).lower() not in ['nan', 'none', '']:
                        mobile_display = f"+{mobile_value}" if not str(mobile_value).startswith('+') else str(mobile_value)
                    else:
                        mobile_display = mobile_value
                else:
                    mobile_display = ""
                
                out.append(
                    f"""
Route     : *{static_route}*
Booking   : {r[m['booking']]}
Time      : {time_display}
{flight_info}{pickup_info}Drop      : {r[m['drop']]}
Client    : {r[m['client']]}
Mobile    : {mobile_display}
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


# ---------------------------------------------------------------------------
# FILE UPLOAD TO GOOGLE SHEET (separate feature - do not modify above logic)
# ---------------------------------------------------------------------------

def _get_google_creds(scopes):
    """Get Google credentials from file path or JSON env var (for Vercel/serverless)."""
    import os
    import json
    from django.conf import settings
    # Option 1: JSON string in env (for Vercel - paste entire key.json content)
    json_str = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS_JSON')
    if json_str:
        try:
            info = json.loads(json_str)
            from google.oauth2.service_account import Credentials
            return Credentials.from_service_account_info(info, scopes=scopes)
        except (json.JSONDecodeError, KeyError):
            pass
    # Option 2: File path (local / .env)
    creds_path = getattr(settings, 'GOOGLE_SHEETS_CREDENTIALS_PATH', None) or os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
    if creds_path and not os.path.isabs(creds_path):
        base = getattr(settings, 'BASE_DIR', None)
        if base:
            creds_path = os.path.join(base, creds_path)
    if creds_path and os.path.isfile(creds_path):
        from google.oauth2.service_account import Credentials
        return Credentials.from_service_account_file(creds_path, scopes=scopes)
    return None


def _extract_google_sheet_id(url):
    """Extract spreadsheet ID from Google Sheet URL (edit or published)."""
    import re
    # Published to web: /d/e/2PACX-xxx...
    m = re.search(r'/d/e/([a-zA-Z0-9_-]+)', url)
    if m:
        return ('published', m.group(1))
    # Standard edit URL: /d/1xxx...
    m = re.search(r'/d/([a-zA-Z0-9_-]+)', url)
    if m:
        return ('edit', m.group(1))
    return None


def _extract_gid(url):
    """Extract worksheet gid from Google Sheet URL (?gid=123 or #gid=123). Uses that tab instead of first sheet."""
    import re
    if not url:
        return None
    m = re.search(r'[?#]gid=(\d+)', url)
    if m:
        try:
            return int(m.group(1))
        except ValueError:
            return None
    return None


def _get_worksheet(sh, gid=None):
    """Return worksheet by gid if given, else first sheet."""
    if gid is not None:
        try:
            return sh.get_worksheet_by_id(gid)
        except (Exception, AttributeError):
            pass
    return sh.sheet1


def _get_sheet_headers_from_csv_export(sheet_id, gid=0):
    """Fetch first row (headers) from a public Google Sheet via CSV export."""
    import csv
    import requests
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/csv,text/plain,*/*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://docs.google.com/',
        'Origin': 'https://docs.google.com',
    }
    if isinstance(sheet_id, tuple):
        url_type, sid = sheet_id
        if url_type == 'published':
            url = f"https://docs.google.com/spreadsheets/d/e/{sid}/pub?output=csv"
        else:
            url = f"https://docs.google.com/spreadsheets/d/{sid}/export?format=csv&gid={gid}"
    else:
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
    resp = requests.get(url, headers=headers, timeout=20)
    resp.raise_for_status()
    first_line = resp.text.split('\n')[0].strip()
    if not first_line:
        return []
    reader = csv.reader([first_line])
    return next(reader)


class FileUploadView(View):
    """
    File Upload page: enter Google Sheet URL, upload file, map columns (drag & drop), then upload to sheet.
    GET: Show the file upload / mapping page.
    POST: Actions: get_sheet_columns | get_file_columns | upload_to_sheet
    """

    def get(self, request):
        return render(request, 'API/file_upload.html')

    def post(self, request):
        action = request.POST.get('action') or (request.FILES and request.POST.get('action'))

        # Get CSRF from header or POST
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and request.method == 'POST':
            pass  # CSRF still validated by Django

        # -------- Action: get_sheet_columns --------
        if action == 'get_sheet_columns':
            sheet_url = (request.POST.get('sheet_url') or '').strip()
            if not sheet_url:
                return JsonResponse({'success': False, 'error': 'Google Sheet URL is required.'})
            sheet_id = _extract_google_sheet_id(sheet_url)
            if not sheet_id:
                return JsonResponse({'success': False, 'error': 'Invalid Google Sheet URL. Could not find spreadsheet ID.'})
            raw_sid = sheet_id[1] if isinstance(sheet_id, tuple) else sheet_id
            if isinstance(sheet_id, tuple) and sheet_id[0] == 'published':
                return JsonResponse({'success': False, 'error': 'Use the standard edit URL (not Published to web) for Load Sheet.'})

            gid = _extract_gid(sheet_url)
            # Try service account first (works when sheet is shared with it)
            creds = _get_google_creds(['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive.readonly'])
            if creds:
                try:
                    import gspread
                    gc = gspread.authorize(creds)
                    sh = gc.open_by_key(raw_sid)
                    ws = _get_worksheet(sh, gid)
                    headers = ws.row_values(1)  # first row
                    if headers:
                        return JsonResponse({'success': True, 'columns': headers, 'sheet_id': raw_sid})
                except Exception as e:
                    err = str(e)
                    if 'PERMISSION_DENIED' in err or '403' in err or 'not found' in err.lower():
                        return JsonResponse({
                            'success': False,
                            'error': 'Share your Google Sheet with the service account email (Editor). Find the email in your key.json (client_email).'
                        })
                    return JsonResponse({'success': False, 'error': err})

            # Fallback: CSV export (often blocked by Google)
            try:
                csv_gid = gid if gid is not None else 0
                headers = _get_sheet_headers_from_csv_export(sheet_id, gid=csv_gid)
                if not headers:
                    return JsonResponse({'success': False, 'error': 'Could not read sheet.'})
                return JsonResponse({'success': True, 'columns': headers, 'sheet_id': raw_sid})
            except requests.exceptions.HTTPError as e:
                if e.response and e.response.status_code == 400:
                    return JsonResponse({
                        'success': False,
                        'error': 'Set up GOOGLE_APPLICATION_CREDENTIALS or GOOGLE_SHEETS_CREDENTIALS_PATH in .env and share your sheet with the service account email (Editor).'
                    })
                return JsonResponse({'success': False, 'error': str(e)})
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})

        # -------- Action: get_sheet_columns_manual (fallback when fetch fails) --------
        if action == 'get_sheet_columns_manual':
            cols_str = (request.POST.get('columns') or '').strip()
            if not cols_str:
                return JsonResponse({'success': False, 'error': 'Enter column names (comma-separated).'})
            cols = [c.strip() for c in cols_str.split(',') if c.strip()]
            if not cols:
                return JsonResponse({'success': False, 'error': 'No valid column names.'})
            return JsonResponse({'success': True, 'columns': cols})

        # -------- Action: get_file_columns --------
        if action == 'get_file_columns':
            f = request.FILES.get('file')
            if not f:
                return JsonResponse({'success': False, 'error': 'No file uploaded.'})
            try:
                name = (f.name or '').lower()
                if name.endswith('.csv'):
                    df = pd.read_csv(f, nrows=0, encoding='utf-8', on_bad_lines='skip')
                elif name.endswith('.xlsx') or name.endswith('.xls'):
                    df = pd.read_excel(f, nrows=0, engine='openpyxl' if name.endswith('.xlsx') else None)
                else:
                    return JsonResponse({'success': False, 'error': 'Unsupported format. Use CSV or Excel (.xlsx, .xls).'})
                cols = list(df.columns)
                return JsonResponse({'success': True, 'columns': cols, 'filename': f.name})
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})

        # -------- Action: upload_to_sheet --------
        if action == 'upload_to_sheet':
            sheet_url = (request.POST.get('sheet_url') or '').strip()
            mapping_json = request.POST.get('mapping')  # JSON: { "Sheet Col A": "File Col 1", ... }
            sheet_columns_json = request.POST.get('sheet_columns')  # Full list of sheet columns in order
            f = request.FILES.get('file')
            if not mapping_json or not f:
                return JsonResponse({'success': False, 'error': 'Missing mapping or file.'})
            sheet_id = _extract_google_sheet_id(sheet_url) if sheet_url else None
            gid_upload = _extract_gid(sheet_url) if sheet_url else None
            try:
                import json
                mapping = json.loads(mapping_json)  # { "Sheet Column Name": "File Column Name", ... }
            except Exception:
                return JsonResponse({'success': False, 'error': 'Invalid mapping JSON.'})

            try:
                name = (f.name or '').lower()
                if name.endswith('.csv'):
                    df = pd.read_csv(f, dtype=str, encoding='utf-8', on_bad_lines='skip')
                elif name.endswith('.xlsx') or name.endswith('.xls'):
                    df = pd.read_excel(f, dtype=str, engine='openpyxl' if name.endswith('.xlsx') else None)
                else:
                    return JsonResponse({'success': False, 'error': 'Unsupported file format.'})
            except Exception as e:
                return JsonResponse({'success': False, 'error': f'Failed to read file: {e}'})

            # Build rows in the FULL sheet column order - skipped mappings get empty string to avoid misalignment
            if sheet_columns_json:
                try:
                    sheet_header_order = json.loads(sheet_columns_json)
                except Exception:
                    sheet_header_order = None
            else:
                sheet_header_order = None
            if not sheet_header_order and sheet_id:
                try:
                    csv_gid = gid_upload if gid_upload is not None else 0
                    sheet_header_order = _get_sheet_headers_from_csv_export(sheet_id, gid=csv_gid)
                except Exception:
                    pass
            if not sheet_header_order:
                try:
                    creds = _get_google_creds(['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive.readonly'])
                    if creds and sheet_id:
                        raw_sid = sheet_id[1] if isinstance(sheet_id, tuple) else sheet_id
                        import gspread
                        gc = gspread.authorize(creds)
                        sh = gc.open_by_key(raw_sid)
                        ws_fetch = _get_worksheet(sh, gid_upload)
                        sheet_header_order = ws_fetch.row_values(1)
                except Exception:
                    pass
            if not sheet_header_order:
                sheet_header_order = list(mapping.keys())  # fallback - may cause misalignment if mappings skipped
            rows = []
            for _, r in df.iterrows():
                row = []
                for sc in sheet_header_order:
                    fc = mapping.get(sc)
                    if fc is None:
                        val = ''
                    else:
                        v = r.get(fc, '')
                        val = v if isinstance(v, str) else (str(v) if pd.notna(v) else '')
                    row.append(val)
                rows.append(row)

            if not rows:
                return JsonResponse({'success': False, 'error': 'No data rows to upload.'})

            # Direct upload to Google Sheet (requires service account - sheet must be shared with it)
            if not sheet_id:
                return JsonResponse({'success': False, 'error': 'Google Sheet URL is required for direct upload.'})
            raw_sheet_id = sheet_id[1] if isinstance(sheet_id, tuple) else sheet_id
            if isinstance(sheet_id, tuple) and sheet_id[0] == 'published':
                return JsonResponse({'success': False, 'error': 'Use the standard edit URL (not Published to web) for direct upload.'})

            creds = _get_google_creds(['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
            if not creds:
                return JsonResponse({
                    'success': False,
                    'error': 'Direct upload not configured. Set GOOGLE_APPLICATION_CREDENTIALS_JSON (paste full key.json) in Vercel env, or use GOOGLE_APPLICATION_CREDENTIALS (file path) locally. Share your sheet with the service account email (Editor).'
                })

            try:
                import gspread
                gc = gspread.authorize(creds)
                sh = gc.open_by_key(raw_sheet_id)
                ws = _get_worksheet(sh, gid_upload)
                # Append data rows (sheet already has header row)
                ws.append_rows(rows, value_input_option='USER_ENTERED')
                return JsonResponse({
                    'success': True,
                    'message': f'Successfully uploaded {len(rows)} row(s) directly to your Google Sheet!',
                    'row_count': len(rows)
                })
            except ImportError:
                return JsonResponse({
                    'success': False,
                    'error': 'Install gspread and google-auth: pip install gspread google-auth'
                })
            except Exception as e:
                err = str(e)
                if 'PERMISSION_DENIED' in err or '403' in err or 'not found' in err.lower():
                    return JsonResponse({
                        'success': False,
                        'error': 'Share your Google Sheet with the service account email (Editor). Find the email in your credentials JSON (client_email).'
                    })
                return JsonResponse({'success': False, 'error': err})

        return JsonResponse({'success': False, 'error': 'Invalid action.'})


class OnOfficeImagesView(APIView):
    """
    GET /api/onoffice/images/<estate_id>/

    Query params (optional):
      - category: onOffice picture category (default: Foto)

    Returns both:
      - webflow_images: [{\"url\": \"...\"}, ...]
      - images: {\"image1\": \"...\", \"image2\": \"...\", ...}
    """

    def get(self, request, estate_id: int):
        token = os.environ.get("ONOFFICE_TOKEN")
        secret = os.environ.get("ONOFFICE_SECRET")
        if not token or not secret:
            return Response(
                {
                    "success": False,
                    "error": "ONOFFICE_TOKEN or ONOFFICE_SECRET not set in environment."
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        category = request.query_params.get("category", "Foto")

        timestamp = str(int(time.time()))
        actionid = "urn:onoffice-de-ns:smart:2.5:smartml:action:get"
        resourcetype = "estatepictures"
        resourceid = ""

        data = timestamp + token + resourcetype + actionid + resourceid

        signature = base64.b64encode(
            hmac.new(secret.encode(), data.encode(), hashlib.sha256).digest()
        ).decode()

        payload = {
            "token": token,
            "request": {
                "actions": [
                    {
                        "actionid": actionid,
                        "resourceid": resourceid,
                        "resourcetype": resourcetype,
                        "timestamp": timestamp,
                        "hmac_version": "2",
                        "hmac": signature,
                        "parameters": {
                            "estateids": [int(estate_id)],
                            "categories": [category],
                        },
                    }
                ]
            },
        }

        try:
            resp = requests.post(
                "https://api.onoffice.de/api/stable/api.php",
                json=payload,
                timeout=20,
            )
            resp.raise_for_status()
            response_json = resp.json()
        except Exception as e:
            return Response(
                {"success": False, "error": f"Request to onOffice failed: {e}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        try:
            results = (
                response_json.get("response", {})
                .get("results", [])[0]
                .get("data", {})
                .get("records", [])
            )
        except (IndexError, AttributeError):
            results = []

        image_urls = []
        for record in results:
            for element in record.get("elements", []):
                url = element.get("url")
                if url:
                    image_urls.append(url)

        webflow_images = [{"url": u} for u in image_urls]
        flat_images = {f"image{i+1}": u for i, u in enumerate(image_urls)}

        return Response(
            {
                "success": True,
                "estate_id": estate_id,
                "category": category,
                "count": len(image_urls),
                "webflow_images": webflow_images,
                "images": flat_images,
            },
            status=status.HTTP_200_OK,
        )

