with open("supplier_page.html", "r", encoding="utf-8") as f:
    html = f.read()

import re
import json

m = re.search(r'"variants"\s*:\s*(\[\{.*?\}\])', html)
if m:
    variants = json.loads(m.group(1))
    print("FOUND VARIANTS:")
    for v in variants:
        print(f"  Variant ID: {v.get('id')} | Price: {v.get('price')} | Stock: {v.get('stock')}")
