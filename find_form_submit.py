with open("checkout_bundle.js", "r", encoding="utf-8") as f:
    js = f.read()

import re

pos = js.find('payment_methods.find')
if pos != -1:
    print("PAYMENT METHOD CONTEXT:")
    print(js[max(0, pos-200):pos+600].encode('ascii', 'ignore').decode('ascii'))
