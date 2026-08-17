with open("checkout_bundle.js", "r", encoding="utf-8") as f:
    js = f.read()

import re

matches = re.finditer(r'https://api-internal-3\.sellauth\.com[^\'"`\s\)]+', js)
for m in matches:
    pos = m.start()
    print("URL:", m.group(0))
    print("CONTEXT:", js[max(0, pos-150):pos+250].encode('ascii', 'ignore').decode('ascii'))
    print("=" * 60)
