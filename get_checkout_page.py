from curl_cffi import requests
import hashlib
import re

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

# 1. Solve challenge on shopadopt
r = session.get("https://shopadopt.mysellauth.com")
if r.status_code == 503:
    cookie = solve_sellauth_challenge(r.text)
    session.cookies.set("yX3", cookie, domain="shopadopt.mysellauth.com")
    session.cookies.set("yX3", cookie, domain=".mysellauth.com")

# 2. Get checkout page
r_checkout = session.get("https://shopadopt.mysellauth.com/checkout")
print("Checkout page status:", r_checkout.status_code, "Length:", len(r_checkout.text))

with open("checkout_page.html", "w", encoding="utf-8") as f:
    f.write(r_checkout.text)

# Search for turnstile or captcha in checkout_page.html
print("Turnstile matches in checkout page:", re.findall(r'turnstile|sitekey|captcha|cf-', r_checkout.text, re.IGNORECASE))
