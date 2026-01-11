# Receipt Parsing Guardrails Implementation

## Overview
Comprehensive guardrails system for validating and correcting receipt parsing by the AI. Ensures accuracy for item quantities, pricing, and financial calculations.

## Implementation Details

### 1. Core Validation Function: `validate_and_correct_receipt()`

Located in `backend/gemini_service.py`, this function applies guardrails to receipt data:

#### Item Validation
- **Quantity Checks:**
  - Must be positive integer (1, 2, 3, ...)
  - Automatically corrects non-numeric quantities to 1
  - Caps unrealistic quantities (> 1000) to 100
  - Sets negative quantities to 1

- **Price Checks:**
  - Must be positive (detects and corrects negative prices)
  - Flags suspiciously low prices (< $0.01) and sets to $0.00
  - Flags suspiciously high prices (> $5000) for review (with logging)
  - Validates price is numeric

#### Financial Calculation Validation
- **Subtotal Verification:**
  - Ensures subtotal ≈ sum of all (quantity × unit_price)
  - Allows 5% tolerance for rounding
  - Auto-corrects mismatched subtotals

- **Tax Rate Validation:**
  - Typical US rates: 5-10%
  - Flags rates > 20% as suspicious
  - Validates total = subtotal + tax

- **Total Calculation:**
  - Verifies total = subtotal + tax
  - Auto-corrects if calculation is wrong

### 2. Enhanced Gemini Prompt with Guardrails

The prompt now includes detailed guardrail instructions that guide the AI:

```
CRITICAL GUARDRAILS FOR ACCURACY:

1. ITEM COUNTS - Verify quantity makes logical sense
   - Quantity must be positive integer (1, 2, 3, etc.)
   - Typical receipts have 1-20 items
   - Quantity should be explicit, not assumed

2. PRICING VALIDATION (before tax)
   - Each item price must be positive (e.g., 5.99)
   - Line total = quantity × unit price
   - Subtotal = sum of all line totals
   - Individual item prices rarely exceed $500
   - Prices below $0.01 are likely OCR errors

3. TAX CONSISTENCY
   - Tax = subtotal × tax_rate (typical: 5-10%)
   - Tax must be positive
   - Total = subtotal + tax (exactly)
   - If tax rate > 15%, likely an error

4. VALIDATION EXAMPLES
   ✓ CORRECT: 4 Cheese Burgers @ $5.99 each = $23.96
   ✗ WRONG: 4 Cheese Burgers = $5.99
   ✓ CORRECT: Subtotal $23.96 + Tax $1.92 = Total $25.88
   ✗ WRONG: Subtotal $23.96 + Tax $50.00 = Total $73.96 (209% tax!)
```

### 3. Integration Points

#### Point 1: After Gemini Parsing
```python
receipt_data = json.loads(response_text.strip())
# Apply guardrails to validate and correct
receipt_data = validate_and_correct_receipt(receipt_data, receipt_data.get("merchant", ""))
```

#### Point 2: Local OCR Fallback
```python
parsed = {
    "merchant": merchant,
    "date": date_str,
    "items": items[:20],
    "total": round(total, 2),
    "subtotal": round(subtotal, 2),
    "tax": round(tax, 2),
    ...
}
# Apply guardrails before returning
parsed = validate_and_correct_receipt(parsed, merchant)
```

## Validation Examples

### Example 1: Negative Price Correction
**Input:** Item with price = -$5.99
**Output:** Price corrected to $0.00 with warning logged
**Correction Type:** `negative_price_set_to_zero`

### Example 2: Invalid Quantity Correction
**Input:** Item with quantity = "invalid" or quantity = -5
**Output:** Quantity corrected to 1
**Correction Type:** `quantity_converted_to_1` or `quantity_set_to_1`

### Example 3: Subtotal Mismatch
**Input:** 2 items @ $5.99 each, subtotal shows $100.00
**Output:** Subtotal corrected to $11.98 (2 × $5.99)
**Math Fix:** Recalculates correct total = $11.98 + tax

### Example 4: Suspiciously High Tax Rate
**Input:** Subtotal $9.48, Tax $50.00 (527% rate)
**Output:** Logged as warning, but not auto-corrected (manual review)
**Action:** Logged warning for investigation

### Example 5: Quantity Cap
**Input:** Item with quantity = 9999
**Output:** Capped to 100, recalculates subtotal
**Correction Type:** `quantity_capped`

## Testing

### Test File: `backend/tests/test_guardrails.py`

Comprehensive test suite with 8 test cases:

1. ✅ **Negative price detection** - Catches and corrects negative prices
2. ✅ **Invalid quantity correction** - Fixes non-numeric and negative quantities
3. ✅ **Extremely high prices** - Flags values > $5000
4. ✅ **Suspiciously low prices** - Corrects values < $0.01
5. ✅ **Unrealistic quantities** - Caps quantities > 1000
6. ✅ **Subtotal math validation** - Corrects sum mismatches
7. ✅ **Tax rate validation** - Flags rates > 20%
8. ✅ **Correct receipt passthrough** - Valid data unchanged

**Result:** 100% success rate (8/8 tests passing)

All validation ensures:
- Quantity × Unit Price = Line Total ✓
- Sum of Line Totals = Subtotal ✓
- Subtotal + Tax = Total ✓

## Logging

All corrections are logged with appropriate levels:

- **Info Level:** Normal corrections, valid data passing through
- **Warning Level:** Suspicious values, auto-corrections, high tax rates
- **Debug Level:** Detailed parsing patterns

Example log output:
```
Item 'Cheese Burger' has invalid quantity -5, setting to 1
Subtotal $100.00 doesn't match items total $15.47, using items total
Tax rate 527.4% is suspiciously high (> 20%), reviewing
Receipt validation: 2 items, subtotal=$15.47, tax=$1.55, total=$17.02
```

## Future Enhancements

1. **Configurable Thresholds:** Allow customization of price/quantity bounds
2. **Merchant-specific Rules:** Different validation for different store types
3. **Historical Baseline:** Compare against user's typical purchases
4. **Advanced ML Scoring:** Use ML for confidence scoring of corrections
5. **User Feedback Loop:** Learn from user corrections for better future parsing

## Files Modified

- `backend/gemini_service.py`
  - Added `validate_and_correct_receipt()` function
  - Updated Gemini prompt with guardrail instructions
  - Integrated guardrails in `extract_receipt_data()`
  - Integrated guardrails in `parse_ocr_text_to_receipt()`

- `backend/tests/test_guardrails.py` (new)
  - Added comprehensive validation test suite

## Deployment Notes

✅ Backwards compatible - doesn't break existing functionality
✅ Non-destructive - logs all corrections for audit trail
✅ Performant - minimal overhead added to parsing pipeline
✅ Production-ready - comprehensive error handling
