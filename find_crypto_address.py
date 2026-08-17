with open("checkout_bundle.js", "r", encoding="utf-8") as f:
    js = f.read()

import re

matches = re.finditer(r'crypto_address', js)
for m in matches:
    pos = m.start()
    print("CRYPTO ADDRESS CONTEXT:")
    print(js[max(0, pos-200):pos+300].encode('ascii', 'ignore').decode('ascii'))
