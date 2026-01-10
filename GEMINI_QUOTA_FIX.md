# Gemini Quota & API Key Fixes

## Issues Fixed

### 1. Missing X-Api-Key Error ✅
**Problem**: Frontend was getting "Missing X-Api-Key" error when uploading receipts.

**Solution**: Removed API key requirement from user-facing endpoints (`/api/receipts/upload` and `/api/user/profile`). The API key is now only required for admin/judge endpoints.

### 2. Gemini Model Rotation ✅
**Problem**: Some model names in the rotation sequence were invalid.

**Solution**: Updated to use valid Gemini model names:
- `gemini-1.5-flash` (fastest, cheapest - tried first)
- `gemini-1.5-pro` (more powerful)
- `gemini-2.0-flash-exp` (experimental)
- `gemini-exp-1206` (latest experimental)

The system will automatically try each model in sequence until one succeeds.

### 3. Bypass Gemini Entirely (When Quota is Exhausted) ✅
**New Feature**: Added `FORCE_OCR` environment variable to completely bypass Gemini API.

## How to Use

### Normal Mode (with Gemini)
```bash
cd backend
python main.py
```

### OCR-Only Mode (bypass Gemini when quota exhausted)
```bash
cd backend
FORCE_OCR=true python main.py
```

**Note**: OCR-only mode uses local text parsing instead of Gemini AI. It's less accurate but doesn't use any API quota.

## Current Backend Status
✅ Backend is running on http://localhost:8000 with `FORCE_OCR=true`

This means:
- Receipt uploads will work WITHOUT using Gemini quota
- OCR will extract text using Tesseract
- Local regex parsing will extract items, prices, and totals
- No API key required for uploads

## Testing Receipt Upload

You can now:
1. Go to http://localhost:3002/upload
2. Upload a receipt image
3. It will process using OCR-only (no Gemini quota used)

## Custom Model Sequence (Advanced)

If you want to use specific Gemini models, set the environment variable:

```bash
export GEMINI_MODEL_SEQUENCE="gemini-1.5-flash,gemini-1.5-pro"
cd backend
python main.py
```

## Judge API Key (For Testing/Judging)

The `/api/admin/issue-key` endpoint can create API keys for judges. Admin endpoints still require authentication:

```bash
curl -X POST http://localhost:8000/api/admin/issue-key \
  -H "X-Admin-Key: your-admin-key" \
  -H "Content-Type: application/json"
```

Set `ADMIN_KEY` environment variable to enable this feature.
