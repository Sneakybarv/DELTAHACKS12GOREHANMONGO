# Weight-Based Pricing OCR Enhancement

## Problem Statement
The OCR parser was failing to extract items from grocery receipts with weight-based pricing formats. When OCR text contained weight information (e.g., "0.778kg NET @ $5.99/kg") mixed with item names on the same line, the parser would:
1. Skip entire lines containing weight keywords due to overly broad skip_words filter
2. Fail to parse items that had weight information prefixes

**Example problematic line:**
```
0.778kg NET @ $5.99/kg BANANA CAVENDISH $1.32
```

Expected: Extract "BANANA CAVENDISH" at "$1.32"
Actual: Line skipped due to "net" being in skip_words

## Root Causes Identified

### Root Cause #1: Over-Aggressive Skip Words Filter
The skip_words list included:
- "net"
- "@"  
- "kg"
- "weight"
- "unit price"

These were intended to filter transaction metadata but were too broad, causing entire receipt lines containing these words to be skipped.

### Root Cause #2: No Weight-Line Stripping Logic
When weight information appeared before item names on the same line, there was no logic to:
1. Detect the weight pattern
2. Remove it from the item name extraction
3. Preserve the actual item name and price

### Root Cause #3: Loyalty Discount Not Applied
Discount amounts were extracted as positive instead of negative values, causing:
- "-$15.00" loyalty discount extracted as "+15.00"
- Final total calculated as $54.20 instead of correct $24.20 (should be $39.20 - $15.00)

## Solution Implemented

### Fix #1: Refined Skip Words Filter (Line 260-272)
**Changed:**
```python
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
```
**Removed:** "net", "@", "kg", "lb", "lbs", "oz", "weight", "unit price"

### Fix #2: Precise Weight-Line Pattern Matching (Line 287-290)
**Added:**
```python
# Skip ONLY pure weight lines (nothing before or after weight pattern)
if re.match(r'^\s*\d+\.?\d*\s*kg\s*(net)?\s*@\s*\$?\d+\.?\d*\s*/?\s*kg\s*$', line_lower, re.IGNORECASE):
    continue
```
Uses `re.match()` (start of line) instead of `re.search()` to ensure only lines that are PURELY weight information are skipped.

### Fix #3: Weight-Prefix Stripping in Pattern 2 (Line 364-370)
**Added to ItemName extraction:**
```python
# Remove weight info if present (e.g., "0.778kg NET @ 5.99/kg BANANA" -> "BANANA")
weight_prefix = re.search(r'^\d+\.?\d*\s*kg\s*(net)?\s*@\s*\$?\d+\.?\d*/?\s*kg\s+', item_name.lower())
if weight_prefix:
    item_name = item_name[weight_prefix.end():].strip()
```
When an item name contains a weight prefix, it's cleanly removed before validation.

### Fix #4: Proper Discount Sign Preservation (Line 454-459)
**Changed:**
```python
# Extract loyalty/discounts (negative amounts)
if any(disc in line_lower for disc in ['loyalty', 'discount', 'coupon', 'member discount']):
    price_matches = re.findall(price_pattern, line)
    if price_matches:
        discount_amt = float(price_matches[-1].replace(',', ''))
        # If the line contains a minus/negative before the amount, make it negative
        if '-' in line[:line.rfind(price_matches[-1])] or line.strip().startswith('-'):
            discount_amt = -abs(discount_amt)
        discounts += discount_amt
```
Now properly detects and preserves the negative sign for discounts.

## Test Results

### Before Fix
```
Items extracted: 5/12
Total: $54.20 (INCORRECT)
Missing: BANANA CAVENDISH, BROCCOLI, BRUSSEL SPROUTS, PEAS SNOW, TOMATOES GRAPE + duplicates
```

### After Fix
```
✓ Items extracted: 12/12
✓ All items with clean names (weight info stripped)
✓ Subtotal: $39.20 ✓
✓ Total: $24.20 ✓ (correctly applied -$15.00 loyalty discount)

Items:
  1. ZUCCHINI GREEN: $4.66
  2. BANANA CAVENDISH: $1.32 ✓ (was missing)
  3. SPECIAL: $0.99
  4. SPECIAL: $1.50
  5. POTATOES BRUSHED: $3.97
  6. BROCCOLI: $4.84 ✓ (was missing)
  7. BRUSSEL SPROUTS: $5.15 ✓ (was missing)
  8. SPECIAL: $0.99
  9. GRAPES GREEN: $7.03
  10. PEAS SNOW: $3.27 ✓ (was missing)
  11. TOMATOES GRAPE: $2.99 ✓ (was missing)
  12. LETTUCE ICEBERG: $2.49
```

### Regression Testing
✓ Advanced test suite: 6/6 PASSED (100%)
✓ Original parsing tests: ALL OK
✓ Backward compatibility: MAINTAINED

## Technical Details

### Changed Files
- `backend/gemini_service.py` - Lines 254-420 (_extract_items_smart function)
- `backend/gemini_service.py` - Lines 430-460 (_extract_financial_values_robust function)

### Key Functions Modified
1. `_extract_items_smart()` - Now handles weight-based pricing with proper filtering
2. `_extract_financial_values_robust()` - Now correctly applies negative discounts

### Pattern Matching Strategy
The parser now uses a 2-tier approach:
1. **Tier 1**: Strict weight-line detection (pure weight-only lines)
2. **Tier 2**: Weight-prefix stripping (for mixed lines with item+weight)

This allows proper parsing of receipts where OCR may format weight information either on separate lines or mixed with item names.

## Files Modified
- `backend/gemini_service.py` - Core OCR parsing improvements
- `backend/tests/test_ocr_advanced.py` - Test suite passing
- `backend/tests/test_ocr_parsing.py` - Original tests still passing

## Impact
- **Grocery receipts**: Now correctly parse weight-based pricing (kg NET @ $price/kg)
- **Discount handling**: Loyalty discounts and coupons now properly reduce totals
- **Compatibility**: All existing receipt formats continue to work correctly
- **User receipts**: Grocery store receipts with weight-based items now extract all 12+ items correctly
