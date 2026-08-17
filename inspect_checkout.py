import re
import json

with open("supplier_page.html", "r", encoding="utf-8") as f:
    html = f.read()

print("HTML Length:", len(html))

# Search for any JSON objects or script tags
scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
print("Script tags count:", len(scripts))

import sys
sys.stdout.reconfigure(encoding='utf-8')

for i, s in enumerate(scripts):
    if "product" in s.lower() or "variant" in s.lower() or "shop" in s.lower():
        print(f"--- SCRIPT {i} ---")
        print(s[:500].encode('ascii', 'ignore').decode('ascii'))

print("Matches for shop_id:")
for m in re.finditer(r'["\']?shop_id["\']?\s*[:=]\s*(\d+)', html, re.IGNORECASE):
    print("Found shop_id:", m.group(0))

print("Matches for product_id:")
for m in re.finditer(r'["\']?product_id["\']?\s*[:=]\s*(\d+)', html, re.IGNORECASE):
    print("Found product_id:", m.group(0))
