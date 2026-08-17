with open("checkout_bundle.js", "r", encoding="utf-8") as f:
    js = f.read()

import re

# Search for status or pending in checkout bundle
matches = re.finditer(r'status\s*:\s*["\']pending["\']|createCryptoAddress|generateAddress', js, re.IGNORECASE)
for m in matches:
    pos = m.start()
    print("STATUS MATCH:")
    print(js[max(0, pos-100):pos+200].encode('ascii', 'ignore').decode('ascii'))
