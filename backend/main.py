"""
Receipt Scanner API - Accessibility-focused receipt processing
FastAPI backend with Gemini AI and MongoDB integration
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import os
from datetime import datetime
import base64

app = FastAPI(title="Receipt Scanner API")

# CORS middleware for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class ReceiptItem(BaseModel):
    name: str
    price: Optional[float] = None
    category: Optional[str] = None
    allergens: List[str] = []
    health_flags: List[str] = []

class Receipt(BaseModel):
    id: Optional[str] = None
    merchant: str
    date: str
    items: List[ReceiptItem]
    total: Optional[float] = None
    return_policy_days: Optional[int] = None
    return_deadline: Optional[str] = None
    image_url: Optional[str] = None
    created_at: str = datetime.utcnow().isoformat()

class HealthInsights(BaseModel):
    allergen_alerts: List[str]
    health_score: int  # 0-100
    health_warnings: List[str]  # "High sugar", "High sodium", etc.
    suggestions: List[str]
    diet_flags: Dict[str, bool]  # vegetarian, vegan, etc.

class UserProfile(BaseModel):
    allergies: List[str] = []
    dietary_preferences: List[str] = []
    health_goals: List[str] = []

@app.get("/")
async def root():
    return {
        "message": "Receipt Scanner API - Accessibility First",
        "version": "1.0.0",
        "features": ["OCR", "Allergen Detection", "Health Analysis", "Voice Support"]
    }

@app.post("/api/receipts/upload")
async def upload_receipt(file: UploadFile = File(...)):
    """
    Upload and process receipt image using Gemini Vision API
    Returns extracted receipt data
    """
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    # Read image bytes
    image_bytes = await file.read()

    # TODO: Process with Gemini API
    # For now, return mock data
    return {
        "status": "processing",
        "message": "Receipt uploaded successfully",
        "receipt_id": "temp_id_123"
    }

@app.post("/api/receipts/analyze")
async def analyze_receipt(receipt: Receipt):
    """
    Analyze receipt for health insights and allergens
    """
    # TODO: Implement health analysis logic
    insights = HealthInsights(
        allergen_alerts=["dairy", "gluten"],
        health_score=65,
        health_warnings=["High sugar content", "Processed foods detected"],
        suggestions=[
            "Consider low-sugar alternatives for yogurt",
            "Add more fresh produce to your cart"
        ],
        diet_flags={"vegetarian": False, "vegan": False, "gluten_free": False}
    )

    return insights

@app.get("/api/receipts")
async def get_receipts(limit: int = 10, offset: int = 0):
    """
    Get all receipts with pagination
    """
    # TODO: Fetch from MongoDB
    return {"receipts": [], "total": 0}

@app.get("/api/receipts/{receipt_id}")
async def get_receipt(receipt_id: str):
    """
    Get single receipt by ID
    """
    # TODO: Fetch from MongoDB
    raise HTTPException(status_code=404, detail="Receipt not found")

@app.get("/api/dashboard/stats")
async def get_dashboard_stats():
    """
    Get dashboard statistics for the week
    """
    return {
        "money_at_risk": 127.50,
        "receipts_expiring_soon": 3,
        "total_receipts": 12,
        "allergen_alerts_this_week": 5,
        "health_score_avg": 68,
        "paper_saved_count": 12
    }

@app.post("/api/text-to-speech")
async def text_to_speech(text: str):
    """
    Convert text to speech for accessibility (ElevenLabs integration)
    """
    # TODO: Integrate ElevenLabs API
    return {"audio_url": "placeholder"}

@app.post("/api/user/profile")
async def update_user_profile(profile: UserProfile):
    """
    Update user allergen and dietary preferences
    """
    # TODO: Save to MongoDB
    return {"status": "updated", "profile": profile}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
