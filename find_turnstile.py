with open("supplier_page.html", "r", encoding="utf-8") as f:
    html = f.read()

import re

# Search for turnstile sitekey
sitekey = re.findall(r'data-sitekey=[\'\"]([^\'\"]+)', html)
print("Turnstile Sitekey:", sitekey)

turnstile_scripts = [s for s in html.splitlines() if "turnstile" in s.lower() or "cf-" in s.lower()]
for s in turnstile_scripts:
    print("TURNSTILE LINE:", s[:150].encode('ascii', 'ignore').decode('ascii'))
