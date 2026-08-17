with open("checkout_bundle.js", "r", encoding="utf-8") as f:
    js = f.read()

import re

# Search for calls to ws function
matches = re.finditer(r'ws\([a-zA-Z0-9_\.]+\s*,\s*\{[^\}]+\}', js)
for m in matches:
    print("WS CALL:", m.group(0))
