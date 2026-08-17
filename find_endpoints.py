with open("checkout_bundle.js", "r", encoding="utf-8") as f:
    js = f.read()

import re

# Search for POST /v1/checkout or similar
matches = re.finditer(r'fetch\([`"\']https://api-internal-3\.sellauth\.com/v1/checkout/[^`"\']+', js)
for m in matches:
    print("ENDPOINT:", m.group(0))
