import requests
import hashlib
import re
import json

def solve_sellauth_challenge(html):
    m = re.search(r"['\"]([A-F0-9]{40})['\"]", html)
    if not m:
        return None
    c = m.group(1)
    n1 = int(c[0], 16)
    i = 0
    while i < 1000000:
        target = (c + str(i)).encode('utf-8')
        digest = hashlib.sha1(target).digest()
        if digest[n1] == 0xb0 and digest[n1+1] == 0x0b:
            return f"{c}{i}"
        i += 1
    return None

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
})

# Warm up challenge cookie
url_base = "https://shopadopt.mysellauth.com"
r = session.get(url_base)
if r.status_code == 503:
    cookie_val = solve_sellauth_challenge(r.text)
    if cookie_val:
        session.cookies.set("yX3", cookie_val, domain="shopadopt.mysellauth.com")
        session.cookies.set("yX3", cookie_val, domain=".mysellauth.com")

slugs = [
    "326-350-potions-249k-273l-bucks",
    "826-850-potions-473k-568k-bucks",
    "1276-1300-potions-759k-869k-bucks"
]

for slug in slugs:
    res = session.get(f"{url_base}/product/{slug}")
    if res.status_code == 200:
        # Search for stock in page HTML or data attribute
        # Try finding json data in page
        m = re.search(r'data-page="([^"]+)"', res.text)
        if m:
            page_data = json.loads(m.group(1).replace('&quot;', '"'))
            product = page_data.get('props', {}).get('product', {})
            stock = product.get('stock') or product.get('stock_count')
            print(f"Slug: {slug} -> EXACT STOCK FROM INERTIA: {stock}")
        else:
            # regex search for stock
            stocks = re.findall(r'"stock":\s*(\d+)', res.text)
            print(f"Slug: {slug} -> EXACT STOCKS REGEX: {stocks}")
    else:
        print(f"Slug {slug} -> Status: {res.status_code}")
