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
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Origin": "https://shopadopt.mysellauth.com",
    "Referer": "https://shopadopt.mysellauth.com/"
}

# 1. Create Checkout
create_payload = {
    "shopId": 211743,
    "email": "dojooni0102@gmail.com",
    "cart": [{"productId": 815313, "variantId": 1397928, "quantity": 1}],
    "paymentMethod": "LTC",
    "source": "embed",
    "altcha": solve_altcha()
}

r1 = requests.post("https://api-internal-3.sellauth.com/v1/checkout", json=create_payload, headers=headers)
print("Create Status:", r1.status_code, r1.json())

unique_id = r1.json().get('url', '').split('/')[-1]

# 2. Update Checkout with Gateway
put_payload = {
    "email": "dojooni0102@gmail.com",
    "gateway": "LTC",
    "altcha": solve_altcha()
}
r2 = requests.put(f"https://api-internal-3.sellauth.com/v1/checkout/{unique_id}", json=put_payload, headers=headers)
print("PUT Status:", r2.status_code, r2.json())

# 3. Fetch Full Checkout
r3 = requests.get(f"https://api-internal-3.sellauth.com/v1/checkout/{unique_id}/full", headers=headers)
print("FULL Status:", r3.status_code)
inv = r3.json().get('invoice', {})
print("Invoice keys:", inv.keys())
print("Invoice data:", {k: inv[k] for k in ['id', 'status', 'gateway', 'price', 'crypto_address', 'crypto_amount', 'deliverables'] if k in inv})
