import re
import requests

with open("supplier_page.html", "r", encoding="utf-8") as f:
    html = f.read()

# Find external app JS scripts
js_urls = re.findall(r'src=[\'\"](https://[^\'\"]+\.js[^\'\"]*)[\'\"]', html)
print("JS URLs:", js_urls)

for url in js_urls:
    if "app" in url or "checkout" in url or "bundle" in url:
        print("Fetching script:", url)
        r = requests.get(url)
        # Search for checkout endpoint or captcha in JS
        matches = re.findall(r'(\w*captcha\w*|\w*turnstile\w*)', r.text, re.IGNORECASE)
        print("Captcha occurrences in", url, ":", set(matches))
        # Search for checkout payload fields
        pos = r.text.find("/checkout")
        if pos != -1:
            print("Found /checkout context:")
            print(r.text[max(0, pos-200):pos+300])
