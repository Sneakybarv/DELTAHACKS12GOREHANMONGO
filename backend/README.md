# Receipt Scanner Backend

Accessibility-focused receipt scanner API built with FastAPI, Gemini AI, and MongoDB Atlas.

## Features

- **Receipt OCR**: Extract text and structured data from receipt images using Gemini Vision API
- **Health Analysis**: Detect allergens, analyze nutrition, and provide health insights
- **Return Policy Tracking**: Automatically calculate return deadlines
- **Accessibility**: Text-to-speech summaries for screen reader users
- **MongoDB Storage**: Persistent storage of receipts and user preferences

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

Test the API with curl:

```bash
# Health check
curl http://localhost:8000/

# Upload receipt (replace with actual image path)
curl -X POST http://localhost:8000/api/receipts/upload \
  -F "file=@receipt.jpg"
```

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
