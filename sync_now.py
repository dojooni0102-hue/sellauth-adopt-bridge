import requests
import hashlib
import re

supplier_session = requests.Session()
supplier_session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36'})

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

headers = {'Authorization': 'Bearer 6041435|EbpGObFUfemI3XElDjR99Y6EQc9rwFkoU1WGQF1L7ee51812', 'Content-Type': 'application/json'}
products = [
    ('835796', '1443082', '326-350-potions-249k-273l-bucks'),
    ('835800', '1443091', '826-850-potions-473k-568k-bucks'),
    ('835802', '1443093', '1276-1300-potions-759k-869k-bucks'),
]

for prod_id, var_id, slug in products:
    url = f'https://shopadopt.mysellauth.com/product/{slug}'
    res = supplier_session.get(url)
    if res.status_code == 503:
        cookie = solve_sellauth_challenge(res.text)
        supplier_session.cookies.set('yX3', cookie, domain='shopadopt.mysellauth.com')
        supplier_session.cookies.set('yX3', cookie, domain='.mysellauth.com')
        res = supplier_session.get(url)
    stocks = re.findall(r'"stock":\s*(\d+)', res.text)
    stock_count = int(stocks[0]) if stocks else 0
    r = requests.put(f'https://api.sellauth.com/v1/shops/261184/products/{prod_id}/stock/{var_id}', json={'stock': stock_count}, headers=headers)
    print(f'Synced {slug} -> REAL STOCK: {stock_count} (SellAuth status: {r.status_code})')
