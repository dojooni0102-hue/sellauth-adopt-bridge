import hashlib
import ecdsa
import base58
import os
import requests
import struct
import logging

logger = logging.getLogger("LTCWallet")

def generate_ltc_wallet():
    """새로운 라이트코인(LTC) 지갑 주소 및 개인키 생성"""
    private_key_bytes = os.urandom(32)
    extended_key = b'\xb0' + private_key_bytes + b'\x01'
    checksum = hashlib.sha256(hashlib.sha256(extended_key).digest()).digest()[:4]
    wif_key = base58.b58encode(extended_key + checksum).decode('utf-8')
    
    sk = ecdsa.SigningKey.from_string(private_key_bytes, curve=ecdsa.SECP256k1)
    vk = sk.verifying_key
    
    public_key_bytes = vk.to_string()
    x = public_key_bytes[:32]
    y = public_key_bytes[32:]
    prefix = b'\x02' if int.from_bytes(y, 'big') % 2 == 0 else b'\x03'
    compressed_pubkey = prefix + x
    
    sha_hash = hashlib.sha256(compressed_pubkey).digest()
    ripemd_hash = hashlib.new('ripemd160', sha_hash).digest()
    
    network_byte = b'\x30'
    extended_ripemd = network_byte + ripemd_hash
    addr_checksum = hashlib.sha256(hashlib.sha256(extended_ripemd).digest()).digest()[:4]
    address = base58.b58encode(extended_ripemd + addr_checksum).decode('utf-8')
    
    return {
        "address": address,
        "private_key_wif": wif_key,
        "private_key_hex": private_key_bytes.hex(),
        "compressed_pubkey_hex": compressed_pubkey.hex()
    }

def get_ltc_balance(address: str) -> float:
    """LitecoinSpace 공개 API로 실시간 잔액 조회 (LTC 단위)"""
    try:
        url = f"https://litecoinspace.org/api/address/{address}"
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            data = res.json()
            funded = data.get("chain_stats", {}).get("funded_txo_sum", 0)
            spent = data.get("chain_stats", {}).get("spent_txo_sum", 0)
            balance_satoshis = funded - spent
            return balance_satoshis / 100_000_000.0
    except Exception:
        pass
    return 0.0

