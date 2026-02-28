# File Upload – Direct Google Sheet Setup

To upload data **directly** to your Google Sheet (instead of downloading CSV), you need a one-time setup.

## 1. Create a Google Service Account

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project (or select existing)
3. Enable **Google Sheets API** and **Google Drive API**
4. Go to **APIs & Services** → **Credentials** → **Create Credentials** → **Service Account**
5. Name it (e.g. "File Upload") and create
6. Click the service account → **Keys** tab → **Add Key** → **Create new key** → **JSON**
7. Save the downloaded JSON file (e.g. `key.json`)

## 2. Share Your Google Sheet

1. Open the JSON file and find `client_email` (e.g. `xxx@your-project.iam.gserviceaccount.com`)
2. Open your Google Sheet
3. Click **Share**
4. Add that email as **Editor**
5. Save

## 3. Configure the App

### Local development

**Option A – .env file**
```
GOOGLE_APPLICATION_CREDENTIALS=key.json
```
Put `key.json` in your project root.

**Option B – Django settings** (in `Sitecapture/settings.py`):
```python
GOOGLE_SHEETS_CREDENTIALS_PATH = BASE_DIR / 'key.json'
```

### Vercel (production)

1. Open your project on [Vercel](https://vercel.com) → **Settings** → **Environment Variables**
2. Add a new variable:
   - **Name:** `GOOGLE_APPLICATION_CREDENTIALS_JSON`
   - **Value:** Paste the **entire contents** of your `key.json` file (the whole JSON as one line or multi-line)
3. Redeploy your project

Example value (paste your actual JSON):
```json
{"type":"service_account","project_id":"your-project","private_key_id":"...","private_key":"-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n","client_email":"xxx@your-project.iam.gserviceaccount.com",...}
```

## 4. Install Dependencies

```bash
pip install gspread google-auth
```

## 5. Use the File Upload Page

1. Enter your Google Sheet URL (standard edit link, e.g. `https://docs.google.com/spreadsheets/d/xxx/edit`)
2. Upload your file and map columns
3. Click **Upload to Sheet** – data is written directly to the sheet
