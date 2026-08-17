with open("checkout_bundle.js", "r", encoding="utf-8") as f:
    js = f.read()

import re

# Search for altcha challenge URL
matches = re.finditer(r'challengeurl|altcha\.org|api-internal-3\.sellauth\.com[^\"]*altcha', js, re.IGNORECASE)
for m in matches:
    pos = m.start()
    snippet = js[max(0, pos-150):pos+300]
    print("--- ALTCHA CHALLENGE URL ---")
    print(snippet.encode('ascii', 'ignore').decode('ascii'))
