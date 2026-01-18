# Quick Configuration Guide 🔧

## Change Security Code

**File**: `API/views.py`  
**Line**: ~79

```python
SECURITY_CODE = "9890"  # Change this value
```

**Example**:
```python
SECURITY_CODE = "1234"  # Your new code
```

---

## Change Google Sheet URL

**File**: `API/views.py`  
**Line**: ~80-84

```python
GOOGLE_SHEET_CSV_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "YOUR_SHEET_ID_HERE"
    "/export?format=csv"
)
```

**How to get your Google Sheet CSV URL**:
1. Open your Google Sheet
2. Go to: File → Share → Publish to web
3. Choose "Comma-separated values (.csv)"
4. Select the sheet you want
5. Click "Publish"
6. Copy the URL

---

## Change Colors/Theme

**File**: `API/templates/API/pilgrim_schedule.html`  
**Location**: Inside `<style>` tag, `:root` section

```css
:root {
    --primary-color: #0a5f38;      /* Main green - Change this */
    --secondary-color: #d4af37;    /* Gold - Change this */
    --accent-color: #8b4513;       /* Brown - Change this */
    --text-dark: #2c3e50;          /* Dark text */
    --text-light: #ecf0f1;         /* Light text */
}
```

**Color Ideas**:
- Blue theme: `--primary-color: #1e3a8a;`
- Purple theme: `--primary-color: #6b21a8;`
- Red theme: `--primary-color: #991b1b;`

---

## Change Page Title/Headers

**File**: `API/templates/API/pilgrim_schedule.html`

### Main Title (Line ~274)
```html
<h1>
    <span class="icon">🕌</span>
    <span>Pilgrim Travel Schedules</span>  <!-- Change this -->
    <span class="icon">✈️</span>
</h1>
```

### Subtitle (Line ~278)
```html
<p>Professional Travel Management System</p>  <!-- Change this -->
```

### Lock Screen Title (Line ~285)
```html
<h2 class="security-title">Secure Access Required</h2>  <!-- Change this -->
```

---

## Change Date Format Instructions

**File**: `API/templates/API/pilgrim_schedule.html`  
**Line**: ~317

```html
<small style="color: #666; margin-top: 8px; display: block;">
    Format: DD-MMM (e.g., 13-Jan, 25-Feb, 01-Mar)  <!-- Change this -->
</small>
```

---

## Modify Schedule Logic

**File**: `API/views.py`  
**Method**: `_generate_schedule()` (starts at line ~104)

**⚠️ WARNING**: This contains your original Jupyter notebook logic.  
Only modify if you know what you're doing!

### Common modifications:
- Change static time (line ~201):
```python
static_time="10:00 AM"  # Change default time
```

- Modify schedule titles (lines ~182, 190, 198, 207):
```python
"SCHEDULE 1 – JED → MAKKAH"  # Change schedule names
```

---

## Add More Schedules

To add a 5th schedule:

**File**: `API/views.py`  
**Location**: At the end of `_generate_schedule()` method

```python
# Add before: return final_output
+
build_schedule(
    df[df["YOUR_FILTER_COLUMN"] == input_date_raw],
    "SCHEDULE 5 – YOUR ROUTE",
    {
        "booking": "TR / مواصلات",
        "route": "ROUT",
        "pickup": "YOUR_PICKUP_COLUMN",
        "time": "YOUR_TIME_COLUMN",
        "drop": "YOUR_DROP_COLUMN",
        "client": "FAMILY NAME",
        "mobile": "MOBILE NO.",
        "agent": "AGENT NAME / اسم وكيل"
    }
)
```

---

## Enable/Disable Security Code

To disable security code (not recommended):

**File**: `API/templates/API/pilgrim_schedule.html`  
**Line**: ~283

Change:
```html
<div class="security-screen active" id="securityScreen">
```
To:
```html
<div class="security-screen" id="securityScreen">
```

And change line ~300:
```html
<div class="schedule-screen" id="scheduleScreen">
```
To:
```html
<div class="schedule-screen active" id="scheduleScreen">
```

---

## Change Icons

**File**: `API/templates/API/pilgrim_schedule.html`

Available emoji icons you can use:
- 🕌 Mosque
- ✈️ Airplane
- 🚌 Bus
- 🏨 Hotel
- 📅 Calendar
- 🔒 Lock
- 🚀 Rocket
- 📍 Location Pin
- ⏰ Clock
- 🌙 Crescent Moon
- ⭐ Star

Replace in HTML:
```html
<span class="icon">🕌</span>  <!-- Change emoji here -->
```

---

## After Making Changes

**Always restart the Django server**:
1. Stop server: Press `Ctrl+C` in terminal
2. Start again: `python manage.py runserver`
3. Refresh browser: Press `F5` or `Ctrl+F5`

---

## Need Help?

All configuration changes are marked with comments in the code:
- Look for `# <-- change here` comments
- Look for `# Configuration - Easy to change` sections
- Check variable names in CAPS (e.g., `SECURITY_CODE`)

**Original logic is preserved** - Don't modify unless necessary!

