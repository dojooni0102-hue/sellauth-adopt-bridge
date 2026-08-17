with open("checkout_bundle.js", "r", encoding="utf-8") as f:
    js = f.read()

pos = js.find('payment_methods.find')
if pos != -1:
    print("EXTENDED CONTEXT:")
    print(js[pos:pos+2000].encode('ascii', 'ignore').decode('ascii'))
