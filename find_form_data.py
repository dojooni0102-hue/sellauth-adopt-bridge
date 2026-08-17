with open("checkout_bundle.js", "r", encoding="utf-8") as f:
    js = f.read()

pos = js.find('handleSubmit(Re)')
if pos != -1:
    print("HANDLE SUBMIT RE CONTEXT:")
    print(js[max(0, pos-800):pos+400].encode('ascii', 'ignore').decode('ascii'))
