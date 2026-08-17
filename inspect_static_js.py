import requests
import re

url = "https://static.mysellauth.com/assets/220375/script.js?v=1776589350000"
r = requests.get(url)
print("Script size:", len(r.text))

# Search for checkout / captcha
matches = re.finditer(r'checkout|captcha|turnstile', r.text, re.IGNORECASE)
for m in matches:
    pos = m.start()
    print("MATCH at", pos, ":", r.text[max(0, pos-100):pos+150])
    print("-" * 50)
