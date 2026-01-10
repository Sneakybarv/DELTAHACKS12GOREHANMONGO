# Quick Fix Guide

## ✅ Fixed Issues

### 1. White Text Problem - FIXED
**Cause**: Dark mode was enabled but pages weren't fully compatible

**Solution**: Updated `frontend/app/globals.css` to force text visibility in dark mode

**How to verify**:
1. Go to http://localhost:3002
2. If text is still white, click the "Dark Mode" button in the top toolbar to toggle it OFF
3. Or just refresh the page - CSS now forces dark gray text to show as light gray in dark mode

### 2. Missing API Key Error - FIXED
**Cause**: Backend required API key for user endpoints

**Solution**: Removed `require_api_key` from user-facing endpoints in `backend/main.py`

**Verify**: Upload should now work without API key errors

### 3. Gemini Model Issues - FIXED
**Cause**: Invalid model names in rotation sequence

**Solution**: Updated to valid models in `backend/gemini_service.py:30-33`

**Current models**: `gemini-1.5-flash`, `gemini-1.5-pro`, `gemini-2.0-flash-exp`, `gemini-exp-1206`

### 4. OCR-Only Mode - NEW FEATURE
**Feature**: Bypass Gemini entirely when quota exhausted

**Current Status**: Backend is running with `FORCE_OCR=true`

**What this means**:
- No Gemini API calls = No quota used
- Uses Tesseract OCR + local regex parsing
- Less accurate but always works

## 📝 Testing Receipt Upload

### Step 1: Check Frontend
```bash
# Open in browser
open http://localhost:3002
```

### Step 2: Upload a Receipt
1. Go to http://localhost:3002/upload
2. Click "Browse Files" or drag-drop a receipt image
3. Select receipt type (Grocery or Restaurant)
4. Click "Generate Health Insights"

### Step 3: Check What Was Extracted
The backend will show in logs what it extracted. To see:

```bash
tail -f /tmp/backend.log
```

Then upload a receipt and watch the log output.

## 🐛 If Receipt Parsing is Still Wrong

The OCR parsing logic is in `backend/gemini_service.py`:
- Lines 184-334: `parse_ocr_text_to_receipt()` - Local parsing function
- Lines 337-633: `extract_receipt_data()` - Main extraction with Gemini fallback

**Common issues**:
1. **Quantity not detected**: Receipt format must be `QTY ItemName UnitPrice Total`
   - Example: `4 Cheese Burger 5.99 23.96`
   - If receipt has different format, parsing will fail

2. **Wrong totals**: Parser looks for "Total to Pay" or "Grand Total"
   - If your receipt uses different wording, it won't find it

3. **Promotional text extracted**: Parser tries to filter but might miss some

**To debug**:
1. Upload a receipt
2. Check `/tmp/backend.log` for the extracted OCR text
3. Share the OCR text output here
4. I can then fix the regex patterns to match your receipt format

## 🔧 Quick Commands

```bash
# Check if servers are running
curl -s http://localhost:8000/ | jq
curl -s http://localhost:3002 | head -5

# View backend logs in real-time
tail -f /tmp/backend.log

# Restart backend WITHOUT Gemini (OCR only)
pkill -f "main.py" && sleep 1
cd /Users/barzinvazifedoost/DeltaHACKSrealREHAN/backend
FORCE_OCR=true python3 main.py > /tmp/backend.log 2>&1 &

# Restart backend WITH Gemini
pkill -f "main.py" && sleep 1
cd /Users/barzinvazifedoost/DeltaHACKSrealREHAN/backend
python3 main.py > /tmp/backend.log 2>&1 &

# Restart frontend
cd /Users/barzinvazifedoost/DeltaHACKSrealREHAN/frontend
npm run dev
```

## 📊 Next Steps

1. **Test white text fix**: Refresh browser or toggle dark mode
2. **Test receipt upload**: Upload a sample receipt
3. **If parsing wrong**: Share the backend log output showing OCR text
4. **If still issues**: Let me know the specific problem and I'll debug further
