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

url = "https://shopadopt.mysellauth.com/product/326-350-potions-249k-273l-bucks"
r = session.get(url)
print("Challenge status:", r.status_code)

cookie_val = solve_sellauth_challenge(r.text)
print("Solved cookie:", cookie_val)

if cookie_val:
    session.cookies.set("yX3", cookie_val, domain="shopadopt.mysellauth.com")
    session.cookies.set("yX3", cookie_val, domain=".mysellauth.com")
    res = session.get(url)
    print("Page status:", res.status_code, "Length:", len(res.text))
    # Look for stock count or inertia / json data in the page
    with open("supplier_page.html", "w", encoding="utf-8") as f:
        f.write(res.text)
    
    # Search for stock in page
    stocks = re.findall(r'stock["\']?\s*[:=]\s*(\d+)', res.text, re.IGNORECASE)
    print("Found stock matches:", stocks)
