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

r = session.get("https://shopadopt.mysellauth.com/customer/reseller")
if r.status_code == 503:
    cookie = solve_sellauth_challenge(r.text)
    session.cookies.set("yX3", cookie, domain="shopadopt.mysellauth.com")
    session.cookies.set("yX3", cookie, domain=".mysellauth.com")
    r = session.get("https://shopadopt.mysellauth.com/customer/reseller")

print("RESELLER PAGE STATUS:", r.status_code)
print("TITLE / TEXT:", r.text[:500])
