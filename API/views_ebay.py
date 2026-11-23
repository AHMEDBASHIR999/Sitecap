import json
import csv
import io
from django.views import View
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from .ebay_research import (
    run_ebay_research,
    test_ebay_credentials,
    test_aliexpress_credentials,
    generate_standalone_html,
    get_model_status,
    DEFAULT_EBAY_CLIENT_ID,
    DEFAULT_EBAY_CERT_ID,
    DEFAULT_ALI_DS_KEY,
    DEFAULT_ALI_DS_SECRET,
    DEFAULT_ALI_DS_TOKEN,
    MARKETPLACE_CONFIG
)


class EbayResearchPageView(View):
    """
    Renders the main Ebay vs AliExpress Turbo Pro Visual Research dashboard.
    """
    def get(self, request):
        context = {
            "default_ebay_client_id": DEFAULT_EBAY_CLIENT_ID,
            "default_ebay_cert_id": DEFAULT_EBAY_CERT_ID,
            "default_ali_key": DEFAULT_ALI_DS_KEY,
            "default_ali_secret": DEFAULT_ALI_DS_SECRET,
            "default_ali_token": DEFAULT_ALI_DS_TOKEN,
            "marketplaces": MARKETPLACE_CONFIG,
            "model_status": get_model_status()
        }
        return render(request, "API/ebay_research.html", context)


@method_decorator(csrf_exempt, name='dispatch')
class EbayResearchRunAPIView(View):
    """
    API endpoint to trigger the research routine.
    Accepts JSON payload or form data.
    """
    def post(self, request):
        try:
            if request.content_type == 'application/json':
                payload = json.loads(request.body.decode('utf-8'))
            else:
                payload = request.POST.dict()
        except Exception as e:
            return JsonResponse({"success": False, "message": f"Invalid request body: {str(e)}"}, status=400)

        raw_links = payload.get("links", "")
        country = payload.get("country", "AUTO")
        ebay_client_id = payload.get("ebay_client_id")
        ebay_cert_id = payload.get("ebay_cert_id")
        ali_key = payload.get("ali_key")
        ali_secret = payload.get("ali_secret")
        ali_token = payload.get("ali_token")
        max_items = payload.get("max_items")
        batch_info = payload.get("batch_info")

        if not raw_links or not str(raw_links).strip():
            return JsonResponse({
                "success": False,
                "message": "Please enter or paste at least one eBay item link or ID."
            }, status=400)

        logs = []
        def log_collector(msg):
            logs.append(msg)

        try:
            result = run_ebay_research(
                raw_links=raw_links,
                country=country,
                ebay_client_id=ebay_client_id,
                ebay_cert_id=ebay_cert_id,
                ali_key=ali_key,
                ali_secret=ali_secret,
                ali_token=ali_token,
                max_items=max_items,
                log_callback=log_collector,
                batch_info=batch_info
            )
            result["logs"] = logs
            return JsonResponse(result, safe=False)
        except Exception as ex:
            return JsonResponse({
                "success": False,
                "message": f"Server processing error: {str(ex)}",
                "logs": logs,
                "errors": [str(ex)]
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class EbayTestConnectionAPIView(View):
    """
    Endpoint to test eBay and AliExpress credentials independently.
    """
    def post(self, request):
        try:
            if request.content_type == 'application/json':
                payload = json.loads(request.body.decode('utf-8'))
            else:
                payload = request.POST.dict()
        except Exception as e:
            return JsonResponse({"success": False, "message": f"Invalid request body: {str(e)}"}, status=400)

        service = payload.get("service", "").lower()

        if service == "ebay":
            client_id = payload.get("ebay_client_id")
            cert_id = payload.get("ebay_cert_id")
            res = test_ebay_credentials(client_id, cert_id)
            return JsonResponse(res)

        elif service == "aliexpress":
            key = payload.get("ali_key")
            secret = payload.get("ali_secret")
            token = payload.get("ali_token")
            res = test_aliexpress_credentials(key, secret, token)
            return JsonResponse(res)

        else:
            return JsonResponse({
                "success": False,
                "message": "Unknown service parameter. Expected 'ebay' or 'aliexpress'."
            }, status=400)


@method_decorator(csrf_exempt, name='dispatch')
class EbayExportReportView(View):
    """
    Exports research results to standalone HTML, CSV, or JSON.
    """
    def post(self, request):
        try:
            body_str = request.body.decode('utf-8')
            if body_str:
                payload = json.loads(body_str)
            else:
                payload = request.POST.dict()
        except Exception:
            try:
                payload = request.POST.dict()
                if "results" in payload and isinstance(payload["results"], str):
                    payload["results"] = json.loads(payload["results"])
                if "summary" in payload and isinstance(payload["summary"], str):
                    payload["summary"] = json.loads(payload["summary"])
            except Exception as e:
                return HttpResponse(f"Invalid export payload: {str(e)}", status=400)

        results = payload.get("results", [])
        summary = payload.get("summary", {})
        fmt = payload.get("format", "html").lower()

        if fmt == "html":
            html_doc = generate_standalone_html(results, summary)
            resp = HttpResponse(html_doc, content_type="text/html; charset=utf-8")
            resp['Content-Disposition'] = 'attachment; filename="ebay_vs_aliexpress_turbo_visual.html"'
            return resp

        elif fmt == "csv":
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow([
                "Index", "Item ID", "Country", "Title", "eBay Price", "Currency",
                "Sold Count", "Age", "Seller", "Location", "eBay Link",
                "Ali Top Title", "Ali Top Price", "Ali Top Score %", "Spread", "Ali Link"
            ])
            for idx, it in enumerate(results, 1):
                top3 = it.get("top3", [])
                t1 = top3[0] if top3 else {}
                writer.writerow([
                    idx,
                    it.get("id"),
                    it.get("country"),
                    it.get("title"),
                    it.get("price"),
                    it.get("curr"),
                    it.get("sold", ""),
                    it.get("age"),
                    it.get("seller"),
                    it.get("loc"),
                    it.get("link"),
                    t1.get("title", ""),
                    t1.get("price", ""),
                    t1.get("score", ""),
                    it.get("spread", ""),
                    t1.get("url", "")
                ])
            resp = HttpResponse(output.getvalue(), content_type="text/csv; charset=utf-8")
            resp['Content-Disposition'] = 'attachment; filename="ebay_research_export.csv"'
            return resp

        elif fmt == "json":
            data = {"summary": summary, "results": results}
            resp = HttpResponse(json.dumps(data, indent=2), content_type="application/json; charset=utf-8")
            resp['Content-Disposition'] = 'attachment; filename="ebay_research_export.json"'
            return resp

        return HttpResponse("Unsupported export format.", status=400)


class EbayModelStatusAPIView(View):
    """
    Returns current status of the CLIP AI model.
    """
    def get(self, request):
        return JsonResponse(get_model_status())

