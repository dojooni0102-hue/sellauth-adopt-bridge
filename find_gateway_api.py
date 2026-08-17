with open("checkout_bundle.js", "r", encoding="utf-8") as f:
    js = f.read()

import re

# Find the function that gets called when user clicks "Pay with LTC" or selects gateway
matches = re.finditer(r'selectGateway|setGateway|payment_method_id|crypto_address', js)
for m in matches:
    pos = m.start()
    snippet = js[max(0, pos-100):pos+250]
    if "fetch(" in snippet or "api-internal-3" in snippet or "method:" in snippet:
        print("--- API CALL SNIPPET ---")
        print(snippet.encode('ascii', 'ignore').decode('ascii'))
