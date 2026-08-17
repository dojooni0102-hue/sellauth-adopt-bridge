from curl_cffi import requests
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
        digest = hashlib.sha1((c + str(i)).encode('utf-8')).digest()
        if digest[n1] == 0xb0 and digest[n1+1] == 0x0b:
            return f"{c}{i}"
        i += 1
    return None

session = requests.Session(impersonate="chrome120")

# 1. Warm up session and solve SellAuth PoW
url_prod = "https://shopadopt.mysellauth.com/product/326-350-potions-249k-273l-bucks"
res = session.get(url_prod)
print("Initial page status:", res.status_code)

if res.status_code == 503:
    cookie_val = solve_sellauth_challenge(res.text)
    print("Solved PoW Cookie:", cookie_val)
    if cookie_val:
        session.cookies.set("yX3", cookie_val, domain="shopadopt.mysellauth.com")
        session.cookies.set("yX3", cookie_val, domain=".mysellauth.com")
        session.cookies.set("yX3", cookie_val, domain=".sellauth.com")
        res = session.get(url_prod)
        print("Page status after PoW solve:", res.status_code)

# 2. Try checkout with solved PoW session
headers = {
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json",
    "Origin": "https://shopadopt.mysellauth.com",
    "Referer": "https://shopadopt.mysellauth.com/",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site"
}

payload = {
    "shopId": 211743,
    "email": "dojooni0102@gmail.com",
    "cart": [
        {
            "productId": 815313,
            "variantId": 1397928,
            "quantity": 1
        }
    ],
    "paymentMethod": "LTC"
}

url_checkout = "https://api-internal-3.sellauth.com/v1/checkout"
r = session.post(url_checkout, json=payload, headers=headers)
print("CURL_CFFI CHECKOUT STATUS:", r.status_code)
print("RESPONSE:", r.text[:500])
