import pypdf
import re
import io
from datetime import datetime

def clean_phone(phone_str):
    return re.sub(r"\D", "", phone_str)

def parse_hotel_date(date_str):
    date_str = date_str.strip()
    for fmt in ("%d/%b", "%d-%B", "%d-%b"):
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.replace(year=datetime.now().year)  # use current year
        except ValueError:
            continue
    return None

def extract_vehicles(text):
    """
    Parses and translates vehicle seating capacities:
    - 12 Seater -> HIACE
    - 7 Seater -> H1
    - 4 Seater -> CAR
    Combines multiple values with a '+' sign.
    """
    matches = re.findall(r"(\d+)\s*-?\s*seat", text.lower())
    codes = []
    for m in matches:
        try:
            val = int(m)
            if val == 12:
                codes.append('HIACE')
            elif val == 7:
                codes.append('H1')
            elif val == 4:
                codes.append('CAR')
        except ValueError:
            continue
    # Remove duplicates preserving order
    unique_codes = []
    for c in codes:
        if c not in unique_codes:
            unique_codes.append(c)
    return "+".join(unique_codes)

def build_route(text, has_makkah, has_madinah):
    """
    Builds the route code based on stay locations and transport details:
    e.g. MAK MED MED WITH BOTH ZIARAT+UMRA GUIDE
    """
    route = ""
    if has_makkah and has_madinah:
        route = "MAK MED"
        if "madinah airport" in text.lower() or "medinah airport" in text.lower() or "med airport" in text.lower():
            route = "MAK MED MED"
        elif "jeddah airport" in text.lower() or "jed airport" in text.lower() or "jeddah" in text.lower() or "jed" in text.lower():
            route = "MAK MED JED"
    elif has_makkah:
        route = "JED MAK JED"
    
    # Check for ziyarat and guide
    has_ziyarat = any(z in text.lower() for z in ['ziyarat', 'ziarat'])
    has_guide = any(g in text.lower() for g in ['umrah guide', 'umra guide'])
    
    if has_ziyarat and has_guide:
        route += " WITH BOTH ZIARAT+UMRA GUIDE"
    elif has_ziyarat:
        route += " WITH ZIARAT"
    elif has_guide:
        route += " WITH UMRA GUIDE"
        
    return route

