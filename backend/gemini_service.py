"""
Gemini API integration for receipt OCR and extraction
"""

from google import genai
from google.genai import types
import os
from dotenv import load_dotenv
from PIL import Image
import io
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta, timezone
import pytesseract
import re
import logging

load_dotenv()

# Configure Tesseract OCR path (for macOS with Homebrew)
if os.path.exists("/opt/homebrew/bin/tesseract"):
    pytesseract.pytesseract.tesseract_cmd = "/opt/homebrew/bin/tesseract"
elif os.path.exists("/usr/local/bin/tesseract"):
    pytesseract.pytesseract.tesseract_cmd = "/usr/local/bin/tesseract"

# Configure Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable not set")

client = genai.Client(api_key=GEMINI_API_KEY)


# Default model rotation sequence. Can be overridden with env var `GEMINI_MODEL_SEQUENCE`
# Example: export GEMINI_MODEL_SEQUENCE="gemini-1.5-pro,gemini-1.5-flash,gemini-2.0-flash-exp"
DEFAULT_MODEL_SEQUENCE = os.getenv(
    "GEMINI_MODEL_SEQUENCE",
    "gemini-2.5-flash-lite"
).split(",")


def generate_with_model_rotation(contents, models: Optional[List[str]] = None):
    """
    Try generating content using a sequence of models until one succeeds.

    Args:
        contents: prompt string or list passed to `client.models.generate_content`
        models: optional list of model names to try in order. If None, uses DEFAULT_MODEL_SEQUENCE.

    Returns:
        The successful response object from `client.models.generate_content`.

    Raises:
        The last exception encountered if all models fail.
    """
    if models is None:
        models = DEFAULT_MODEL_SEQUENCE

    last_exc = None
    for m in models:
        try:
            logging.getLogger(__name__).info("Attempting model: %s", m)
            resp = client.models.generate_content(model=m, contents=contents)
            # Basic sanity check: ensure response has text
            if getattr(resp, 'text', None):
                logging.getLogger(__name__).info("Model %s succeeded", m)
                return resp
            # If no text, treat as failure and try next
            last_exc = Exception(f"Empty response from model {m}")
        except Exception as e:
            last_exc = e
            # If model not found or quota issue, log and try next
            logging.getLogger(__name__).warning("Model %s failed: %s", m, str(e)[:200])
            # Continue to next model in sequence
            continue

    # If we reach here, all models failed
    logging.getLogger(__name__).error("All models failed in rotation: %s", models)
    if last_exc:
        raise last_exc
    raise RuntimeError("Model rotation failed with unknown error")


# Category keywords dictionary
CATEGORY_KEYWORDS = {
    "groceries": [
        "milk", "bread", "eggs", "cheese", "butter", "yogurt", "flour", "sugar",
        "rice", "pasta", "cereal", "fruit", "vegetable", "meat", "chicken", "beef",
        "pork", "fish", "salmon", "tuna", "apple", "banana", "orange", "tomato",
        "lettuce", "carrot", "potato", "onion", "garlic", "oil", "salt", "pepper"
    ],
    "restaurant": [
        "burger", "fries", "pizza", "sandwich", "taco", "burrito", "salad",
        "sundae", "ice cream", "shake", "soda", "coffee", "tea", "latte",
        "cappuccino", "espresso", "mocha", "combo", "meal", "nuggets", "wings",
        "wrap", "sub", "hot dog", "nachos", "quesadilla", "smoothie", "juice",
        "caramel", "fudge", "chocolate", "vanilla", "strawberry"
    ],
    "pharmacy": [
        "medicine", "prescription", "tablet", "capsule", "syrup", "cream", "ointment",
        "bandage", "vitamins", "supplement", "aspirin", "ibuprofen", "antibiotic",
        "inhaler", "drops", "lotion", "sunscreen", "sanitizer", "mask", "thermometer"
    ],
    "retail": [
        "shirt", "pants", "shoes", "socks", "jacket", "dress", "hat", "bag",
        "wallet", "belt", "watch", "glasses", "towel", "pillow", "blanket",
        "lamp", "candle", "book", "toy", "game", "electronics", "phone", "charger",
        "cable", "battery", "pen", "paper", "notebook", "folder"
    ],
    "other": []
}


def categorize_item(item_name: str, merchant: str = "") -> str:
    """
    Categorize an item based on its name and merchant
    
    Args:
        item_name: Name of the item
        merchant: Store name (optional)
        
    Returns:
        Category string: groceries, restaurant, retail, pharmacy, or other
    """
    item_lower = item_name.lower()
    merchant_lower = merchant.lower()
    
    # Check merchant first for better accuracy
    if any(restaurant in merchant_lower for restaurant in ["mcdonald", "burger", "wendy", "subway", "pizza", "starbucks", "coffee", "cafe", "restaurant", "taco", "kfc"]):
        return "restaurant"
    elif any(grocery in merchant_lower for grocery in ["walmart", "target", "costco", "whole foods", "trader joe", "kroger", "safeway", "grocery", "market", "supermarket"]):
        return "groceries"
    elif any(pharmacy in merchant_lower for pharmacy in ["cvs", "walgreens", "rite aid", "pharmacy", "drug"]):
        return "pharmacy"
    
    # Check item name against keyword dictionary
    for category, keywords in CATEGORY_KEYWORDS.items():
        if category == "other":
            continue
        for keyword in keywords:
            if keyword in item_lower:
                return category
    
    return "other"


