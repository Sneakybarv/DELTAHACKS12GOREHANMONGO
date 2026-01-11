# Simple OCR parsing tests for parse_ocr_text_to_receipt
import sys
sys.path.insert(0, '/Users/barzinvazifedoost/DeltaHACKSrealREHAN/backend')
from gemini_service import parse_ocr_text_to_receipt

samples = [
    (
        "4   Cheese Burger          5.99    23.96\n4   Soda                   0.49     1.96\n2   Cinnamon Bun           1.00     2.00",
        {
            'Cheese Burger':4,
            'Soda':4,
            'Cinnamon Bun':2
        }
    ),
    (
        # noisy spacing / tabs
        "4\tCheese Burger    5.99\t23.96\n4 Cheese   Soda 0.49 1.96\n2 Cinnamon Bun 1.00 2.00",
        {
            'Cheese Burger':4,
            'Soda':4,
            'Cinnamon Bun':2
        }
    ),
    (
        # Promotional text mixed in
        "4 Cheese Burger 5.99 23.96\nTake home a bag of meatballs and 2 pkgs of cream sauce for only $9.99\n4 Soda 0.49 1.96\n2 Cinnamon Bun 1.00 2.00",
        {
            'Cheese Burger':4,
            'Soda':4,
            'Cinnamon Bun':2
        }
    )
]

all_ok = True
for text, expected in samples:
    res = parse_ocr_text_to_receipt(text)
    items = res.get('items', [])
    print('\nInput:\n', text)
    print('\nParsed items:')
    for it in items:
        print(' -', it)
    # verify expected quantities
    for name, qty in expected.items():
        found = False
        for it in items:
            if name.lower() in it['name'].lower():
                found = True
                if it.get('quantity', 1) != qty:
                    print(f"FAIL: {name} qty {it.get('quantity')} != {qty}")
                    all_ok = False
                break
        if not found:
            print(f"FAIL: {name} not found in parsed items")
            all_ok = False

print('\nALL OK' if all_ok else '\nSOME TESTS FAILED')
