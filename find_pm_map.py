with open("checkout_bundle.js", "r", encoding="utf-8") as f:
    js = f.read()

import re

matches = re.finditer(r'payment_methods\.map|\.payment_methods', js)
for m in matches:
    pos = m.start()
    print("PAYMENT METHODS MAP CONTEXT:")
    print(js[max(0, pos-100):pos+600].encode('ascii', 'ignore').decode('ascii'))
    print("=" * 60)