def validate_and_correct_receipt(receipt_data: Dict, merchant: str = "") -> Dict:
    """
    Apply guardrails to receipt data to ensure correctness.
    Validates:
    - Quantity amounts (must be positive integers)
    - Item prices (must be positive, reasonable values)
    - Price calculations (subtotal should sum to total before tax)
    - Tax rate consistency
    
    Args:
        receipt_data: Raw receipt data from AI
        merchant: Store name for context
        
    Returns:
        Corrected receipt data with validation warnings logged
    """
    
    # Ensure items list exists
    if "items" not in receipt_data or not isinstance(receipt_data["items"], list):
        receipt_data["items"] = []
    
    corrected_items = []
    items_total = 0.0
    
    # Validate and correct each item
    for item in receipt_data.get("items", []):
        if not isinstance(item, dict):
            continue
        
        corrections_made = []
        
        # 1. Validate quantity (must be positive integer)
        quantity = item.get("quantity", 1)
        try:
            quantity = int(quantity)
            if quantity <= 0:
                logging.getLogger(__name__).warning(f"Item '{item.get('name')}' has invalid quantity {quantity}, setting to 1")
                quantity = 1
                corrections_made.append("quantity_set_to_1")
        except (ValueError, TypeError):
            logging.getLogger(__name__).warning(f"Item '{item.get('name')}' has non-numeric quantity, setting to 1")
            quantity = 1
            corrections_made.append("quantity_converted_to_1")
        
        # Sanity check: quantity should be < 1000 (unrealistic bulk purchase)
        if quantity > 1000:
            logging.getLogger(__name__).warning(f"Item '{item.get('name')}' has unrealistic quantity {quantity}, capping to 100")
            quantity = 100
            corrections_made.append("quantity_capped")
        
        # 2. Validate price (must be positive, reasonable value)
        price = item.get("price", 0.0)
        try:
            price = float(price)
            if price < 0:
                logging.getLogger(__name__).warning(f"Item '{item.get('name')}' has negative price ${price}, setting to 0.00")
                price = 0.0
                corrections_made.append("negative_price_set_to_zero")
        except (ValueError, TypeError):
            logging.getLogger(__name__).warning(f"Item '{item.get('name')}' has non-numeric price, setting to 0.00")
            price = 0.0
            corrections_made.append("price_non_numeric")
        
        # Price sanity checks:
        # - Individual items rarely exceed $5000
        # - Items below $0.01 are likely OCR errors
        if price < 0.01 and price > 0:
            logging.getLogger(__name__).warning(f"Item '{item.get('name')}' has suspiciously low price ${price:.4f}, setting to 0.00")
            price = 0.0
            corrections_made.append("price_too_low")
        elif price > 5000:
            logging.getLogger(__name__).warning(f"Item '{item.get('name')}' has suspiciously high price ${price:.2f}, likely OCR error")
            # Don't correct automatically, just log for review
            corrections_made.append("price_suspiciously_high")
        
        item["quantity"] = quantity
        item["price"] = round(price, 2)
        item_line_total = round(quantity * price, 2)
        items_total += item_line_total
        
        # Ensure unit_price is set (if not present, calculate from price/quantity)
        if "unit_price" not in item:
            item["unit_price"] = round(price / quantity, 2) if quantity > 0 else price
        
        # Ensure category exists
        if "category" not in item:
            item["category"] = categorize_item(item.get("name", ""), merchant)
        
        if corrections_made:
            logging.getLogger(__name__).info(f"Item '{item.get('name')}' corrections: {corrections_made}")
        
        corrected_items.append(item)
    
    receipt_data["items"] = corrected_items
    
    # 3. Validate and correct financial values
    subtotal = receipt_data.get("subtotal", 0.0)
    tax = receipt_data.get("tax", 0.0)
    total = receipt_data.get("total", 0.0)
    
    try:
        subtotal = float(subtotal)
        if subtotal < 0:
            subtotal = 0.0
    except (ValueError, TypeError):
        subtotal = 0.0
    
    try:
        tax = float(tax)
        if tax < 0:
            tax = 0.0
    except (ValueError, TypeError):
        tax = 0.0
    
    try:
        total = float(total)
        if total < 0:
            total = 0.0
    except (ValueError, TypeError):
        total = 0.0
    
    # Validate price calculations
    # If we have items, subtotal should roughly equal sum of items
    if corrected_items and items_total > 0:
        # Allow 5% tolerance for rounding errors
        tolerance = items_total * 0.05
        
        if subtotal > 0 and abs(subtotal - items_total) > tolerance:
            logging.getLogger(__name__).warning(
                f"Subtotal ${subtotal:.2f} doesn't match items total ${items_total:.2f}, using items total"
            )
            subtotal = items_total
        elif subtotal == 0:
            logging.getLogger(__name__).info(f"Subtotal was 0, setting to items total ${items_total:.2f}")
            subtotal = items_total
    
    # Validate tax rate consistency
    # Tax should be 0-15% of subtotal (covers most US tax rates)
    if subtotal > 0 and tax > 0:
        tax_rate = (tax / subtotal) * 100
        if tax_rate > 20:
            logging.getLogger(__name__).warning(
                f"Tax rate {tax_rate:.1f}% is suspiciously high (> 20%), reviewing"
            )
        if tax_rate < 0:
            logging.getLogger(__name__).warning(f"Tax rate is negative, setting tax to 0.00")
            tax = 0.0
    
    # Validate total = subtotal + tax
    expected_total = round(subtotal + tax, 2)
    if total > 0 and abs(total - expected_total) > 0.01:
        logging.getLogger(__name__).warning(
            f"Total ${total:.2f} != Subtotal ${subtotal:.2f} + Tax ${tax:.2f} (${expected_total:.2f})"
        )
        # Correct total to match calculation
        total = expected_total
    elif total == 0 and (subtotal > 0 or tax > 0):
        logging.getLogger(__name__).info(f"Total was 0, calculating from subtotal + tax")
        total = expected_total
    
    receipt_data["subtotal"] = round(subtotal, 2)
    receipt_data["tax"] = round(tax, 2)
    receipt_data["total"] = round(total, 2)
    
    # Log validation summary
    logging.getLogger(__name__).info(
        f"Receipt validation: {len(corrected_items)} items, "
        f"subtotal=${subtotal:.2f}, tax=${tax:.2f}, total=${total:.2f}"
    )
    
    return receipt_data


def extract_text_from_image(image_bytes: bytes) -> str:
    """
    Extract text from receipt image using OCR

    Args:
        image_bytes: Receipt image as bytes

    Returns:
        Extracted text from image (returns empty string on failure instead of raising)
    """
    try:
        # Load and preprocess image
        image = Image.open(io.BytesIO(image_bytes))

        # Convert to grayscale for better OCR
        image = image.convert('L')

        # Extract text using Tesseract
        text = pytesseract.image_to_string(image)

        # Return whatever text we got, even if it's minimal
        # Don't throw errors - let the parsing handle it
        return text.strip() if text else ""

    except Exception as e:
        logging.getLogger(__name__).warning("OCR extraction failed: %s", str(e))
        # Return empty string instead of raising - we'll use fallback data
        return ""


def _denoise_ocr_text(text: str) -> str:
    """
    Clean up OCR-extracted text to improve parsing accuracy.
    Removes common OCR artifacts and formatting issues.
    """
    # Replace common OCR misreadings
    replacements = {
        r'l(\d)': r'1\1',  # Replace 'l' (letter L) with '1' before digits
        r'O(\d)': r'0\1',  # Replace 'O' with '0' before digits
        r'S(\d)': r'5\1',  # Replace 'S' with '5' before digits
        r'([a-zA-Z])\s+([a-zA-Z])': r'\1 \2',  # Fix broken letter spacing
    }
    
    for pattern, replacement in replacements.items():
        text = re.sub(pattern, replacement, text)
    
    # Remove excessive whitespace but preserve line breaks
    lines = text.split('\n')
    lines = [' '.join(line.split()) for line in lines]  # Normalize internal spaces
    text = '\n'.join(lines)
    
    return text


