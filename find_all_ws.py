with open("checkout_bundle.js", "r", encoding="utf-8") as f:
    js = f.read()

import re

for m in re.finditer(r'ws\([a-zA-Z0-9_\.]+\s*,', js):
    pos = m.start()
    print("=== WS CALL CONTEXT ===")
    print(js[max(0, pos-200):pos+400].encode('ascii', 'ignore').decode('ascii'))
