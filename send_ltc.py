import requests
import hashlib
import ecdsa
import base58
import struct

# 봇 지갑 정보
BOT_ADDRESS = "LfZY83v3AX2GH4S9hd4qKLhTmbHHzJTp7e"
BOT_WIF = "TAt1SoUi2mep6G4EUtR2uztRMiAjH3PMQL8qqj1vbrD8iLnGgthi"
TARGET_ADDRESS = "LKs5txBUcvxE8TPi2FtMp7cJzKEbiF4WCr"

# 1. WIF에서 개인키 바이트 추출
decoded_wif = base58.b58decode_check(BOT_WIF)
# 접두사 1바이트(0xb0)와 압축 플래그 1바이트(0x01) 제거
private_key_bytes = decoded_wif[1:33]
sk = ecdsa.SigningKey.from_string(private_key_bytes, curve=ecdsa.SECP256k1)
vk = sk.verifying_key

# 압축 공개키 생성
pubkey_bytes = vk.to_string()
x = pubkey_bytes[:32]
y = pubkey_bytes[32:]
prefix = b'\x02' if int.from_bytes(y, 'big') % 2 == 0 else b'\x03'
compressed_pubkey = prefix + x

# 2. UTXO 조회
utxo_res = requests.get(f"https://litecoinspace.org/api/address/{BOT_ADDRESS}/utxo")
utxos = utxo_res.json()
print("조회된 UTXO:", utxos)

if not utxos:
    print("사용 가능한 잔액이 없습니다.")
    exit(1)

utxo = utxos[0]
txid_hex = utxo["txid"]
vout = utxo["vout"]
input_value = utxo["value"] # 1816530 satoshis

# 수수료 및 전송 금액 계산
fee_satoshis = 2000 # 0.00002 LTC (약 1.2원)
send_amount_satoshis = input_value - fee_satoshis
print(f"총 잔액: {input_value} sats -> 전송액: {send_amount_satoshis} sats ({send_amount_satoshis / 1e8} LTC), 수수료: {fee_satoshis} sats")

# 3. 대상 주소의 PubKeyHash 추출
decoded_target = base58.b58decode_check(TARGET_ADDRESS)
target_pkh = decoded_target[1:] # 20바이트 해시
target_script_pubkey = b'\x76\xa9\x14' + target_pkh + b'\x88\xac' # OP_DUP OP_HASH160 <pkh> OP_EQUALVERIFY OP_CHECKSIG

# 내 주소의 PubKeyHash
decoded_my = base58.b58decode_check(BOT_ADDRESS)
my_pkh = decoded_my[1:]
my_script_pubkey = b'\x76\xa9\x14' + my_pkh + b'\x88\xac'

# 4. 트랜잭션 구성 및 서명 해시 (SIGHASH_ALL = 0x01)
# TX 버전: 1 (4 bytes little-endian)
version = struct.pack("<I", 1)
# Input 수: 1 (1 byte)
in_count = b'\x01'
# Prev TXID (32 bytes little-endian)
prev_txid = bytes.fromhex(txid_hex)[::-1]
# Prev VOUT (4 bytes little-endian)
prev_vout = struct.pack("<I", vout)
# Sequence: 0xffffffff
sequence = struct.pack("<I", 0xffffffff)

# Output 수: 1 (1 byte)
out_count = b'\x01'
# Output Value (8 bytes little-endian)
out_value = struct.pack("<Q", send_amount_satoshis)
# Output Script Length (1 byte) + Script
out_script = bytes([len(target_script_pubkey)]) + target_script_pubkey
# Locktime: 0 (4 bytes)
locktime = struct.pack("<I", 0)

# 서명용 Raw TX (Input Script에 my_script_pubkey 삽입)
sig_script_placeholder = bytes([len(my_script_pubkey)]) + my_script_pubkey
raw_tx_to_sign = (
    version +
    in_count +
    prev_txid + prev_vout + sig_script_placeholder + sequence +
    out_count +
    out_value + out_script +
    locktime +
    struct.pack("<I", 1) # SIGHASH_ALL
)

# 더블 SHA256 해시
tx_hash = hashlib.sha256(hashlib.sha256(raw_tx_to_sign).digest()).digest()

# ECDSA DER 서명 생성
sig_der = sk.sign_digest(tx_hash, sigencode=ecdsa.util.sigencode_der_canonize) + b'\x01' # SIGHASH_ALL byte appended

# 최종 ScriptSig (서명 + 압축 공개키)
script_sig = (
    bytes([len(sig_der)]) + sig_der +
    bytes([len(compressed_pubkey)]) + compressed_pubkey
)
script_sig_len = bytes([len(script_sig)])

# 최종 전송용 Raw Transaction Hex
final_raw_tx = (
    version +
    in_count +
    prev_txid + prev_vout + script_sig_len + script_sig + sequence +
    out_count +
    out_value + out_script +
    locktime
)

raw_hex = final_raw_tx.hex()
print("생성된 최종 트랜잭션 HEX (길이: %d):" % len(raw_hex))

# 5. 블록체인 네트워크에 브로드캐스트 (LitecoinSpace API)
broadcast_res = requests.post("https://litecoinspace.org/api/tx", data=raw_hex)
print("브로드캐스트 상태 코드:", broadcast_res.status_code)
print("브로드캐스트 응답 (TXID):", broadcast_res.text)
