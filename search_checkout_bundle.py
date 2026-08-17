with open("checkout_bundle.js", "r", encoding="utf-8") as f:
    js = f.read()

import re

# Search for turnstile rendering or token parameter
matches = re.finditer(r'turnstile\.render|sitekey|captcha_verification_failed|/v1/checkout', js, re.IGNORECASE)
for m in matches:
    pos = m.start()
    snippet = js[max(0, pos-150):pos+250]
    print("--- MATCH ---")
    print(snippet.encode('ascii', 'ignore').decode('ascii'))