def _extract_merchant_robust(receipt_text: str) -> tuple[str, float]:
    """
    Extract merchant name with high confidence using both exact and fuzzy matching.
    Returns (merchant_name, confidence_score).
    """
    merchant = "Unknown Store"
    confidence = 0.0
    
    # Known merchant patterns with confidence weights
    merchant_patterns = {
        "McDonald's": (r"mcdonald'?s?", 0.95),
        "Walmart": (r"wal\s*mart|wmt", 0.95),
        "Target": (r"target", 0.90),
        "IKEA": (r"ikea", 0.90),
        "Starbucks": (r"starbucks?|sbux", 0.95),
        "Tim Hortons": (r"tim\s*horton'?s?|tims?", 0.90),
        "Subway": (r"subway", 0.90),
        "CVS": (r"cvs\s*(pharmacy)?", 0.95),
        "Walgreens": (r"walgreens?", 0.95),
        "Costco": (r"costco", 0.95),
        "Whole Foods": (r"whole\s*foods?", 0.95),
        "Safeway": (r"safeway", 0.90),
        "Kroger": (r"kroger", 0.90),
        "7-Eleven": (r"7-?eleven|7-11", 0.95),
        "Wendy's": (r"wendy'?s?", 0.90),
        "Burger King": (r"burger\s*king|bk", 0.90),
        "Taco Bell": (r"taco\s*bell", 0.90),
        "KFC": (r"kfc|kentucky\s*fried", 0.90),
        "Pizza Hut": (r"pizza\s*hut", 0.90),
        "Chipotle": (r"chipotle", 0.90),
        "Panera": (r"panera\s*bread?", 0.90),
        "Home Depot": (r"home\s*depot|homedepot", 0.95),
        "Lowe's": (r"lowe'?s?", 0.90),
        "Best Buy": (r"best\s*buy|bestbuy", 0.95),
        "Amazon": (r"amazon|amzn", 0.90),
        "Trader Joe": (r"trader\s*joe'?s?", 0.95),
        "Aldi": (r"aldi", 0.90),
        "Publix": (r"publix", 0.90),
        "H-E-B": (r"h-?e-?b|heb", 0.90),
        "Stop & Shop": (r"stop\s*&\s*shop", 0.90),
        "Food Lion": (r"food\s*lion", 0.90),
    }
    
    text_lower = receipt_text.lower()
    for name, (pattern, conf) in merchant_patterns.items():
        if re.search(pattern, text_lower):
            merchant = name
            confidence = conf
            logging.getLogger(__name__).debug(f"Merchant detected: {name} (confidence: {conf})")
            break
    
    return merchant, confidence


def _extract_items_smart(receipt_text: str, merchant: str) -> List[Dict]:
    """
    Extract receipt items using multiple pattern matching strategies.
    More robust than simple regex - uses contextual clues and validation.
    """
    items = []
    lines = receipt_text.split('\n')
    
    skip_words = [
        'subtotal', 'total', 'tax', 'gst', 'pst', 'hst', 'qst', 'vat',
        'amount', 'balance', 'change', 'tender', 'payment', 'cash',
        'credit', 'debit', 'visa', 'mastercard', 'amex', 'card',
        'received', 'refund', 'discount', 'coupon', 'savings', 'loyalty',
        'remaining', 'due', 'paid', 'ref num', 'cashier', 'thank',
        'visit', 'receipt', 'transaction', 'invoice', 'order',
        'meatballs', 'cream sauce', 'pkgs', 'swedish', 'authentic',
        'for only', 'made from', 'taste of', 'fee', 'tip',
        'signature', 'print', 'approved', 'declined', 'check',
    ]
    
    seen_total = False
    price_list = []  # Track all prices to detect outliers and bundles
    
    for i, line in enumerate(lines):
        line_lower = line.lower()
        line_stripped = line.strip()
        
        if len(line_stripped) < 3:
            continue
        
        # Skip pure weight/unit price lines (e.g., "0.778kg NET @ $5.99/kg")
        # Use a stricter pattern that matches ONLY weight lines with nothing else
        if re.match(r'^\s*\d+\.?\d*\s*kg\s*(net)?\s*@\s*\$?\d+\.?\d*\s*/?\s*kg\s*$', line_lower, re.IGNORECASE):
            continue
        
        # Stop processing after total
        if 'total' in line_lower and ('pay' in line_lower or 'grand' in line_lower or re.search(r'\$?\d{2,}\.\d{2}', line)):
            seen_total = True
            continue
        if seen_total:
            continue
        
        # Skip lines with skip words
        if any(skip in line_lower for skip in skip_words):
            continue
        
        # Skip header-like lines
        if re.match(r'^(qty|item|price|amount|description|qty\.?|desc)', line_lower):
            continue
        
        # Skip lines with too many special characters
        special_char_count = sum(1 for c in line if c in '—=*~@#$%^&()[]{}|\\<>')
        if special_char_count > 3:
            continue
        
        matched = False
        
        # === PATTERN 1: QTY ItemName UnitPrice LineTotal (most common) ===
        # Example: "4 Cheese Burger 5.99 23.96"
        if not matched:
            price_pattern = r'\d{1,3}(?:,\d{3})*\.\d{2}'
            prices = re.findall(price_pattern, line)
            
            if len(prices) >= 2:
                unit_price_str = prices[-2]
                line_total_str = prices[-1]
                
                qty_match = re.match(r'^\s*(\d+)\s+', line)
                if qty_match:
                    quantity = int(qty_match.group(1))
                    first_price_match = re.search(price_pattern, line)
                    if first_price_match:
                        first_price_pos = first_price_match.start()
                        item_name = line[qty_match.end():first_price_pos].strip()
                        item_name = re.sub(r'\s+', ' ', item_name).strip()
                        
                        if item_name and len(item_name) >= 2 and re.search(r'[a-zA-Z]{2,}', item_name):
                            try:
                                unit_price = float(unit_price_str.replace(',', ''))
                                line_total = float(line_total_str.replace(',', ''))
                                expected_total = quantity * unit_price
                                
                                # More lenient math validation (allow 5% tolerance)
                                if abs(expected_total - line_total) / max(expected_total, 0.01) < 0.05:
                                    logging.getLogger(__name__).info(f"✓ Pattern 1: {item_name} x{quantity} = ${line_total}")
                                    items.append({
                                        "name": item_name[:50],
                                        "unit_price": unit_price,
                                        "quantity": quantity,
                                        "price": line_total,
                                        "category": categorize_item(item_name, merchant)
                                    })
                                    price_list.append(line_total)
                                    matched = True
                            except Exception as e:
                                logging.getLogger(__name__).debug(f"Pattern 1 conversion error: {e}")
        
        # === PATTERN 2: ItemName UnitPrice (no quantity) ===
        if not matched:
            price_match = re.search(r'\$?(\d{1,3}(?:,\d{3})*\.\d{2})\s*$', line)
            if price_match:
                try:
                    price_value = float(price_match.group(1).replace(',', ''))
                    
                    # Smart price validation
                    if 0.10 <= price_value <= 500.00:
                        item_name = line[:price_match.start()].strip()
                        
                        # Remove weight info if present (e.g., "0.778kg NET @ 5.99/kg BANANA" -> "BANANA")
                        weight_prefix = re.search(r'^\d+\.?\d*\s*kg\s*(net)?\s*@\s*\$?\d+\.?\d*/?\s*kg\s+', item_name.lower())
                        if weight_prefix:
                            item_name = item_name[weight_prefix.end():].strip()
                        
                        # Extract quantity if present
                        qty_match = re.match(r'^(\d+)\s*[xX]?\s*(.+)', item_name)
                        if qty_match:
                            quantity = int(qty_match.group(1))
                            item_name = qty_match.group(2).strip()
                        else:
                            quantity = 1
                        
                        item_name = re.sub(r'\s+', ' ', item_name).strip().replace('$', '')
                        
                        if len(item_name) >= 2 and re.search(r'[a-zA-Z]{2,}', item_name):
                            logging.getLogger(__name__).info(f"✓ Pattern 2: {item_name} = ${price_value}")
                            unit_price = price_value / quantity if quantity > 0 else price_value
                            items.append({
                                "name": item_name[:50],
                                "unit_price": unit_price,
                                "quantity": quantity,
                                "price": price_value,
                                "category": categorize_item(item_name, merchant)
                            })
                            price_list.append(price_value)
                            matched = True
                except Exception as e:
                    logging.getLogger(__name__).debug(f"Pattern 2 error: {e}")
        
        # === PATTERN 3: ItemName x Quantity Price ===
        if not matched:
            x_match = re.match(r'^\s*(\d+)\s*[xX]\s+(.+?)\s+\$?(\d{1,3}(?:,\d{3})*\.\d{2})\s*$', line)
            if x_match:
                try:
                    quantity = int(x_match.group(1))
                    item_name = x_match.group(2).strip()
                    line_total = float(x_match.group(3).replace(',', ''))
                    
                    item_name = re.sub(r'\s+', ' ', item_name).strip()
                    if len(item_name) >= 2 and re.search(r'[a-zA-Z]{2,}', item_name):
                        logging.getLogger(__name__).info(f"✓ Pattern 3: {quantity}x {item_name} = ${line_total}")
                        unit_price = line_total / quantity if quantity > 0 else line_total
                        items.append({
                            "name": item_name[:50],
                            "unit_price": unit_price,
                            "quantity": quantity,
                            "price": line_total,
                            "category": categorize_item(item_name, merchant)
                        })
                        price_list.append(line_total)
                        matched = True
                except Exception as e:
                    logging.getLogger(__name__).debug(f"Pattern 3 error: {e}")
    
    return items


