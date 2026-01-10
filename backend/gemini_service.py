"""
Gemini API integration for receipt OCR and extraction
"""

from langchain_google_genai import ChatGoogleGenerativeAI
import os
from dotenv import load_dotenv
from PIL import Image
import io
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import base64
from langchain_core.messages import HumanMessage

load_dotenv()

# Configure Gemini
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY environment variable not set")

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.3,
    api_key=api_key
)


async def extract_receipt_data(image_bytes: bytes) -> Dict:
    """
    Extract structured data from receipt image using Gemini Vision API

    Args:
        image_bytes: Receipt image as bytes

    Returns:
        Dictionary with extracted receipt data
    """
    try:
        # Load image
        image = Image.open(io.BytesIO(image_bytes))

        # Craft detailed prompt for receipt extraction
        prompt = """
        Analyze this receipt image and extract the following information in JSON format:

        {
            "merchant": "store name",
            "date": "YYYY-MM-DD",
            "items": [
                {
                    "name": "item name",
                    "price": 0.00,
                    "category": "groceries|restaurant|retail|pharmacy|other"
                }
            ],
            "total": 0.00,
            "subtotal": 0.00,
            "tax": 0.00,
            "payment_method": "cash|credit|debit|unknown"
        }

        Guidelines:
        - Extract ALL items with their prices
        - Categorize items based on the store type and item name
        - Use proper date format YYYY-MM-DD
        - If information is unclear, use null or "unknown"
        - For the merchant, provide the official store name
        - Prices should be numbers without currency symbols

        Return ONLY the JSON object, no other text.
        """

        # Generate content with image
        image_base64 = base64.b64encode(image_bytes).decode()
        message = HumanMessage(content=[
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": f"data:image/jpeg;base64,{image_base64}"}
        ])
        response = await llm.ainvoke([message])

        # Parse JSON from response
        response_text = str(response.content).strip() if response.content else ""

        # Remove markdown code blocks if present
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]

        receipt_data = json.loads(response_text.strip())

        # Add return policy information
        receipt_data["return_policy_days"] = get_return_policy_days(receipt_data.get("merchant", ""))

        # Calculate return deadline
        if receipt_data.get("date") and receipt_data.get("return_policy_days"):
            try:
                purchase_date = datetime.strptime(receipt_data["date"], "%Y-%m-%d")
                deadline = purchase_date + timedelta(days=receipt_data["return_policy_days"])
                receipt_data["return_deadline"] = deadline.strftime("%Y-%m-%d")
            except:
                receipt_data["return_deadline"] = None

        return receipt_data

    except Exception as e:
        print(f"Error extracting receipt data: {e}")
        raise Exception(f"Failed to extract receipt data: {str(e)}")


def get_return_policy_days(merchant: str) -> Optional[int]:
    """
    Get return policy days for common merchants
    This is a simplified version - could be expanded with a real database
    """
    merchant_lower = merchant.lower()

    # Common return policies
    policies = {
        "walmart": 90,
        "target": 90,
        "costco": 90,
        "amazon": 30,
        "best buy": 15,
        "home depot": 90,
        "lowes": 90,
        "tj maxx": 30,
        "marshalls": 30,
        "gap": 45,
        "old navy": 45,
        "nordstrom": 90,
        "macy's": 30,
        "whole foods": 90,
        "trader joe's": 30,
        "cvs": 60,
        "walgreens": 30,
        "rite aid": 30,
    }

    for store, days in policies.items():
        if store in merchant_lower:
            return days

    # Default return policy
    return 30


async def analyze_receipt_health(items: List[Dict]) -> Dict:
    """
    Analyze receipt items for health insights using Gemini

    Args:
        items: List of receipt items

    Returns:
        Health insights dictionary
    """
    try:
        # Create item list for analysis
        item_names = [item.get("name", "") for item in items]

        prompt = f"""
        Analyze these grocery/food items for health and allergen information:

        Items: {', '.join(item_names)}

        Provide a JSON response with:
        {{
            "allergen_alerts": ["list of potential allergens found: dairy, nuts, gluten, soy, eggs, shellfish, etc."],
            "health_score": 0-100 (higher is healthier),
            "health_warnings": ["specific warnings like 'High sugar', 'High sodium', 'Processed foods', etc."],
            "suggestions": ["specific actionable suggestions for healthier alternatives"],
            "diet_flags": {{
                "vegetarian_friendly": true/false,
                "vegan_friendly": true/false,
                "gluten_free": true/false,
                "high_protein": true/false,
                "low_sugar": true/false
            }},
            "nutritional_summary": "brief 1-2 sentence summary"
        }}

        Be specific and practical. Return ONLY the JSON object.
        """

        response = await llm.ainvoke(prompt)
        response_text = str(response.content).strip() if response.content else ""

        # Clean markdown formatting
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]

        health_data = json.loads(response_text.strip())
        return health_data

    except Exception as e:
        print(f"Error analyzing health data: {e}")
        # Return default safe response
        return {
            "allergen_alerts": [],
            "health_score": 50,
            "health_warnings": ["Unable to analyze"],
            "suggestions": ["Review items manually"],
            "diet_flags": {
                "vegetarian_friendly": False,
                "vegan_friendly": False,
                "gluten_free": False,
                "high_protein": False,
                "low_sugar": False
            },
            "nutritional_summary": "Analysis unavailable"
        }


async def generate_receipt_summary_text(receipt_data: Dict) -> str:
    """
    Generate a natural language summary of the receipt for text-to-speech
    Optimized for accessibility

    Args:
        receipt_data: Receipt data dictionary

    Returns:
        Natural language summary string
    """
    merchant = receipt_data.get("merchant", "Unknown store")
    date = receipt_data.get("date", "Unknown date")
    total = receipt_data.get("total", 0)
    items = receipt_data.get("items", [])
    item_count = len(items)

    # Create simple, clear summary
    summary = f"Receipt from {merchant} on {date}. "
    summary += f"Total: ${total:.2f}. "
    summary += f"You purchased {item_count} item{'s' if item_count != 1 else ''}. "

    # List items
    if item_count > 0:
        summary += "Items: "
        for i, item in enumerate(items[:5]):  # Limit to first 5 items
            item_name = item.get("name", "Unknown item")
            item_price = item.get("price", 0)
            summary += f"{item_name} for ${item_price:.2f}"
            if i < len(items[:5]) - 1:
                summary += ", "

        if item_count > 5:
            summary += f", and {item_count - 5} more items"

    summary += "."

    # Add return policy info
    if receipt_data.get("return_policy_days"):
        summary += f" This item can be returned within {receipt_data['return_policy_days']} days."

    return summary
