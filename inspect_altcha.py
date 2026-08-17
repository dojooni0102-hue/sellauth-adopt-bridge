with open("checkout_bundle.js", "r", encoding="utf-8") as f:
    js = f.read()

import re

# Search for altcha or captcha in js
matches = re.finditer(r'altcha', js, re.IGNORECASE)
for m in matches:
    pos = m.start()
    snippet = js[max(0, pos-200):pos+400]
    print("=== ALTCHA SNIPPET ===")
    print(snippet.encode('ascii', 'ignore').decode('ascii'))
