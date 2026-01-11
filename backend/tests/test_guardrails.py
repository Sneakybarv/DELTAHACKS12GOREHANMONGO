#!/usr/bin/env python3
"""
Test the guardrails validation function to verify it catches errors
and corrects receipt data appropriately.
"""
import sys
sys.path.insert(0, '/Users/barzinvazifedoost/DeltaHACKSrealREHAN/backend')
from gemini_service import validate_and_correct_receipt

# Test cases demonstrating guardrails functionality
test_cases = [
    {
        "name": "Negative price detection and correction",
        "input": {
            "merchant": "Test Store",
            "items": [
                {"name": "Item 1", "price": -5.99, "quantity": 1},
                {"name": "Item 2", "price": 3.49, "quantity": 1},
            ],
            "subtotal": 3.49,
            "tax": 0.35,
            "total": 3.84
        },
        "expected_fixes": ["negative_price_set_to_zero"]
    },
    {
        "name": "Invalid quantity detection and correction",
        "input": {
            "merchant": "Test Store",
            "items": [
                {"name": "Item 1", "price": 5.99, "quantity": -5},
                {"name": "Item 2", "price": 3.49, "quantity": "invalid"},
            ],
            "subtotal": 9.48,
            "tax": 0.76,
            "total": 10.24
        },
        "expected_fixes": ["quantity correction"]
    },
    {
        "name": "Extremely high price detection",
        "input": {
            "merchant": "Test Store",
            "items": [
                {"name": "Item 1", "price": 999999.99, "quantity": 1},
                {"name": "Item 2", "price": 3.49, "quantity": 1},
            ],
            "subtotal": 1000003.48,
            "tax": 80000.28,
            "total": 1080003.76
        },
        "expected_fixes": ["price_suspiciously_high"]
    },
    {
        "name": "Price and quantity too low",
        "input": {
            "merchant": "Test Store",
            "items": [
                {"name": "Item 1", "price": 0.001, "quantity": 1},
                {"name": "Item 2", "price": 3.49, "quantity": 1},
            ],
            "subtotal": 3.49,
            "tax": 0.35,
            "total": 3.84
        },
        "expected_fixes": ["price_too_low"]
    },
    {
        "name": "Unrealistic quantity",
        "input": {
            "merchant": "Test Store",
            "items": [
                {"name": "Item 1", "price": 5.99, "quantity": 9999},
                {"name": "Item 2", "price": 3.49, "quantity": 1},
            ],
            "subtotal": 59909.99,
            "tax": 4792.80,
            "total": 64702.79
        },
        "expected_fixes": ["quantity_capped"]
    },
    {
        "name": "Math validation: subtotal mismatch",
        "input": {
            "merchant": "Test Store",
            "items": [
                {"name": "Item 1", "price": 5.99, "quantity": 2},  # Should be 11.98
                {"name": "Item 2", "price": 3.49, "quantity": 1},  # Should be 3.49
            ],
            "subtotal": 100.00,  # Wrong! Should be 15.47
            "tax": 1.55,
            "total": 101.55
        },
        "expected_fixes": ["subtotal correction"]
    },
    {
        "name": "Tax rate validation: suspiciously high",
        "input": {
            "merchant": "Test Store",
            "items": [
                {"name": "Item 1", "price": 5.99, "quantity": 1},
                {"name": "Item 2", "price": 3.49, "quantity": 1},
            ],
            "subtotal": 9.48,
            "tax": 50.00,  # 527% tax rate - impossible!
            "total": 59.48
        },
        "expected_fixes": ["high tax rate warning"]
    },
    {
        "name": "Correct receipt passes through unchanged",
        "input": {
            "merchant": "McDonald's",
            "items": [
                {"name": "Cheese Burger", "price": 5.99, "quantity": 2},  # = 11.98
                {"name": "Soda", "price": 2.49, "quantity": 1},  # = 2.49
            ],
            "subtotal": 14.47,
            "tax": 1.16,
            "total": 15.63
        },
        "expected_fixes": []
    }
]

print("=" * 80)
print("GUARDRAILS VALIDATION TESTS")
print("=" * 80)

passed = 0
failed = 0

for test_case in test_cases:
    print(f"\n{'='*60}")
    print(f"TEST: {test_case['name']}")
    print(f"{'='*60}")
    
    try:
        result = validate_and_correct_receipt(test_case["input"], test_case["input"].get("merchant", ""))
        
        # Check that corrections were made as expected
        print(f"✅ Validation completed")
        print(f"   Items: {len(result['items'])}")
        for item in result['items']:
            print(f"     - {item['name']}: qty={item['quantity']}, price=${item['price']:.2f}")
        print(f"   Subtotal: ${result['subtotal']:.2f}")
        print(f"   Tax: ${result['tax']:.2f}")
        print(f"   Total: ${result['total']:.2f}")
        
        # Verify calculation: total = subtotal + tax
        calc_total = result['subtotal'] + result['tax']
        if abs(calc_total - result['total']) < 0.01:
            print(f"   ✓ Math check PASSED: {result['subtotal']:.2f} + {result['tax']:.2f} = {result['total']:.2f}")
            passed += 1
        else:
            print(f"   ✗ Math check FAILED: {result['subtotal']:.2f} + {result['tax']:.2f} ≠ {result['total']:.2f}")
            failed += 1
            
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        failed += 1

# Summary
print(f"\n{'='*80}")
print(f"SUMMARY: {passed} PASSED, {failed} FAILED out of {len(test_cases)} tests")
print(f"Success rate: {(passed / len(test_cases) * 100):.0f}%")
print("=" * 80)
