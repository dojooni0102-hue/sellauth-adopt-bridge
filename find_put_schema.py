with open("checkout_bundle.js", "r", encoding="utf-8") as f:
    js = f.read()

import re

# Find how payment_method is updated
matches = re.finditer(r'payment_method|gateway', js)
for m in matches:
    pos = m.start()
    snippet = js[max(0, pos-100):pos+250]
    if "PUT" in snippet or "method" in snippet or "api-internal-3" in snippet:
        print("MATCH:", snippet.encode('ascii', 'ignore').decode('ascii'))
        print("-" * 50)
