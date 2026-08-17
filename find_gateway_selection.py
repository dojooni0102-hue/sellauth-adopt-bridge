with open("checkout_bundle.js", "r", encoding="utf-8") as f:
    js = f.read()

import re

# Search for gateway update in checkout bundle
matches = re.finditer(r'gateway:\s*[a-zA-Z0-9_\.]+|selectedGateway', js)
for m in matches:
    pos = m.start()
    snippet = js[max(0, pos-100):pos+200]
    print("--- GATEWAY SNIPPET ---")
    print(snippet.encode('ascii', 'ignore').decode('ascii'))
