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
inv_url = r1.json().get('url', '')
unique_id = inv_url.split('/')[-1]
print("Created unique_id:", unique_id)

# 2. Select Payment Method 147367 (LTC)
put_payload = {
    "payment_method_id": 147367,
    "email": "dojooni0102@gmail.com",
    "altcha": solve_altcha()
}
r2 = requests.put(f"https://api-internal-3.sellauth.com/v1/checkout/{unique_id}", json=put_payload, headers=headers)
print("PUT response:", r2.status_code, r2.json())

# 3. Check Invoice Full
r3 = requests.get(f"https://api-internal-3.sellauth.com/v1/checkout/{unique_id}/full", headers=headers)
inv = r3.json().get('invoice', {})
print("Invoice status:", inv.get('status'))
print("Gateway:", inv.get('gateway'))
print("Crypto Address:", inv.get('crypto_address'))
print("Crypto Amount:", inv.get('crypto_amount'))
print("Price USD:", inv.get('price_usd'))
