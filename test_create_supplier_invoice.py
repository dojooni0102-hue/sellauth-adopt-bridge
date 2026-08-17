import requests
import json

# Supplier shop ID is 211743, product ID is 815313
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

# Test public invoice creation endpoints
endpoints = [
    "https://api.sellauth.com/v1/shops/211743/checkout",
    "https://api.sellauth.com/v1/shops/211743/invoices",
    "https://api-internal-3.sellauth.com/v1/shops/211743/invoices",
    "https://api-internal-3.sellauth.com/v1/checkout",
    "https://shopadopt.mysellauth.com/checkout",
]

payload = {
    "product_id": 815313,
    "quantity": 1,
    "email": "dojooni0102@gmail.com",
    "gateway": "LTC"
}

for url in endpoints:
    try:
        r = requests.post(url, json=payload, headers=headers, timeout=5)
        print(url, "->", r.status_code, r.text[:200])
    except Exception as e:
        print(url, "-> ERROR:", e)
