# Pilgrim Travel Schedule System - Setup Complete ✅

## 🎉 What Was Created

A fully responsive, professional, and attractive landing page for managing pilgrim travel schedules with the following features:

### 1. **Security Code Protection**
   - Landing page requires a security code (9890) before access
   - Beautiful lock screen with smooth animations
   - Invalid code handling with error messages

### 2. **Schedule Generation**
   - Date input field for generating schedules
   - Supports flexible date formats (e.g., 13-Jan, JAN-13)
   - Real-time schedule generation from Google Sheets
   - Beautiful display of 4 different schedule types:
     - Schedule 1: JED → MAKKAH
     - Schedule 2: MAKKAH → MADINAH
     - Schedule 3: MADINAH → AIRPORT
     - Schedule 4: MAKKAH → JED

### 3. **Professional Design**
   - ✨ Fully responsive (mobile, tablet, desktop)
   - 🎨 Professional pilgrim travel theme with green/gold colors
   - 🕌 Islamic-themed icons and styling
   - 💫 Smooth animations and transitions
   - 🔄 Loading indicators
   - 📱 Mobile-first design approach

## 📁 Files Created/Modified

### 1. **API/views.py**
   - Added `PilgrimScheduleView` class
   - Integrated your exact Jupyter notebook logic (unchanged)
   - Handles security code verification
   - Generates schedules from Google Sheets

### 2. **API/urls.py**
   - Added route: `path('', PilgrimScheduleView.as_view(), name='pilgrim-schedule')`
   - Accessible at: `http://localhost:8000/api/`

### 3. **API/templates/API/pilgrim_schedule.html**
   - Beautiful, professional HTML template
   - Fully responsive CSS
   - Interactive JavaScript for form handling
   - AJAX-based communication (no page reloads)

### 4. **requirements.txt**
   - Added `pandas` dependency

## 🚀 How to Use

### Step 1: Install Dependencies (if needed)
```bash
pip install -r requirements.txt
```

### Step 2: Start Django Server
```bash
cd "C:\Users\AHmEd_RajpOoT\Desktop\New API Django\Sitecap"
python manage.py runserver
```

### Step 3: Access the Application
Open your browser and navigate to:
```
http://localhost:8000/api/
```

### Step 4: Enter Security Code
- Enter: **9890**
- Click "Unlock Access"

### Step 5: Generate Schedules
- Enter a date (e.g., "13-Jan" or "JAN-13")
- Click "Generate Schedules"
- View the beautiful results!

## ⚙️ Easy Configuration

All settings are in `API/views.py` in the `PilgrimScheduleView` class:

```python
class PilgrimScheduleView(View):
    # Configuration - Easy to change
    SECURITY_CODE = "9890"  # <-- Change security code here
    GOOGLE_SHEET_CSV_URL = (
        "https://docs.google.com/spreadsheets/d/"
        "1F475ZKlJ3OdcMmqnaVJki91OlOikX78mHwKa1fPCD9s"
        "/export?format=csv"
    )  # <-- Change Google Sheet URL here
```

### To Change Security Code:
1. Open `API/views.py`
2. Find line: `SECURITY_CODE = "9890"`
3. Change to your desired code
4. Save and restart server

### To Change Google Sheet:
1. Open `API/views.py`
2. Find `GOOGLE_SHEET_CSV_URL`
3. Replace with your Google Sheet export URL
4. Save and restart server

### To Modify Colors/Theme:
1. Open `API/templates/API/pilgrim_schedule.html`
2. Find the `:root` section in `<style>`
3. Change CSS variables:
   ```css
   :root {
       --primary-color: #0a5f38;      /* Main green color */
       --secondary-color: #d4af37;    /* Gold color */
       --accent-color: #8b4513;       /* Brown accent */
       /* ... modify as needed ... */
   }
   ```

## 📱 Responsive Breakpoints

The design automatically adapts to:
- **Desktop**: 1200px+ (Full layout)
- **Tablet**: 768px-1199px (Medium layout)
- **Mobile**: 480px-767px (Compact layout)
- **Small Mobile**: <480px (Extra compact)

## 🔒 Security Features

- CSRF token protection (Django built-in)
- Password-type input for security code
- Session-based access control
- No direct data exposure

## 🎨 Design Features

- **Modern Gradient Background**: Professional green theme
- **Smooth Animations**: Fade-in, slide-in effects
- **Loading States**: Spinners and loading text
- **Error Handling**: Beautiful error messages
- **Custom Scrollbar**: Styled for the schedule output
- **Icons**: Emoji-based (universally supported)
- **Typography**: Clean, readable fonts

## 📊 Your Original Logic

**✅ Your original Jupyter notebook logic is 100% preserved!**

The `_generate_schedule()` method contains your exact code:
- Date parsing logic
- Google Sheets data fetching
- All 4 schedule filters
- Schedule building functions
- Static time handling
- All column mappings

**Nothing was changed in the logic - only wrapped in a Django view!**

## 🛠️ Testing

### Test Security Code
1. Go to `http://localhost:8000/api/`
2. Try wrong code → Should show error
3. Enter "9890" → Should unlock

### Test Schedule Generation
1. After unlocking, enter "13-Jan"
2. Click "Generate Schedules"
3. Should display all 4 schedules
4. Try different dates to verify

### Test Responsiveness
1. Open browser DevTools (F12)
2. Toggle device toolbar
3. Test on different screen sizes
4. Verify layout adapts properly

## 📝 Notes

- The page uses AJAX, so no page reloads occur
- All data comes from your Google Sheet in real-time
- The design is production-ready
- Works on all modern browsers
- No external dependencies (Bootstrap, jQuery, etc.)
- Pure HTML, CSS, and vanilla JavaScript

## 🎯 Future Customization Ideas

You can easily:
1. Add more date formats
2. Export schedules to PDF
3. Add print functionality
4. Include more filters
5. Add admin dashboard
6. Implement user authentication
7. Add schedule notifications
8. Create mobile app version

## ✅ Status: COMPLETE & READY TO USE! 🚀

Your pilgrim travel schedule system is now fully functional, beautiful, and production-ready!

---

**Created by**: AI Assistant  
**Date**: January 18, 2026  
**Technology Stack**: Django, Pandas, HTML5, CSS3, JavaScript (Vanilla)

