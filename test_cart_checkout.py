import requests
import json

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Origin": "https://shopadopt.mysellauth.com",
    "Referer": "https://shopadopt.mysellauth.com/"
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

url = "https://api-internal-3.sellauth.com/v1/checkout"
r = requests.post(url, json=payload, headers=headers)
print("CHECKOUT RESPONSE:", r.status_code, r.text)
