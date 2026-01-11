#!/usr/bin/env python3
"""
Advanced OCR parsing tests - demonstrates improved parsing capabilities
Tests edge cases, various receipt formats, and robustness improvements
"""
import sys
sys.path.insert(0, '/Users/barzinvazifedoost/DeltaHACKSrealREHAN/backend')
from gemini_service import parse_ocr_text_to_receipt

# Test cases with diverse receipt formats
test_cases = [
    {
        "name": "Standard Fast Food Receipt",
        "text": """
        McDONALDS #12345
        123 Main St
        
        4x Cheese Burger      5.99      23.96
        2x Large Soda         2.49       4.98
        1x Fries              1.99       1.99
        
        Subtotal:                       30.93
        Tax (10%)                        3.09
        Total to Pay:                   34.02
        """,
        "expected_items": ["Cheese Burger", "Soda", "Fries"],
        "expected_merchant": "McDonald's",
        "expected_total": 34.02
    },
    {
        "name": "Grocery Store Receipt with Varying Formats",
        "text": """
        WALMART SUPERCENTER #4521
        
        Milk 2% Gallon          3.99
        Bread Whole Wheat       2.49
        2 @ 5.99 = 11.98  Cheese Block
        Eggs Dozen              4.29
        Apples Red              0.99/lb x 3 = 2.97
        
        Subtotal:                       26.21
        Tax (8.5%)                       2.23
        TOTAL:                          28.44
        """,
        "expected_items": ["Milk", "Bread", "Cheese", "Eggs", "Apples"],
        "expected_merchant": "Walmart",
        "expected_total": 28.44
    },
    {
        "name": "Receipt with OCR Noise and Formatting",
        "text": """
        STARBUCKS COFFEE
        Store #1234
        
        1x Grande Caffe Latte   5.45      5.45
        1x Blueberry Muffin     3.99      3.99
        1x VENTI Caramel        6.25      6.25
        
        ========================
        Subtotal              15.69
        Tax                    1.26
        Total                 16.95
        ========================
        Thank you!
        """,
        "expected_items": ["Latte", "Muffin", "Caramel"],
        "expected_merchant": "Starbucks",
        "expected_total": 16.95
    },
    {
        "name": "Pharmacy Receipt with Long Item Names",
        "text": """
        CVS PHARMACY #5678
        123 Oak Avenue
        
        Vitamin D3 1000 IU Softgels    12.99
        Ibuprofen 200mg Tablets 100ct   4.99
        Triple Antibiotic Ointment      3.49
        
        Subtotal:                       21.47
        Tax (7%)                         1.50
        TOTAL TO PAY:                   22.97
        """,
        "expected_items": ["Vitamin", "Ibuprofen", "Antibiotic"],
        "expected_merchant": "CVS",
        "expected_total": 22.97
    },
    {
        "name": "Receipt with Promotional Text (should be filtered)",
        "text": """
        IKEA
        Store #123
        
        1  Hemnes Bed Frame               299.99    299.99
        4  Kallax Shelf Unit               49.99    199.96
        2  Sultan Mattress              199.99    399.98
        
        Take advantage of our summer sale! Save 25%!
        Get a free pillow with every mattress purchase.
        Limited time offer!
        
        Subtotal:                                   899.93
        Delivery:                                    50.00
        Tax (10%):                                   95.00
        Total:                                     1044.93
        """,
        "expected_items": ["Bed", "Shelf", "Mattress"],
        "expected_merchant": "IKEA",
        "expected_total": 1044.93
    },
    {
        "name": "Small Restaurant Receipt with Tip Line",
        "text": """
        Chipotle Mexican Grill
        
        1  Chicken Bowl Rice Black Beans  8.95      8.95
        1  Guacamole Upcharge             2.45      2.45
        1  Sprite Large                   2.50      2.50
        
        Subtotal:                                   13.90
        Tax:                                        1.11
        TOTAL:                                     15.01
        Tip: _____________
        Total with Tip: ___________
        """,
        "expected_items": ["Chicken", "Guacamole", "Sprite"],
        "expected_merchant": "Chipotle",
        "expected_total": 15.01
    }
]

def validate_receipt(result, test_case):
    """Validate receipt extraction against expected values"""
    errors = []
    
    # Check merchant
    if test_case["expected_merchant"].lower() not in result["merchant"].lower():
        errors.append(f"Merchant mismatch: expected '{test_case['expected_merchant']}', got '{result['merchant']}'")
    
    # Check items extracted
    items = result.get("items", [])
    if len(items) == 0:
        errors.append(f"No items extracted (expected {len(test_case['expected_items'])})")
    
    # Check total
    expected_total = test_case["expected_total"]
    actual_total = result.get("total", 0)
    if abs(actual_total - expected_total) > 0.01:
        errors.append(f"Total mismatch: expected ${expected_total:.2f}, got ${actual_total:.2f}")
    
    return errors

# Run tests
print("=" * 80)
print("ADVANCED OCR PARSING TESTS")
print("=" * 80)

passed = 0
failed = 0

for test_case in test_cases:
    print(f"\n{'='*80}")
    print(f"TEST: {test_case['name']}")
    print(f"{'='*80}")
    
    try:
        result = parse_ocr_text_to_receipt(test_case["text"])
        
        # Validate
        errors = validate_receipt(result, test_case)
        
        if not errors:
            print(f"✅ PASSED")
            print(f"   Merchant: {result['merchant']}")
            print(f"   Items: {len(result['items'])} extracted")
            for item in result['items'][:3]:
                print(f"     - {item['name']}: ${item['price']:.2f}")
            if len(result['items']) > 3:
                print(f"     ... and {len(result['items']) - 3} more items")
            print(f"   Total: ${result['total']:.2f}")
            passed += 1
        else:
            print(f"❌ FAILED")
            for error in errors:
                print(f"   - {error}")
            print(f"\n   Actual result:")
            print(f"   Merchant: {result['merchant']}")
            print(f"   Items extracted: {len(result['items'])}")
            for item in result['items'][:3]:
                print(f"     - {item['name']}: ${item['price']:.2f}")
            print(f"   Total: ${result['total']:.2f}")
            failed += 1
    
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
        failed += 1

# Summary
print(f"\n{'='*80}")
print(f"SUMMARY: {passed} PASSED, {failed} FAILED out of {len(test_cases)} tests")
print(f"Success rate: {100 * passed // len(test_cases)}%")
print(f"{'='*80}\n")