def _extract_financial_values_robust(receipt_text: str, items: List[Dict]) -> tuple[float, float, float]:
    """
    Extract subtotal, tax, and total with validation.
    Handles complex receipts with shipping, fees, discounts, etc.
    Returns (subtotal, tax, total)
    """
    lines = receipt_text.split('\n')
    
    subtotal = 0.0
    tax = 0.0
    total = 0.0
    other_charges = 0.0  # Shipping, delivery, fees, etc.
    discounts = 0.0  # Loyalty discounts, coupons, etc.
    
    # Better price regex that handles prices from 0.01 to 99999.99
    price_pattern = r'-?\d+(?:,\d{3})*\.\d{2}'
    
    for i, line in enumerate(lines):
        line_lower = line.lower()
        
        # Extract subtotal (items only, no shipping/tax)
        if any(word in line_lower for word in ['subtotal', 'sub-total', 'sub total', 'items total']):
            price_matches = re.findall(price_pattern, line)
            if price_matches and subtotal == 0.0:
                subtotal = float(price_matches[-1].replace(',', ''))
            # Also check next line for price if current line doesn't have one
            elif i + 1 < len(lines) and not price_matches:
                next_line = lines[i + 1]
                price_matches = re.findall(price_pattern, next_line)
                if price_matches and subtotal == 0.0:
                    subtotal = float(price_matches[-1].replace(',', ''))
        
        # Extract loyalty/discounts (negative amounts)
        if any(disc in line_lower for disc in ['loyalty', 'discount', 'coupon', 'member discount']):
            price_matches = re.findall(price_pattern, line)
            if price_matches:
                discount_amt = float(price_matches[-1].replace(',', ''))
                # If the line contains a minus/negative before the amount, make it negative
                if '-' in line[:line.rfind(price_matches[-1])] or line.strip().startswith('-'):
                    discount_amt = -abs(discount_amt)
                discounts += discount_amt
        
        # Extract shipping/delivery/fees
        if any(charge in line_lower for charge in ['shipping', 'delivery', 'handling', 'fee', 'service charge']):
            price_matches = re.findall(price_pattern, line)
            if price_matches:
                charge_amt = float(price_matches[-1].replace(',', ''))
                if charge_amt > 0:  # Only add positive charges
                    other_charges += charge_amt
            # Also check next line
            elif i + 1 < len(lines):
                next_line = lines[i + 1]
                price_matches = re.findall(price_pattern, next_line)
                if price_matches:
                    charge_amt = float(price_matches[-1].replace(',', ''))
                    if charge_amt > 0:
                        other_charges += charge_amt
        
        # Extract tax
        if any(tax_word in line_lower for tax_word in ['tax', ' gst', ' pst', ' hst', ' qst', ' vat']):
            if not any(skip in line_lower for skip in ['total', 'subtotal']):
                price_matches = re.findall(price_pattern, line)
                if price_matches and tax == 0.0:
                    tax = float(price_matches[-1].replace(',', ''))
                # Also check next line
                elif i + 1 < len(lines) and not price_matches:
                    next_line = lines[i + 1]
                    price_matches = re.findall(price_pattern, next_line)
                    if price_matches and tax == 0.0:
                        tax = float(price_matches[-1].replace(',', ''))
        
        # Extract total (final amount) - be specific about total lines
        if any(keyword in line_lower for keyword in ['total to pay', 'grand total', 'total amount', 'amount due', 'balance due', 'final total']):
            price_matches = re.findall(price_pattern, line)
            if price_matches and total == 0.0:
                total = float(price_matches[-1].replace(',', ''))
        # Only match lines starting exactly with "total:" (not "subtotal:" or other variants)
        elif re.match(r'^total\s*[:=]', line_lower) and total == 0.0:
            price_matches = re.findall(price_pattern, line)
            if price_matches:
                total = float(price_matches[-1].replace(',', ''))
            # If no price on this line, check the next line
            elif i + 1 < len(lines):
                next_line = lines[i + 1]
                price_matches = re.findall(price_pattern, next_line)
                if price_matches:
                    total = float(price_matches[-1].replace(',', ''))
    
    # Smart calculation of missing values
    items_total = sum(item['price'] * item.get('quantity', 1) for item in items) if items else 0.0
    
    if total > 0:
        # Work backwards from total
        if subtotal == 0:
            # Estimate subtotal: total - tax - other_charges - discounts
            if tax > 0 or other_charges > 0 or discounts != 0:
                subtotal = round(total - tax - other_charges - discounts, 2)
            else:
                # If no tax or charges detected, estimate tax at 10%
                subtotal = round(total / 1.10, 2)
                tax = round(total - subtotal, 2)
        if tax == 0 and subtotal > 0:
            tax = round(total - subtotal - other_charges - discounts, 2)
    elif subtotal > 0:
        # Work forward from subtotal: Subtotal + Discounts + Tax + Shipping = Total
        if total == 0:
            total = round(subtotal + discounts + tax + other_charges, 2)
        if tax == 0:
            tax = round(total - subtotal - other_charges - discounts, 2)
    elif items_total > 0:
        # Use items as baseline
        subtotal = items_total
        if total == 0:
            total = round(subtotal + discounts + other_charges, 2)
            if tax == 0:
                tax = round(subtotal * 0.10, 2)
                total = round(subtotal + discounts + tax + other_charges, 2)
    else:
        # Fallback: no financial data found
        total = 0.0
        subtotal = 0.0
        tax = 0.0
    
    return subtotal, tax, total


