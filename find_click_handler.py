with open("checkout_bundle.js", "r", encoding="utf-8") as f:
    js = f.read()

import re

# Find where payment method button is clicked
matches = re.finditer(r'payment_method_id|selectedPaymentMethod|paymentMethod', js)
for m in matches:
    pos = m.start()
    snippet = js[max(0, pos-100):pos+300]
    if "onClick" in snippet or "handleSubmit" in snippet or "PUT" in snippet or "POST" in snippet:
        print("MATCH:")
        print(snippet.encode('ascii', 'ignore').decode('ascii'))
        print("-" * 50)
