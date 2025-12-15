import requests
import os
from requests.auth import HTTPBasicAuth

# Best practice: Load these from environment variables or settings.py
# For now, you can set them here or use os.getenv()
CLIENT_ID = "56073c0b-f4f9-4ee7-a42d-841eec482231" 
CLIENT_SECRET = "bZEcc(Cjkuz2wrLAVhMDvKwHjlxjk3c)1msu!QP1ItzMkPDhUaYHqcSxnkEWNiLO"

def get_bol_access_token():
    """Fetches a fresh OAuth token from Bol.com"""
    token_url = "https://login.bol.com/token?grant_type=client_credentials"
    auth = HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET)
    
    try:
        response = requests.post(
            token_url, 
            auth=auth, 
            headers={"Accept": "application/json"}
        )
        response.raise_for_status()
        return response.json()["access_token"]
    except requests.RequestException as e:
        print(f"Auth Error: {e}")
        return None

def fetch_invoice_spec(invoice_id, access_token):
    """Downloads the JSON specification for the invoice"""
    url = f"https://api.bol.com/retailer/invoices/{invoice_id}/specification"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.retailer.v10+json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Fetch Error: {e}")
        return None

def calculate_invoice_totals(invoice_data, target_ean=None):
    """
    Parses the invoice JSON and calculates totals.
    If target_ean is provided, filters for that EAN.
    If not, returns totals for ALL EANs found.
    """
    
    # Storage for results: { "EAN123": { "revenue": 0, "commission": 0 ... } }
    results = {}

    lines = invoice_data.get("invoiceSpecification", [])

    for line in lines:
        item = line.get("item", {})
        
        # --- 1. EXTRACT EAN ---
        ean = "UNKNOWN"
        props = item.get("AdditionalItemProperty", [])
        
        # Try to find explicit EAN property
        for p in props:
            if p.get("Name", {}).get("value") == "EAN":
                ean = p.get("Value", {}).get("value")
                break
        
        # Fallback to looking for 13-digit number
        if ean == "UNKNOWN":
            for p in props:
                val = p.get("Value", {}).get("value", "")
                if val and val.isdigit() and len(val) >= 13:
                    ean = val
                    break
        
        # Filter if a specific EAN was requested
        if target_ean and ean != target_ean:
            continue
            
        # Initialize dictionary for this EAN if new
        if ean not in results:
            results[ean] = {
                "revenue": 0.0,
                "commission": 0.0,
                "ads_cost": 0.0,
                "shipping": 0.0,
                "other": 0.0
            }

        # --- 2. EXTRACT AMOUNT ---
        amount = float(line.get("lineExtensionAmount", {}).get("value", 0.0))
        
        # --- 3. CLASSIFY ---
        name = item.get("Name", {}).get("value", "").upper()
        desc_list = item.get("Description", [])
        description = desc_list[0].get("value", "").lower() if desc_list else ""

        # Revenue (Invert Logic)
        if name in ["TURNOVER", "CORRECTION_TURNOVER"]:
            results[ean]["revenue"] += -amount
            
        # Commission
        elif name in ["COMMISSION", "CORRECTION_COMMISSION"]:
            results[ean]["commission"] += amount
            
        # Shipping
        elif name in ["PICK_PACK", "OUTBOUND", "DISTRIBUTION_BY_BOLCOM_LABEL", "PLAZA_RETURN_SHIPPING_LABEL"]:
            results[ean]["shipping"] += amount
            
        # Ads
        elif "sponsored products" in description or "advert" in description or name == "SPONSORED_PRODUCTS_ADS":
            results[ean]["ads_cost"] += amount
            
        # Other
        else:
            if "verzend" in description or "shipping" in description:
                results[ean]["shipping"] += amount
            elif "commissie" in description:
                results[ean]["commission"] += amount
            else:
                results[ean]["other"] += amount

    # --- 4. CALCULATE NET FOR ALL ---
    final_output = []
    for ean_key, data in results.items():
        net = data["revenue"] - (data["commission"] + data["shipping"] + data["ads_cost"] + data["other"])
        
        final_output.append({
            "ean": ean_key,
            "revenue": round(data["revenue"], 2),
            "commission": round(data["commission"], 2),
            "ads_cost": round(data["ads_cost"], 2),
            "shipping": round(data["shipping"], 2),
            "other": round(data["other"], 2),
            "net_result": round(net, 2)
        })

    return final_output