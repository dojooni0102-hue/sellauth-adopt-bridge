import requests
import hashlib
import re
import json

supplier_session = requests.Session()
supplier_session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
})

def solve_sellauth_challenge(html):
    m = re.search(r"['\"]([A-F0-9]{40})['\"]", html)
    if not m:
        return None
    c = m.group(1)
    n1 = int(c[0], 16)
    i = 0
    while i < 1000000:
        digest = hashlib.sha1((c + str(i)).encode('utf-8')).digest()
        if digest[n1] == 0xb0 and digest[n1+1] == 0x0b:
            return f"{c}{i}"
        i += 1
    return None

# Warm up session with PoW cookie
res = supplier_session.get("https://shopadopt.mysellauth.com/product/326-350-potions-249k-273l-bucks")
if res.status_code == 503:
    cookie = solve_sellauth_challenge(res.text)
    supplier_session.cookies.set("yX3", cookie, domain="shopadopt.mysellauth.com")
    supplier_session.cookies.set("yX3", cookie, domain=".mysellauth.com")
    res = supplier_session.get("https://shopadopt.mysellauth.com/product/326-350-potions-249k-273l-bucks")

print("Product page status:", res.status_code)

# Check csrf token and checkout endpoints on shopadopt
csrf_match = re.search(r'name="csrf-token"\s+content="([^"]+)"', res.text)
csrf_token = csrf_match.group(1) if csrf_match else None
print("CSRF Token:", csrf_token)

# Try creating checkout/invoice on shopadopt
# Check if there is an inertia page props or form
m = re.search(r'data-page="([^"]+)"', res.text)
if m:
    page_data = json.loads(m.group(1).replace('&quot;', '"'))
    props = page_data.get('props', {})
    prod = props.get('product', {})
    print("Product details on supplier:", prod.get('id'), prod.get('name'), "Variants:", prod.get('variants'))
    shop = props.get('shop', {})
    print("Shop ID on supplier:", shop.get('id'))