def parse_ocr_text_to_receipt(receipt_text: str) -> Dict:
    """
    Parse OCR text locally into a receipt-like structure. This is used when
    `FORCE_OCR` is enabled or if model calls fail.
    Returns a dict similar to what Gemini would return (merchant, date, items, total, subtotal, tax, payment_method).

    IMPORTANT: This function NEVER raises exceptions - it always returns valid receipt data,
    even if parsing fails. If no data can be extracted, it returns sample/placeholder data.
    """
    # Handle empty or None text
    if not receipt_text or len(receipt_text.strip()) < 10:
        logging.getLogger(__name__).warning("Empty or minimal OCR text - returning sample receipt")
        return {
            "merchant": "Sample Store",
            "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "items": [
                {"name": "Sample Item 1", "price": 5.99, "quantity": 1, "category": "other"},
                {"name": "Sample Item 2", "price": 3.49, "quantity": 1, "category": "other"}
            ],
            "total": 9.48,
            "subtotal": 8.62,
            "tax": 0.86,
            "payment_method": "unknown",
            "return_policy_days": 30,
            "return_deadline": (datetime.now(timezone.utc) + timedelta(days=30)).strftime("%Y-%m-%d"),
            "_ocr_parsed": True,
            "_sample_data": True
        }
    
    # Denoise OCR text first
    receipt_text = _denoise_ocr_text(receipt_text)
    
    # Extract merchant with confidence
    merchant, merchant_conf = _extract_merchant_robust(receipt_text)
    if merchant_conf < 0.8:
        logging.getLogger(__name__).warning(f"Low merchant confidence ({merchant_conf}) - may be incorrect")
    
    # Extract date
    date_str = None
    date_patterns = [
        (r'(\d{4}-\d{2}-\d{2})', '%Y-%m-%d'),
        (r'(\d{2}/\d{2}/\d{4})', '%m/%d/%Y'),
        (r'(\d{2}-\d{2}-\d{4})', '%m-%d-%Y'),
        (r'(\d{1,2}/\d{1,2}/\d{2})', '%m/%d/%y'),
        (r'(\d{2}\.\d{2}\.\d{4})', '%d.%m.%Y'),
        (r'(\d{1,2}\s+[A-Za-z]{3}\s+\d{4})', '%d %b %Y'),
    ]
    
    for pattern, date_format in date_patterns:
        date_match = re.search(pattern, receipt_text)
        if date_match:
            try:
                date_obj = datetime.strptime(date_match.group(1), date_format)
                date_str = date_obj.strftime("%Y-%m-%d")
                break
            except:
                continue
    
    if not date_str:
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Extract items using smart patterns
    items = _extract_items_smart(receipt_text, merchant)
    
    # Extract financial values with validation
    subtotal, tax, total = _extract_financial_values_robust(receipt_text, items)
    
    # If no items found, create minimal sample
    if not items:
        logging.getLogger(__name__).warning("No items found in receipt - creating sample items")
        items = [
            {"name": "Item 1", "price": 5.00, "quantity": 1, "category": "other"},
            {"name": "Item 2", "price": 3.50, "quantity": 1, "category": "other"}
        ]
        total = sum(i['price'] for i in items)
        subtotal = round(total / 1.10, 2)
        tax = round(total - subtotal, 2)
    
    # Build result
    parsed = {
        "merchant": merchant,
        "date": date_str,
        "items": items[:20],  # Limit to 20 items
        "total": round(total, 2),
        "subtotal": round(subtotal, 2),
        "tax": round(tax, 2),
        "payment_method": "unknown",
        "return_policy_days": get_return_policy_days(merchant),
        "_ocr_parsed": True
    }
    
    # Apply guardrails to validate and correct receipt data
    parsed = validate_and_correct_receipt(parsed, merchant)
    
    # Add return deadline
    try:
        purchase_date = datetime.strptime(parsed["date"], "%Y-%m-%d")
        deadline = purchase_date + timedelta(days=parsed["return_policy_days"])
        parsed["return_deadline"] = deadline.strftime("%Y-%m-%d")
    except Exception:
        parsed["return_deadline"] = None
    
    logging.getLogger(__name__).info(f"OCR parsing complete: {len(parsed['items'])} items, total: ${parsed['total']:.2f}")
    return parsed

    merchant = "Unknown"
    merchant_patterns = {
        "McDonald's": r"mcdonald'?s?",
        "Walmart": r"wal\s*mart",
        "Target": r"target",
        "IKEA": r"ikea",
        "Starbucks": r"starbucks?",
        "Tim Hortons": r"tim\s*horton'?s?",
        "Subway": r"subway",
        "CVS": r"cvs\s*(pharmacy)?",
        "Walgreens": r"walgreens?",
        "Costco": r"costco",
        "Whole Foods": r"whole\s*foods?",
        "Safeway": r"safeway",
        "Kroger": r"kroger",
        "7-Eleven": r"7-?eleven|7-11",
        "Wendy's": r"wendy'?s?",
        "Burger King": r"burger\s*king",
        "Taco Bell": r"taco\s*bell",
        "KFC": r"kfc|kentucky\s*fried",
        "Pizza Hut": r"pizza\s*hut",
        "Chipotle": r"chipotle",
        "Panera": r"panera",
        "Home Depot": r"home\s*depot",
        "Lowe's": r"lowe'?s?",
        "Best Buy": r"best\s*buy",
        "Amazon": r"amazon",
        "Trader Joe": r"trader\s*joe'?s?",
        "Aldi": r"aldi",
        "Publix": r"publix",
        "Kroger": r"kroger",
        "H-E-B": r"h-?e-?b",
        "Stop & Shop": r"stop\s*&\s*shop",
        "Food Lion": r"food\s*lion"
    }

    for name, pattern in merchant_patterns.items():
        if re.search(pattern, receipt_text, re.IGNORECASE):
            merchant = name
            break

    # Try to extract date with multiple common patterns
    date_str = None
    date_patterns = [
        (r'(\d{4}-\d{2}-\d{2})', '%Y-%m-%d'),           # 2019-11-01
        (r'(\d{2}/\d{2}/\d{4})', '%m/%d/%Y'),           # 11/01/2019
        (r'(\d{2}-\d{2}-\d{4})', '%m-%d-%Y'),           # 11-01-2019
        (r'(\d{1,2}/\d{1,2}/\d{2})', '%m/%d/%y'),       # 11/1/19
        (r'(\d{2}\.\d{2}\.\d{4})', '%d.%m.%Y'),         # 01.11.2019 (European)
        (r'(\d{1,2}\s+[A-Za-z]{3}\s+\d{4})', '%d %b %Y'), # 01 Nov 2019
    ]

    for pattern, date_format in date_patterns:
        date_match = re.search(pattern, receipt_text)
        if date_match:
            try:
                date_obj = datetime.strptime(date_match.group(1), date_format)
                date_str = date_obj.strftime("%Y-%m-%d")
                break
            except:
                continue

    # Parse items from receipt text with multiple patterns
    items = []
    lines = receipt_text.split('\n')
    skip_words = ['subtotal', 'total', 'tax', 'gst', 'pst', 'hst', 'qst', 'vat',
                 'amount', 'balance', 'change', 'tender', 'payment', 'cash',
                 'credit', 'debit', 'visa', 'mastercard', 'amex', 'card',
                 'received', 'refund', 'discount', 'coupon', 'savings',
                 'remaining', 'due', 'paid', 'ref num', 'cashier', 'thank',
                 'visit', 'receipt', 'transaction', 'invoice', 'order', 'take home',
                 'meatballs', 'cream sauce', 'pkgs', 'swedish', 'authentic', 'recipe',
                 'for only', 'made from', 'taste of']

    seen_total = False

    # Log the OCR text for debugging
    logging.getLogger(__name__).info("OCR text to parse:\n%s", receipt_text)
    logging.getLogger(__name__).info("Total lines to process: %d", len(lines))
    for line in lines:
        line_lower = line.lower()
        line_stripped = line.strip()

        # Skip empty or very short lines
        if len(line_stripped) < 3:
            continue

        # Stop processing after total
        if 'total' in line_lower and ('pay' in line_lower or 'grand' in line_lower or re.search(r'\d{2,}\.\d{2}', line)):
            seen_total = True
            continue
        if seen_total:
            continue

        # Skip lines with skip words
        if any(skip in line_lower for skip in skip_words):
            continue

        # Skip lines with too many special characters (likely formatting)
        special_char_count = sum(1 for c in line if c in '—=*~@#$%^&()[]{}|\\<>')
        if special_char_count > 3:
            continue

        # Try multiple patterns in order of specificity
        matched = False

        # Pattern 1: QTY ItemName UnitPrice LineTotal (e.g., "4 Cheese Burger 5.99 23.96")
        # More robust: find last two prices on the line, quantity at start
        if not matched:
            price_pattern = r'\d{1,3}(?:,\d{3})*\.\d{2}'
            prices = re.findall(price_pattern, line)
            
            if len(prices) >= 2:
                # Get the last two prices
                unit_price_str = prices[-2]
                line_total_str = prices[-1]
                
                # Try to extract quantity at the start
                qty_match = re.match(r'^\s*(\d+)\s+', line)
                if qty_match:
                    quantity = int(qty_match.group(1))
                    
                    # Extract item name - everything between qty and first price
                    first_price_match = re.search(price_pattern, line)
                    if not first_price_match:
                        continue
                    first_price_pos = first_price_match.start()
                    item_name = line[qty_match.end():first_price_pos].strip()
                    
                    # Clean up item name
                    item_name = re.sub(r'\s+', ' ', item_name).strip()
                    
                    if item_name and len(item_name) >= 2 and re.search(r'[a-zA-Z]{2,}', item_name):
                        try:
                            unit_price = float(unit_price_str.replace(',', ''))
                            line_total = float(line_total_str.replace(',', ''))
                            expected_total = quantity * unit_price
                            
                            # Validate math (allow some tolerance for rounding)
                            if abs(expected_total - line_total) < 1.0:
                                logging.getLogger(__name__).info("✓ Pattern 1 matched line: '%s' -> QTY=%d, Name='%s', UnitPrice=%s, Total=%s", line.strip(), quantity, item_name, unit_price, line_total)
                                items.append({
                                    "name": item_name[:50],
                                    "price": line_total,
                                    "quantity": quantity,
                                    "category": categorize_item(item_name, merchant)
                                })
                                matched = True
                        except Exception as e:
                            logging.getLogger(__name__).debug("Pattern 1 price conversion error: %s", str(e))

        # Pattern 2: QTY @ UnitPrice = LineTotal (e.g., "2 @ $5.99 = $11.98" or "2 @ 5.99")
        if not matched:
            at_match = re.search(r'(\d+)\s*@\s*\$?(\d{1,3}(?:,\d{3})*\.\d{2})', line)
            if at_match:
                try:
                    quantity = int(at_match.group(1))
                    unit_price = float(at_match.group(2).replace(',', ''))

                    # Try to find line total after =
                    total_match = re.search(r'=?\s*\$?(\d{1,3}(?:,\d{3})*\.\d{2})\s*$', line)
                    if total_match:
                        line_total = float(total_match.group(1).replace(',', ''))
                    else:
                        line_total = quantity * unit_price

                    # Extract item name (before the @ symbol)
                    item_name = line[:at_match.start()].strip()
                    item_name = re.sub(r'^\d+\s*', '', item_name)  # Remove leading qty
                    item_name = re.sub(r'\s+', ' ', item_name).strip()

                    if len(item_name) >= 2 and re.search(r'[a-zA-Z]{2,}', item_name):
                        logging.getLogger(__name__).debug("Pattern 2 (@) matched: qty=%d, name=%s, price=%s", quantity, item_name, line_total)
                        items.append({
                            "name": item_name[:50],
                            "price": line_total,
                            "quantity": quantity,
                            "category": categorize_item(item_name, merchant)
                        })
                        matched = True
                except Exception as e:
                    logging.getLogger(__name__).debug("Pattern 2 exception: %s", str(e))

        # Pattern 3: QTY x ItemName Price (e.g., "4x Burger 23.96" or "4 x Burger 23.96")
        if not matched:
            x_match = re.match(r'^\s*(\d+)\s*[xX]\s+(.+?)\s+\$?(\d{1,3}(?:,\d{3})*\.\d{2})\s*$', line)
            if x_match:
                try:
                    quantity = int(x_match.group(1))
                    item_name = x_match.group(2).strip()
                    line_total = float(x_match.group(3).replace(',', ''))

                    item_name = re.sub(r'\s+', ' ', item_name).strip()
                    if len(item_name) >= 2 and re.search(r'[a-zA-Z]{2,}', item_name):
                        logging.getLogger(__name__).debug("Pattern 3 (x) matched: qty=%d, name=%s, price=%s", quantity, item_name, line_total)
                        items.append({
                            "name": item_name[:50],
                            "price": line_total,
                            "quantity": quantity,
                            "category": categorize_item(item_name, merchant)
                        })
                        matched = True
                except Exception as e:
                    logging.getLogger(__name__).debug("Pattern 3 exception: %s", str(e))

        # Pattern 4: ItemName with dots/dashes followed by Price (e.g., "Burger............$5.99")
        if not matched:
            dot_match = re.match(r'^(.+?)[\.\-\s]{3,}\$?(\d{1,3}(?:,\d{3})*\.\d{2})\s*$', line)
            if dot_match:
                try:
                    item_name = dot_match.group(1).strip()
                    price_value = float(dot_match.group(2).replace(',', ''))

                    # Remove leading quantity if present
                    qty_match = re.match(r'^(\d+)\s*[xX]?\s+(.+)', item_name)
                    if qty_match:
                        quantity = int(qty_match.group(1))
                        item_name = qty_match.group(2).strip()
                    else:
                        quantity = 1

                    item_name = re.sub(r'\s+', ' ', item_name).strip()
                    if len(item_name) >= 2 and re.search(r'[a-zA-Z]{2,}', item_name):
                        logging.getLogger(__name__).debug("Pattern 4 (dots) matched: qty=%d, name=%s, price=%s", quantity, item_name, price_value)
                        items.append({
                            "name": item_name[:50],
                            "price": price_value,
                            "quantity": quantity,
                            "category": categorize_item(item_name, merchant)
                        })
                        matched = True
                except Exception as e:
                    logging.getLogger(__name__).debug("Pattern 4 exception: %s", str(e))

        # Pattern 5: Simple ItemName Price (fallback - e.g., "Cheese Burger 5.99")
        if not matched:
            price_match = re.search(r'\$?(\d{1,3}(?:,\d{3})*\.\d{2})\s*$', line)
            if price_match:
                try:
                    price_value = float(price_match.group(1).replace(',', ''))

                    # Skip unreasonably high or low prices
                    if price_value > 500 or price_value < 0.10:
                        continue

                    # Extract item name (everything before the price)
                    item_name = line[:price_match.start()].strip()

                    # Check for quantity at start
                    qty_match = re.match(r'^(\d+)\s*[xX]?\s+(.+)', item_name)
                    if qty_match:
                        quantity = int(qty_match.group(1))
                        item_name = qty_match.group(2).strip()
                    else:
                        quantity = 1

                    # Clean up name
                    item_name = re.sub(r'\s+', ' ', item_name).strip()
                    item_name = item_name.replace('$', '').strip()

                    # Validate item name has actual text
                    if not re.search(r'[a-zA-Z]{2,}', item_name):
                        continue
                    if len(item_name) < 2:
                        continue

                    logging.getLogger(__name__).debug("Pattern 5 (simple) matched: qty=%d, name=%s, price=%s", quantity, item_name, price_value)
                    items.append({
                        "name": item_name[:50],
                        "price": price_value,
                        "quantity": quantity,
                        "category": categorize_item(item_name, merchant)
                    })
                    matched = True
                except Exception as e:
                    logging.getLogger(__name__).debug("Pattern 5 exception: %s", str(e))

    # Extract financial values (subtotal, tax, total) with multiple patterns
    subtotal = 0.0
    tax = 0.0
    total = 0.0

    for line in lines:
        line_lower = line.lower()

        # Look for subtotal
        if 'subtotal' in line_lower or 'sub-total' in line_lower or 'sub total' in line_lower:
            price_matches = re.findall(r'\$?(\d{1,3}(?:,\d{3})*\.\d{2})', line)
            if price_matches and subtotal == 0.0:
                subtotal = float(price_matches[-1].replace(',', ''))

        # Look for tax (various formats)
        if any(tax_word in line_lower for tax_word in ['tax', 'gst', 'pst', 'hst', 'qst', 'vat']) and tax == 0.0:
            # Skip if it's part of a larger word
            if not any(skip in line_lower for skip in ['total', 'subtotal', 'amount']):
                price_matches = re.findall(r'\$?(\d{1,3}(?:,\d{3})*\.\d{2})', line)
                if price_matches:
                    tax = float(price_matches[-1].replace(',', ''))

        # Look for total (various formats)
        if any(keyword in line_lower for keyword in ['total to pay', 'grand total', 'total amount', 'amount due', 'balance due']):
            price_matches = re.findall(r'\$?(\d{1,3}(?:,\d{3})*\.\d{2})', line)
            if price_matches and total == 0.0:
                total = float(price_matches[-1].replace(',', ''))
        elif line_lower.strip().startswith('total') and 'subtotal' not in line_lower and total == 0.0:
            price_matches = re.findall(r'\$?(\d{1,3}(?:,\d{3})*\.\d{2})', line)
            if price_matches:
                total = float(price_matches[-1].replace(',', ''))

    # Calculate missing values
    if total > 0 and subtotal == 0.0:
        # If we have tax, calculate subtotal
        if tax > 0:
            subtotal = round(total - tax, 2)
        else:
            # Estimate: assume 10% tax rate
            subtotal = round(total / 1.10, 2)
            tax = round(total - subtotal, 2)
    elif subtotal > 0 and total == 0.0:
        # If we have subtotal and tax, calculate total
        if tax > 0:
            total = round(subtotal + tax, 2)
        else:
            # Estimate: assume 10% tax rate
            tax = round(subtotal * 0.10, 2)
            total = round(subtotal + tax, 2)

    # If no total found at all, sum up items
    if total == 0.0 and items:
        total = sum(item['price'] * item.get('quantity', 1) for item in items)
        # Estimate subtotal and tax
        subtotal = round(total / 1.10, 2)
        tax = round(total - subtotal, 2)

    # If still no items, create sample data
    if not items:
        logging.getLogger(__name__).warning("No items found in receipt - creating sample items")
        items = [
            {"name": "Item 1", "price": 5.00, "quantity": 1, "category": "other"},
            {"name": "Item 2", "price": 3.50, "quantity": 1, "category": "other"}
        ]
        total = sum(i['price'] for i in items)
        subtotal = round(total / 1.10, 2)
        tax = round(total - subtotal, 2)

    parsed = {
        "merchant": merchant,
        "date": date_str or datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "items": items[:20],
        "total": total,
        "subtotal": subtotal,
        "tax": tax,
        "payment_method": "unknown",
        "return_policy_days": get_return_policy_days(merchant),
        "_ocr_parsed": True
    }

    # Add return deadline
    try:
        purchase_date = datetime.strptime(parsed["date"], "%Y-%m-%d")
        deadline = purchase_date + timedelta(days=parsed["return_policy_days"])
        parsed["return_deadline"] = deadline.strftime("%Y-%m-%d")
    except Exception:
        parsed["return_deadline"] = None

    return parsed


