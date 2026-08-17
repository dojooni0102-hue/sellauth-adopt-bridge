import requests

headers = {'User-Agent': 'Mozilla/5.0'}
r = requests.get('https://api-internal-3.sellauth.com/v1/checkout/353c678361e10-0000014993784/full', headers=headers)
data = r.json()
inv = data.get('invoice', {})
items = inv.get('items', [])

for item in items:
    item_id = item.get('id')
    print("ITEM ID:", item_id)
    r_deliv = requests.get(f'https://api-internal-3.sellauth.com/v1/checkout/353c678361e10-0000014993784/{item_id}/deliverables', headers=headers)
    print("DELIVERABLES STATUS:", r_deliv.status_code)
    print("DELIVERABLES TEXT:")
    print(r_deliv.text)
