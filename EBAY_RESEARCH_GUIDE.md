# ⚡ eBay vs AliExpress Turbo Pro Visual Product Research Guide

Welcome to the automated **eBay vs AliExpress Turbo Pro Visual Research** dashboard in Sitecap! This system replaces manual Jupyter Notebook executions with a high-performance, scalable web platform supporting **UK, USA, and Australia (AUS)** marketplaces.

---

## 🚀 Quick Access

Once the Django development server is running (`python manage.py runserver`), open your browser to:

```
http://localhost:8000/ebay-research/
```
*(Also accessible at `http://localhost:8000/ebayresearch/`)*

---

## 🌟 Key Features & Capabilities

### 1. 🌍 Multi-Country / Multi-Marketplace Support
Seamlessly switch between target markets with one click:
- 🇬🇧 **United Kingdom (UK)**: `EBAY_GB` marketplace, `ebay.co.uk`, currency `£` (GBP), AliExpress direct shipping to `GB`.
- 🇺🇸 **United States (USA)**: `EBAY_US` marketplace, `ebay.com`, currency `$` (USD), AliExpress direct shipping to `US`.
- 🇦🇺 **Australia (AUS)**: `EBAY_AU` marketplace, `ebay.com.au`, currency `AU$` (AUD), AliExpress direct shipping to `AU`.
- 🌐 **Auto-Detect**: Automatically identifies marketplace per listing by parsing domains (`.co.uk`, `.com.au`, `.com`).

---

### 2. 🔑 Client-Side Credential Storage & Token Expiration Alerts
- **Cookie & LocalStorage Persistence**:
  Click **API Credentials & Keys** in the header. Enter your eBay and AliExpress credentials. They are saved directly into your browser's cookies and local storage, persisting across sessions.
- **Pre-configured Defaults**:
  Pre-loaded with your working credentials (`EBAY_CLIENT_ID`, `EBAY_CERT_ID`, `ALI_DS_KEY`, `ALI_DS_SECRET`, `ALI_DS_TOKEN`).
- **Live Connection Test**:
  Test your eBay and AliExpress keys independently directly from the UI before running searches.
- **Smart Expiration & Rate Limit Toasts**:
  When a token expires, an API session lapses, or a rate limit is exceeded, formatted interactive toasts appear with direct action buttons (`[Change Tokens Now]`) that instantly open the credentials drawer focused on the exact field.

---

### 3. ⚡ High-Throughput eBay Bulk Browse API
- Retrieves item metadata in parallel batches of **20 items per request** using eBay's Browse Bulk Item API.
- Eliminates `429 Rate Limits`.
- Automatically queries fallback item groups for multi-variation listings.
- Extracts sold counts and calculates listing ages (e.g. `1.8d`).

---

### 4. 🧠 Deep Visual AI Re-Ranking (CLIP ViT-B-32)
- Downloads item photos and crops 9% borders to remove promotional watermarks and badges.
- Queries AliExpress Dropshipping Image Search API (`aliexpress.ds.image.search`) via HMAC-SHA256 signature.
- Computes cosine similarity embeddings with `SentenceTransformer("clip-ViT-B-32")`.
- Ranks matches using visual similarity + title keyword overlap + seller order volume and Choice/Top trust ratings.

---

### 5. 📊 Interactive Dashboard & Match Switcher
- **Top 3 Match Switching**:
  For each eBay listing, toggle between candidates `#1`, `#2`, and `#3`. The table dynamically recalculates the price, profit spread, visual match %, and supplier link instantly.
- **Live Search & Filter Toolbar**:
  - Sort by: Most Recently Listed, Best Visual Match %, Most Sold, Price Low-to-High, Price High-to-Low, Highest Profit Spread.
  - Title & Seller include keyword search (instant typing filter).
  - Comma-separated exclude filter (e.g. `refurbished, parts, broken`).
  - Presets: All Listings, Only 70%+ AliExpress Matches, Only Sold Data, Only Profitable Spread (> $0).
- **Full Image Zoom Modal**:
  Click any eBay or AliExpress thumbnail to enlarge high-resolution photos with listing titles.
- **Exporting**:
  - **Standalone HTML Report**: Exact self-contained dashboard you can share or open offline.
  - **CSV Export**: Spreadsheet with full item and supplier details.
  - **JSON Export**: Raw structured data.

---

## 🛠️ API Endpoints Reference

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/ebay-research/` | `GET` | Main Web Interface |
| `/ebay-research/api/run/` | `POST` | Core analysis routine (takes links, country, credentials) |
| `/ebay-research/api/test/` | `POST` | Tests eBay OAuth or AliExpress Dropshipping API connection |
| `/ebay-research/api/status/` | `GET` | Returns CLIP AI Model status (GPU/CPU/Fallback) |
| `/ebay-research/api/export/` | `POST` | Generates standalone HTML, CSV, or JSON downloads |

