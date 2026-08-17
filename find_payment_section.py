with open("checkout_bundle.js", "r", encoding="utf-8") as f:
    js = f.read()

pos = js.find('sectionPaymentMethod')
if pos != -1:
    print("SECTION PAYMENT METHOD:")
    print(js[max(0, pos-200):pos+800].encode('ascii', 'ignore').decode('ascii'))
