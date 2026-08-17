import requests
import hashlib
import json
import base64

def solve_altcha():
    res = requests.get('https://api-internal-3.sellauth.com/v1/altcha', timeout=5).json()
    salt = res['salt']
    target = res['challenge']
    for n in range(res.get('maxnumber', 50000) + 1):
        if hashlib.sha256(f'{salt}{n}'.encode('utf-8')).hexdigest() == target:
            p = {'algorithm': res['algorithm'], 'challenge': target, 'number': n, 'salt': salt, 'signature': res['signature']}
            return base64.b64encode(json.dumps(p).encode('utf-8')).decode('utf-8')

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json",
    "Origin": "https://shopadopt.mysellauth.com",
    "Referer": "https://shopadopt.mysellauth.com/"
}

# Try passing paymentMethodId: 147367
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
    "paymentMethodId": 147367,
    "source": "embed",
    "altcha": solve_altcha()
}

r = requests.post("https://api-internal-3.sellauth.com/v1/checkout", json=payload, headers=headers)
print("CREATE STATUS:", r.status_code, r.json())

inv_id = r.json().get('url', '').split('/')[-1]
r_full = requests.get(f"https://api-internal-3.sellauth.com/v1/checkout/{inv_id}/full", headers=headers)
inv = r_full.json().get('invoice', {})
print("LTC ADDRESS:", inv.get('crypto_address'))
print("LTC AMOUNT:", inv.get('crypto_amount'))
print("PRICE USD:", inv.get('price'))