def send_ltc_payment(sender_priv_hex: str = "", sender_pub_hex: str = "", sender_address: str = "", recipient_address: str = "", amount_ltc: float = 0.0, **kwargs) -> dict:
    """
    실제 블록체인 네트워크로 raw transaction을 서명하고 브로드캐스트하는 온체인 전송 엔진
    """
    try:
        priv_key = sender_priv_hex or kwargs.get('sender_priv_hex_or_wif') or kwargs.get('private_key') or ""
        # 1. WIF 또는 Hex에서 개인키 바이트 및 공개키 추출
        if priv_key.startswith('T'):
            decoded_wif = base58.b58decode_check(priv_key)
            private_key_bytes = decoded_wif[1:33]
        else:
            private_key_bytes = bytes.fromhex(priv_key)
            
        sk = ecdsa.SigningKey.from_string(private_key_bytes, curve=ecdsa.SECP256k1)
        vk = sk.verifying_key
        pubkey_bytes = vk.to_string()
        x = pubkey_bytes[:32]
        y = pubkey_bytes[32:]
        prefix = b'\x02' if int.from_bytes(y, 'big') % 2 == 0 else b'\x03'
        compressed_pubkey = prefix + x

        # 2. UTXO 조회
        utxo_res = requests.get(f"https://litecoinspace.org/api/address/{sender_address}/utxo", timeout=10)
        if utxo_res.status_code != 200 or not utxo_res.json():
            return {"success": False, "error": "지갑에 사용 가능한 UTXO(잔액)가 없습니다."}
        
        utxos = utxo_res.json()
        target_satoshis = int(round(amount_ltc * 100_000_000))
        fee_satoshis = 2000 # 0.00002 LTC (약 1.2원)
        
        # UTXO 선택
        total_input = 0
        selected_utxos = []
        for u in utxos:
            total_input += u["value"]
            selected_utxos.append(u)
            if total_input >= (target_satoshis + fee_satoshis):
                break
                
        if total_input < (target_satoshis + fee_satoshis):
            return {"success": False, "error": f"잔액 부족: 필요 {target_satoshis + fee_satoshis} sats / 보유 {total_input} sats"}

        change_satoshis = total_input - target_satoshis - fee_satoshis

        # 3. 대상 주소 ScriptPubKey 생성 (P2PKH 'L', P2SH 'M'/'3', 또는 P2WPKH 'ltc1')
        if recipient_address.startswith('ltc1'):
            import bech32
            hrp, data = bech32.bech32_decode(recipient_address)
            decoded = bech32.convertbits(data[1:], 5, 8, False)
            target_script_pubkey = bytes([0x00, len(decoded)]) + bytes(decoded)
        elif recipient_address.startswith('M') or recipient_address.startswith('3'):
            decoded_target = base58.b58decode_check(recipient_address)
            target_pkh = decoded_target[1:]
            target_script_pubkey = b'\xa9\x14' + target_pkh + b'\x87'
        else:
            decoded_target = base58.b58decode_check(recipient_address)
            target_pkh = decoded_target[1:]
            target_script_pubkey = b'\x76\xa9\x14' + target_pkh + b'\x88\xac'

        # 내 지갑 ScriptPubKey (잔돈 반환용)
        decoded_my = base58.b58decode_check(sender_address)
        my_pkh = decoded_my[1:]
        my_script_pubkey = b'\x76\xa9\x14' + my_pkh + b'\x88\xac'

        # 4. 트랜잭션 구성 (1 Input, 1 or 2 Outputs)
        version = struct.pack("<I", 1)
        in_count = bytes([len(selected_utxos)])
        
        # Outputs
        outputs_bytes = b''
        out_count_num = 1
        # Output 1: 송금 대상
        outputs_bytes += struct.pack("<Q", target_satoshis)
        outputs_bytes += bytes([len(target_script_pubkey)]) + target_script_pubkey
        
        # Output 2: 잔돈 (있는 경우)
        if change_satoshis > 500:
            out_count_num += 1
            outputs_bytes += struct.pack("<Q", change_satoshis)
            outputs_bytes += bytes([len(my_script_pubkey)]) + my_script_pubkey
            
        out_count = bytes([out_count_num])
        locktime = struct.pack("<I", 0)

        # 서명 생성
        u = selected_utxos[0]
        prev_txid = bytes.fromhex(u["txid"])[::-1]
        prev_vout = struct.pack("<I", u["vout"])
        sequence = struct.pack("<I", 0xffffffff)
        
        sig_script_placeholder = bytes([len(my_script_pubkey)]) + my_script_pubkey
        raw_tx_to_sign = (
            version +
            in_count +
            prev_txid + prev_vout + sig_script_placeholder + sequence +
            out_count +
            outputs_bytes +
            locktime +
            struct.pack("<I", 1) # SIGHASH_ALL
        )

        tx_hash = hashlib.sha256(hashlib.sha256(raw_tx_to_sign).digest()).digest()
        sig_der = sk.sign_digest(tx_hash, sigencode=ecdsa.util.sigencode_der_canonize) + b'\x01'
        
        script_sig = (
            bytes([len(sig_der)]) + sig_der +
            bytes([len(compressed_pubkey)]) + compressed_pubkey
        )
        script_sig_len = bytes([len(script_sig)])

        final_raw_tx = (
            version +
            in_count +
            prev_txid + prev_vout + script_sig_len + script_sig + sequence +
            out_count +
            outputs_bytes +
            locktime
        )

        # 5. 블록체인 브로드캐스트
        broadcast_res = requests.post("https://litecoinspace.org/api/tx", data=final_raw_tx.hex(), timeout=10)
        if broadcast_res.status_code == 200:
            txid = broadcast_res.text.strip()
            logger.info(f"온체인 브로드캐스트 성공! TXID: {txid}")
            return {"success": True, "txid": txid, "amount": amount_ltc, "recipient": recipient_address}
        else:
            logger.error(f"브로드캐스트 실패: {broadcast_res.status_code} {broadcast_res.text}")
            return {"success": False, "error": f"브로드캐스트 실패: {broadcast_res.text}"}
    except Exception as e:
        logger.error(f"온체인 전송 예외: {e}")
        return {"success": False, "error": str(e)}
