with open("supplier_page.html", "r", encoding="utf-8") as f:
    html = f.read()

import re

for line in html.splitlines():
    if "variant" in line.lower() and "id" in line.lower():
        print("LINE:", line[:200].encode('ascii', 'ignore').decode('ascii'))
