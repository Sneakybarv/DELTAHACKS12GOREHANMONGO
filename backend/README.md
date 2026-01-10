# Receipt Scanner Backend

Accessibility-focused receipt scanner API built with FastAPI, Gemini Vision AI, and MongoDB Atlas.

## Features

- **Gemini Vision API Integration**: Advanced receipt scanning using Google's Gemini 2.5 Flash model with multimodal capabilities
- **Intelligent OCR**: Extracts merchant name, date, items, prices, and totals from receipt images with high accuracy
- **Health Analysis**: AI-powered nutritional analysis, allergen detection, and dietary recommendations
- **Return Policy Tracking**: Automatically calculate return deadlines for 20+ major retailers
- **Accessibility-First**: Natural language text summaries optimized for text-to-speech and screen readers
- **MongoDB Storage**: Persistent storage of receipts and user preferences
- **Security**: Built-in rate limiting (50 req/min), image validation, and input sanitization

## Gemini Vision Capabilities

This backend uses **Gemini 2.5 Flash** with vision capabilities to:

1. **Scan Receipt Images**: Processes JPG, PNG, WebP images up to 10MB
2. **Extract Structured Data**: Converts receipt images to JSON with:
   - Merchant name
   - Purchase date
   - Itemized list with prices
   - Total, subtotal, and tax
   - Payment method
   - Return policy information

3. **Health Analysis**: Analyzes purchased items for:
   - Allergen detection (dairy, nuts, gluten, soy, etc.)
   - Health score (0-100)
   - Nutritional warnings
   - Dietary flags (vegetarian, vegan, gluten-free)
   - Personalized suggestions

## Setup

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your API keys:

```bash
cp .env.example .env
```

Required API keys:
- **MongoDB Atlas URI**: Sign up at [mongodb.com/cloud/atlas](https://www.mongodb.com/cloud/atlas)
- **Gemini API Key**: Get from [ai.google.dev](https://ai.google.dev/)
- Optional: **ElevenLabs API Key** for text-to-speech

### 3. MongoDB Atlas Setup

1. Create a free cluster at [mongodb.com/cloud/atlas](https://www.mongodb.com/cloud/atlas)
2. Create a database named `receipt_scanner`
3. Add your IP address to the network access list
4. Create a database user
5. Copy the connection string to `.env` as `MONGODB_URI`

### 4. Run the Server

```bash
python main.py
```

Or with uvicorn:

```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

## API Documentation

Once running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Endpoints

### Receipt Processing
- `POST /api/receipts/upload` - Upload receipt image
- `POST /api/receipts/analyze` - Analyze receipt for health insights
- `GET /api/receipts` - Get all receipts (paginated)
- `GET /api/receipts/{id}` - Get single receipt

### Dashboard
- `GET /api/dashboard/stats` - Get dashboard statistics

### Accessibility
- `POST /api/text-to-speech` - Convert receipt text to speech

### User Profile
- `POST /api/user/profile` - Update allergen preferences

## Project Structure

```
backend/
├── main.py              # FastAPI app and routes
├── database.py          # MongoDB connection and operations
├── gemini_service.py    # Gemini API integration
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variables template
└── README.md           # This file
```

## Testing

### Test with curl:

```bash
# Health check
curl http://localhost:8000/

# Upload and scan receipt with Gemini Vision
curl -X POST http://localhost:8000/api/receipts/upload \
  -F "file=@/path/to/receipt.jpg" \
  -H "Content-Type: multipart/form-data"

# Expected Response:
{
  "status": "success",
  "message": "Receipt processed successfully",
  "data": {
    "merchant": "Whole Foods Market",
    "date": "2026-01-10",
    "items": [
      {"name": "Organic Milk", "price": 5.99, "category": "groceries"},
      {"name": "Bananas", "price": 2.49, "category": "groceries"}
    ],
    "total": 8.48,
    "subtotal": 7.99,
    "tax": 0.49,
    "return_policy_days": 90,
    "return_deadline": "2026-04-10",
    "text_summary": "Receipt from Whole Foods Market on 2026-01-10. Total: $8.48...",
    "processed_at": "2026-01-10T12:34:56.789Z"
  }
}
```

### Test Health Analysis:

```bash
curl -X POST http://localhost:8000/api/receipts/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "merchant": "Grocery Store",
    "date": "2026-01-10",
    "items": [
      {"name": "Whole Milk", "price": 4.99},
      {"name": "Peanut Butter", "price": 6.49},
      {"name": "Bread", "price": 3.99}
    ],
    "total": 15.47
  }'

# Expected Response:
{
  "allergen_alerts": ["dairy", "nuts", "gluten"],
  "health_score": 65,
  "health_warnings": ["Contains dairy", "High in saturated fat"],
  "suggestions": ["Consider almond milk as dairy-free alternative"],
  "diet_flags": {
    "vegetarian_friendly": true,
    "vegan_friendly": false,
    "gluten_free": false
  }
}
```

## How Gemini Vision Works

The `gemini_service.py` module uses **LangChain** with **Google Generative AI** to:

1. **Accept Image Input**: Receives receipt image as bytes
2. **Encode Image**: Converts to base64 for API transmission
3. **Create Vision Prompt**: Sends detailed extraction instructions to Gemini
4. **Parse Response**: Extracts JSON data from AI response
5. **Enhance Data**: Adds return policies and deadlines
6. **Generate Summary**: Creates accessible text for screen readers

### Key Functions:

- `extract_receipt_data(image_bytes)` - Main vision OCR function
- `analyze_receipt_health(items)` - Health and allergen analysis
- `generate_receipt_summary_text(receipt_data)` - Accessibility summary

## Sponsor Prize Eligibility

This backend qualifies for:
- ✅ **MLH Best Use of Gemini API** - Receipt OCR and health analysis
- ✅ **MLH Best Use of MongoDB Atlas** - Receipt and user data storage
- ⏳ **MLH Best Use of ElevenLabs** - Optional text-to-speech (TODO)

## Next Steps

1. Integrate ElevenLabs API for text-to-speech
2. Add user authentication
3. Implement caching for faster responses
4. Add batch processing for multiple receipts
5. Create webhook for real-time updates
