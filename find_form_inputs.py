with open("checkout_bundle.js", "r", encoding="utf-8") as f:
    js = f.read()

pos = js.find('form', js.find('handleSubmit(Re)'))
if pos != -1:
    print("FORM INPUTS:")
    print(js[pos:pos+2000].encode('ascii', 'ignore').decode('ascii'))