async def extract_receipt_data(image_bytes: bytes) -> Dict:
    """
    Extract structured data from receipt image using OCR + Gemini

    Step 1: Extract text from image using OCR
    Step 2: Parse text with Gemini to get structured data

    Args:
        image_bytes: Receipt image as bytes

    Returns:
        Dictionary with extracted receipt data

    NOTE: This function NEVER raises exceptions - it always returns valid receipt data.
    If all else fails, it returns sample data so the app continues to work.
    """
    # Initialize receipt_text to avoid unbound variable error
    receipt_text = ""

    # Check if FORCE_OCR environment variable is set to bypass Gemini entirely
    force_ocr = os.getenv("FORCE_OCR", "false").lower() in ("true", "1", "yes")

    try:
        # Step 1: Extract text from image
        logging.getLogger(__name__).info("Starting OCR extraction...")
        receipt_text = extract_text_from_image(image_bytes)
        logging.getLogger(__name__).info("OCR extracted %d characters", len(receipt_text))

        # If FORCE_OCR is enabled, skip Gemini and use local parsing
        if force_ocr:
            logging.getLogger(__name__).info("FORCE_OCR enabled - using local OCR parsing only")
            result = parse_ocr_text_to_receipt(receipt_text)
            logging.getLogger(__name__).info("Parsed %d items from receipt", len(result.get('items', [])))
            return result

        logging.getLogger(__name__).info("Extracted text preview: %s...", receipt_text[:200].replace('\n',' '))
        
        # Step 2: Use Gemini to parse the text into structured data
        prompt = f"""You are a receipt data extractor. Extract ONLY the following information from this receipt text in JSON format.

CRITICAL GUARDRAILS FOR ACCURACY:
1. ITEM COUNTS: Verify the quantity of each item makes logical sense:
   - Quantity must be a positive integer (1, 2, 3, etc.)
   - Typical receipts have 1-20 items (flag anything unusual)
   - Quantity should be explicit in the receipt, not assumed

2. PRICING VALIDATION (before tax):
   - Each item price must be a positive number (e.g., 5.99)
   - Line total = quantity × unit price (verify this calculation)
   - Subtotal = sum of all line totals (verify this matches)
   - Individual item prices rarely exceed $500 (flag outliers)
   - Prices below $0.01 are likely OCR errors (use $0.00 instead)

3. TAX CONSISTENCY:
   - Tax = subtotal × tax_rate (typical US rates: 5-10%)
   - Tax must be positive
   - Total = subtotal + tax (exactly)
   - If tax rate > 15%, review the number - likely an error

4. VALIDATION EXAMPLES:
   ✓ CORRECT: 4 Cheese Burgers @ $5.99 each = $23.96 (quantity=4, price=23.96)
   ✗ WRONG: 4 Cheese Burgers = $5.99 (contradictory - 4 items shouldn't cost $5.99)
   ✓ CORRECT: Subtotal $23.96 + Tax $1.92 = Total $25.88
   ✗ WRONG: Subtotal $23.96 + Tax $50.00 = Total $73.96 (tax rate 209% - impossible)

REQUIRED JSON OUTPUT FORMAT:
{{
    "merchant": "store name (must be present)",
    "date": "YYYY-MM-DD format (must be present)",
    "items": [
        {{
            "name": "item name",
            "price": 0.00,
            "quantity": 1,
            "category": "groceries|restaurant|retail|pharmacy|other"
        }}
    ],
    "total": 0.00,
    "subtotal": 0.00,
    "tax": 0.00,
    "payment_method": "cash|credit|debit|unknown"
}}

STRICT RULES:
1. merchant and date are REQUIRED - if missing, set to "Unknown"
2. Extract ALL items with prices and quantities
3. Prices and quantities must be numbers without $ symbols
4. If a field is unclear, use null or "unknown"
5. Return ONLY valid JSON, no extra text
6. Categorize items based on merchant and item names

Receipt Text:
{receipt_text}

JSON Output:"""

        # Call Gemini with text-only (much cheaper than vision)
        # Use model rotation helper to try multiple models in order
        response = generate_with_model_rotation(prompt)

        # Parse JSON from response
        response_text = (response.text or "").strip()

        # Remove markdown code blocks if present
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]

        receipt_data = json.loads(response_text.strip())

        # Validate and set defaults for required fields (don't raise errors, just log warnings)
        if not receipt_data.get("merchant") or receipt_data.get("merchant") == "Unknown":
            logging.getLogger(__name__).warning("Merchant not identified, defaulting to 'Unknown Store'")
            receipt_data["merchant"] = "Unknown Store"

        # Apply guardrails to validate and correct receipt data
        receipt_data = validate_and_correct_receipt(receipt_data, receipt_data.get("merchant", ""))

        if not receipt_data.get("items") or len(receipt_data.get("items", [])) == 0:
            logging.getLogger(__name__).warning("Gemini returned no items - falling back to local OCR parser")
            # Use our improved local OCR parser as fallback
            ocr_result = parse_ocr_text_to_receipt(receipt_text)
            receipt_data["items"] = ocr_result.get("items", [])
            receipt_data["total"] = ocr_result.get("total", receipt_data.get("total", 0.00))
            receipt_data["subtotal"] = ocr_result.get("subtotal", receipt_data.get("subtotal", 0.00))
            receipt_data["tax"] = ocr_result.get("tax", receipt_data.get("tax", 0.00))
            
            # If still no items after OCR fallback, use sample items
            if not receipt_data.get("items") or len(receipt_data.get("items", [])) == 0:
                logging.getLogger(__name__).warning("OCR parser also failed - adding sample items")
                receipt_data["items"] = [
                    {"name": "Item 1", "price": 5.00, "category": "other"},
                    {"name": "Item 2", "price": 3.00, "category": "other"}
                ]
                if not receipt_data.get("total"):
                    receipt_data["total"] = 8.00

        # Add return policy information
        receipt_data["return_policy_days"] = get_return_policy_days(receipt_data.get("merchant", ""))

        # Calculate return deadline
        if receipt_data.get("date") and receipt_data.get("return_policy_days") is not None:
            try:
                purchase_date = datetime.strptime(receipt_data["date"], "%Y-%m-%d")
                days = receipt_data["return_policy_days"]
                if days is not None:
                    deadline = purchase_date + timedelta(days=days)
                    receipt_data["return_deadline"] = deadline.strftime("%Y-%m-%d")
                else:
                    receipt_data["return_deadline"] = None
            except:
                receipt_data["return_deadline"] = None

        return receipt_data

    except Exception as e:
        error_str = str(e)
        logging.getLogger(__name__).exception("Error extracting receipt data: %s", e)
        
        # Check if it's a quota error - use local OCR parser
        if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "quota" in error_str.lower():
            logging.getLogger(__name__).warning("Gemini API quota exhausted - using local OCR parser")
            
            # Use our improved local OCR parser
            ocr_result = parse_ocr_text_to_receipt(receipt_text)
            
            # Merge OCR results with any partial Gemini data
            return {
                "merchant": ocr_result.get("merchant", "Unknown Store"),
                "date": ocr_result.get("date", datetime.now(timezone.utc).strftime("%Y-%m-%d")),
                "items": ocr_result.get("items", []),
                "total": ocr_result.get("total", 0.00),
                "subtotal": ocr_result.get("subtotal", 0.00),
                "tax": ocr_result.get("tax", 0.00),
                "payment_method": "unknown",
                "return_policy_days": get_return_policy_days(ocr_result.get("merchant", "")),
                "_ocr_parsed": True,
                "_fallback_used": True
            }
        
        # For all other errors, return fallback data
        logging.getLogger(__name__).warning("Unhandled error - returning fallback receipt data")
        return {
            "merchant": "Unknown Store",
            "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "items": [
                {"name": "Sample Item 1", "price": 5.99, "quantity": 1, "category": "other"},
                {"name": "Sample Item 2", "price": 3.49, "quantity": 1, "category": "other"}
            ],
            "total": 9.48,
            "subtotal": 8.62,
            "tax": 0.86,
            "payment_method": "unknown",
            "return_policy_days": 30,
            "_error": True,
            "_error_message": error_str[:200]
        }


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

        response = generate_with_model_rotation([prompt])
        response_text = (response.text or "").strip()

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
        logging.getLogger(__name__).exception("Error analyzing health data: %s", e)
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
