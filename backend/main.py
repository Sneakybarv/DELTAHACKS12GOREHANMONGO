"""
Receipt Scanner API - Accessibility-focused receipt processing
FastAPI backend with Gemini AI and MongoDB integration
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import os
from datetime import datetime, timezone
import base64
from security import (
    rate_limit_check,
    validate_image_upload,
    sanitize_user_input,
    validate_receipt_data,
    get_cors_origins
)
from gemini_service import (
    extract_receipt_data,
    analyze_receipt_health,
    generate_receipt_summary_text
)

app = FastAPI(
    title="Receipt Scanner API",
    description="Accessibility-first receipt processing with AI",
    version="1.0.0"
)

# Get environment
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# CORS middleware with environment-based origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(ENVIRONMENT),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    max_age=3600,  # Cache preflight requests for 1 hour
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
    created_at: str = datetime.now(timezone.utc).isoformat()

class HealthInsights(BaseModel):
    allergen_alerts: List[str]
    health_score: int  # 0-100
    health_warnings: List[str]
    suggestions: List[str]
    diet_flags: Dict[str, bool]

class UserProfile(BaseModel):
    allergies: List[str] = []
    dietary_preferences: List[str] = []
    health_goals: List[str] = []

@app.get("/")
async def root():
    return {
        "message": "Receipt Scanner API - Accessibility First",
        "version": "1.0.0",
        "features": ["OCR", "Allergen Detection", "Health Analysis", "Voice Support"],
        "environment": ENVIRONMENT
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for deployment monitoring"""
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}

@app.post("/api/receipts/upload")
async def upload_receipt(
    request: Request,
    file: UploadFile = File(...),
    _: None = Depends(rate_limit_check)
):
    """
    Upload and process receipt image using Gemini Vision API
    Returns extracted receipt data

    Rate limited to 50 requests per minute per IP
    """
    try:
        # Validate content type
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")

        # Read and validate image
        image_bytes = await file.read()
        validate_image_upload(image_bytes, max_size_mb=10)

        # Process receipt with Gemini Vision API
        receipt_data = await extract_receipt_data(image_bytes)
        
        # Generate accessible text summary
        text_summary = await generate_receipt_summary_text(receipt_data)
        
        # Add the text summary to the response
        receipt_data["text_summary"] = text_summary
        receipt_data["image_size_bytes"] = len(image_bytes)
        receipt_data["processed_at"] = datetime.now(timezone.utc).isoformat()
        
        return {
            "status": "success",
            "message": "Receipt processed successfully",
            "data": receipt_data
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Error processing receipt: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to process receipt. Please try again with a clearer image."
        )

@app.post("/api/receipts/analyze")
async def analyze_receipt(
    request: Request,
    receipt: Receipt,
    _: None = Depends(rate_limit_check)
):
    """
    Analyze receipt for health insights and allergens using Gemini AI

    Rate limited to 50 requests per minute per IP
    """
    try:
        # Validate receipt data
        validate_receipt_data(receipt.dict())

        # Sanitize merchant name
        receipt.merchant = sanitize_user_input(receipt.merchant, max_length=200)

        # Sanitize item names
        for item in receipt.items:
            item.name = sanitize_user_input(item.name, max_length=200)

        # Analyze health data using Gemini
        items_dict = [item.dict() for item in receipt.items]
        health_data = await analyze_receipt_health(items_dict)
        
        insights = HealthInsights(
            allergen_alerts=health_data.get("allergen_alerts", []),
            health_score=health_data.get("health_score", 50),
            health_warnings=health_data.get("health_warnings", []),
            suggestions=health_data.get("suggestions", []),
            diet_flags=health_data.get("diet_flags", {})
        )

        return insights
    
    except Exception as e:
        print(f"Error analyzing receipt: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to analyze receipt. Please try again."
        )

@app.get("/api/receipts")
async def get_receipts(
    request: Request,
    limit: int = 10,
    offset: int = 0,
    _: None = Depends(rate_limit_check)
):
    """
    Get all receipts with pagination

    Rate limited to 50 requests per minute per IP
    """
    # Validate pagination params
    if limit > 100:
        raise HTTPException(status_code=400, detail="Limit cannot exceed 100")
    if limit < 1:
        raise HTTPException(status_code=400, detail="Limit must be at least 1")
    if offset < 0:
        raise HTTPException(status_code=400, detail="Offset cannot be negative")

    # TODO: Fetch from MongoDB
    return {"receipts": [], "total": 0}

@app.get("/api/receipts/{receipt_id}")
async def get_receipt(
    receipt_id: str,
    request: Request,
    _: None = Depends(rate_limit_check)
):
    """
    Get single receipt by ID

    Rate limited to 50 requests per minute per IP
    """
    # Sanitize receipt_id to prevent injection
    receipt_id = sanitize_user_input(receipt_id, max_length=50)

    # TODO: Fetch from MongoDB
    raise HTTPException(status_code=404, detail="Receipt not found")

@app.get("/api/dashboard/stats")
async def get_dashboard_stats(
    request: Request,
    _: None = Depends(rate_limit_check)
):
    """
    Get dashboard statistics for the week

    Rate limited to 50 requests per minute per IP
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
async def text_to_speech(
    text: str,
    request: Request,
    _: None = Depends(rate_limit_check)
):
    """
    Convert text to speech for accessibility

    Rate limited to 50 requests per minute per IP
    """
    # Sanitize and validate input
    text = sanitize_user_input(text, max_length=5000)

    if not text:
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    # TODO: Integrate ElevenLabs API or Web Speech API
    return {"audio_url": "placeholder", "text_length": len(text)}

@app.post("/api/user/profile")
async def update_user_profile(
    profile: UserProfile,
    request: Request,
    _: None = Depends(rate_limit_check)
):
    """
    Update user allergen and dietary preferences

    Rate limited to 50 requests per minute per IP
    """
    # Sanitize profile data
    profile.allergies = [sanitize_user_input(a, 50) for a in profile.allergies[:20]]
    profile.dietary_preferences = [sanitize_user_input(d, 50) for d in profile.dietary_preferences[:20]]
    profile.health_goals = [sanitize_user_input(g, 100) for g in profile.health_goals[:10]]

    # TODO: Save to MongoDB
    return {"status": "updated", "profile": profile}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