def extract_travel_to_haram(pdf_file_path):
    """
    Parser for 'Travel to Haram' Agent voucher layout.
    Extracts customer info, hotels, check-in/out dates, route, vehicles, and flights.
    Falls back to OCR.space API for scanned/image-only PDFs.
    """
    reader = pypdf.PdfReader(pdf_file_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    
    # If the PDF does not contain selectable text (is scanned/image only)
    if not text.strip():
        # Fallback to OCR.space API!
        try:
            import requests
            url = "https://api.ocr.space/parse/image"
            
            # Reset seek position of the file stream to read it from start
            if hasattr(pdf_file_path, 'seek'):
                pdf_file_path.seek(0)
            
            payload = {
                'apikey': 'helloworld',
                'language': 'eng',
                'isOverlayRequired': 'false',
                'filetype': 'pdf'
            }
            # Upload the file stream
            response = requests.post(url, data=payload, files={'file': pdf_file_path}, timeout=25)
            if response.status_code == 200:
                result = response.json()
                parsed_results = result.get("ParsedResults", [])
                if parsed_results:
                    for page in parsed_results:
                        text += page.get("ParsedText", "") + "\n"
        except Exception as e:
            raise ValueError(
                f"This PDF appears to be a scanned image or photo, and the online OCR parser could not be reached: {str(e)}. "
                "Please upload a digital PDF voucher downloaded directly from the travel agency portal."
            )
            
    if not text.strip():
        raise ValueError(
            "This PDF appears to be a scanned image or photo and contains no readable text layers. "
            "Please upload the digital PDF voucher downloaded directly from the travel agency portal."
        )
        
    extracted = {
        'agent_name': 'Travel to Haram',
        'lead_pax': '',
        'mobile_no': '',
        'makkah_hotel': '',
        'makkah_check_in': '',
        'makkah_check_out': '',
        'madinah_hotel': '',
        'madinah_check_in': '',
        'madinah_check_out': '',
        'vehicles': '',
        'route': '',
        'flights': []
    }
    
    # 1. Extract Makkah & Madinah Hotel Names
    makkah_match = re.search(r"Makkah Hotel:\s*(.*)", text)
    if makkah_match:
        extracted['makkah_hotel'] = makkah_match.group(1).strip()
    
    madinah_match = re.search(r"Madina(?:h)? Hotel:\s*(.*)", text)
    if madinah_match:
        extracted['madinah_hotel'] = madinah_match.group(1).strip()

    # 2. Extract Route & Vehicles
    extracted['vehicles'] = extract_vehicles(text)
    extracted['route'] = build_route(text, bool(extracted['makkah_hotel']), bool(extracted['madinah_hotel']))

    # 3. Extract Customer Info (Lead Pax Name & Mobile No.)
    pax_match = re.search(r"Lead Pax Name[ \t]*:[ \t]*(.+)", text, re.IGNORECASE)
    if pax_match:
        extracted['lead_pax'] = pax_match.group(1).strip()
    else:
        # OCR scanned colon as dot fallback
        pax_match_dot = re.search(r"Lead Pax Name[ \t]*[\.:][ \t]*(.+)", text, re.IGNORECASE)
        if pax_match_dot:
            extracted['lead_pax'] = pax_match_dot.group(1).strip()

    support_numbers_raw = [
        "0203-355-4383", "02033554383",
        "+44 7893 927567", "+447893927567",
        "(00966) 599709855", "00966599709855",
        "+442039500763", "+442032877797",
        "442039500763", "442032877797",
        "00966 599709855"
    ]
    support_normalized = {clean_phone(n) for n in support_numbers_raw if clean_phone(n)}
    
    all_numbers = re.findall(r"\b(?:\+?\d[\d\t -]{7,15}\d)\b", text)
    customer_mobile = ""
    for num in all_numbers:
        norm = clean_phone(num)
        if len(norm) >= 10 and norm not in support_normalized:
            customer_mobile = num.strip()
            break
            
    extracted['mobile_no'] = customer_mobile
    
    # Fallback to search relative to mobile if Lead Pax Name match failed
    if not extracted['lead_pax'] and customer_mobile:
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        for idx, line in enumerate(lines):
            if customer_mobile in line:
                if idx > 0:
                    potential_name = lines[idx-1]
                    if re.match(r"^[A-Za-z\s\.\'-]+$", potential_name):
                        extracted['lead_pax'] = potential_name
                    else:
                        if idx > 1 and re.match(r"^[A-Za-z\s\.\'-]+$", lines[idx-2]):
                            extracted['lead_pax'] = lines[idx-2]
                break

    # 4. Chronological Stay-to-Date Alignment (Handles multiple hotels/orders)
    headers = []
    matches = re.finditer(r"(Makkah|Madina|Madinah|Jeddah)[ \t]*Hotel", text, re.IGNORECASE)
    for m in matches:
        h_type = m.group(1).lower()
        if h_type == 'madina':
            h_type = 'madinah'
        headers.append(h_type)
        
    date_matches = re.findall(r"(\d{1,2}/[A-Za-z]{3})", text)
    cleaned_dates = []
    for d in date_matches:
        m = re.search(r"(\d{1,2}/[A-Za-z]{3})", d)
        if m:
            cleaned_dates.append(m.group(1))
            
    parsed_dates = []
    seen_dstr = set()
    for d in cleaned_dates:
        if d not in seen_dstr:
            dt = parse_hotel_date(d)
            if dt:
                parsed_dates.append((d, dt))
                seen_dstr.add(d)
    parsed_dates.sort(key=lambda x: x[1])
    sorted_dates = [x[0] for x in parsed_dates]
    
    stays = []
    for i in range(len(sorted_dates) - 1):
        stays.append((sorted_dates[i], sorted_dates[i+1]))
        
    for idx, h_type in enumerate(headers):
        if idx < len(stays):
            stay_in, stay_out = stays[idx]
            if h_type == 'makkah':
                extracted['makkah_check_in'] = stay_in
                extracted['makkah_check_out'] = stay_out
            elif h_type == 'madinah':
                extracted['madinah_check_in'] = stay_in
                extracted['madinah_check_out'] = stay_out

    # 5. Flights
    flights = re.findall(r"\b((?:SV|TK|EK|QR|WY|EY|XY|KU|MS)\d{3,4})\b", text)
    extracted['flights'] = list(set(flights))
    
    return extracted
