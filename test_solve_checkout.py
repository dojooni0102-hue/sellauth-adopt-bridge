import requests
import hashlib
import json
import base64
import time

def solve_altcha():
    """SellAuth 투명 백그라운드 Altcha PoW 챌린지 풀이기 (약 2ms 소요)"""
    t0 = time.time()
    res = requests.get("https://api-internal-3.sellauth.com/v1/altcha", timeout=5)
    if res.status_code != 200:
        return None
    
    data = res.json()
    salt = data["salt"]
    target_challenge = data["challenge"]
    max_number = data.get("maxnumber", 50000)
    
    for n in range(max_number + 1):
        test_str = f"{salt}{n}".encode('utf-8')
        if hashlib.sha256(test_str).hexdigest() == target_challenge:
            sol_payload = {
                "algorithm": data["algorithm"],
                "challenge": target_challenge,
                "number": n,
                "salt": salt,
                "signature": data["signature"]
            }
            b64_sol = base64.b64encode(json.dumps(sol_payload).encode('utf-8')).decode('utf-8')
            print(f"Altcha 풀이 완료 (소요시간: {(time.time()-t0)*1000:.2f}ms, number: {n})")
            return b64_sol
    return None

# Test checkout with solved Altcha token!
altcha_token = solve_altcha()

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
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
    "paymentMethod": "LTC",
    "source": "embed",
    "altcha": altcha_token
}

url_checkout = "https://api-internal-3.sellauth.com/v1/checkout"
r = requests.post(url_checkout, json=payload, headers=headers)
print("CHECKOUT INVOICE CREATION STATUS:", r.status_code)
print("RESPONSE:", r.json() if r.status_code in [200, 201] else r.text)
