from curl_cffi import requests
import hashlib
import re

session = requests.Session(impersonate="chrome120")

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

r = session.get("https://shopadopt.mysellauth.com")
if r.status_code == 503:
    cookie = solve_sellauth_challenge(r.text)
    session.cookies.set("yX3", cookie, domain="shopadopt.mysellauth.com")
    session.cookies.set("yX3", cookie, domain=".mysellauth.com")

# Get React checkout bundle
r_js = session.get("https://shopadopt.mysellauth.com/checkout/assets/index-NYBAgCpW.js")
print("JS bundle status:", r_js.status_code, "Length:", len(r_js.text))

with open("checkout_bundle.js", "w", encoding="utf-8") as f:
    f.write(r_js.text)

# Search for turnstile / sitekey / captcha in the JS bundle
for m in re.finditer(r'turnstile|sitekey|captcha|cf-turnstile|0x4AAAAAA[0-9a-zA-Z]+', r_js.text, re.IGNORECASE):
    pos = m.start()
    print("MATCH at", pos, ":", r_js.text[max(0, pos-100):pos+150])
