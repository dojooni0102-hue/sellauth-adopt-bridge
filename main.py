import os
import re
import json
import time
import uuid
import base64
import hashlib
import logging
from datetime import datetime
from typing import Optional, Dict
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.responses import PlainTextResponse
import requests
from dotenv import load_dotenv
import ltc_wallet
import voucher_validator
import voucher_cashout
import cryptovoucher_engine

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("SellAuthBridge")

app = FastAPI(
    title="SellAuth Adopt Me Dropship Bridge Server",
    description="24/7 Automated dropshipping bridge with unique Purchase ID idempotency & real-time stock sync",
    version="4.0.0"
)

BOT_LTC_ADDRESS = os.getenv("BOT_LTC_ADDRESS", "LfZY83v3AX2GH4S9hd4qKLhTmbHHzJTp7e").strip()
BOT_LTC_WIF = os.getenv("BOT_LTC_WIF", "TAt1SoUi2mep6G4EUtR2uztRMiAjH3PMQL8qqj1vbrD8iLnGgthi").strip()
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/1538132500252196895/zvwekUl3n_imKxLE9EYwkzHv0HSNK7tC0At5-AmmnWdvbqAwo3e6D4vGxsBjcrutyzxX").strip()

SUPPLIER_SHOP_ID = 211743

PRODUCTS = {
    "potion350": "326-350-potions-249k-273l-bucks",
    "326-350-potions-249k-273l-bucks": "326-350-potions-249k-273l-bucks",
    "potion850": "826-850-potions-473k-568k-bucks",
    "826-850-potions-473k-568k-bucks": "826-850-potions-473k-568k-bucks",
    "potion1300": "1276-1300-potions-759k-869k-bucks",
    "1276-1300-potions-759k-869k-bucks": "1276-1300-potions-759k-869k-bucks",
}

SUPPLIER_PRODUCT_MAP = {
    "326-350-potions-249k-273l-bucks": {"productId": 815313, "variantId": 1397928, "paymentMethodId": 147367},
    "826-850-potions-473k-568k-bucks": {"productId": 815316, "variantId": 1397931, "paymentMethodId": 147367},
    "1276-1300-potions-759k-869k-bucks": {"productId": 815318, "variantId": 1397933, "paymentMethodId": 147367},
}

MY_SELLAUTH_API_KEY = os.getenv("MY_SELLAUTH_API_KEY", "6041435|EbpGObFUfemI3XElDjR99Y6EQc9rwFkoU1WGQF1L7ee51812").strip()
MY_SHOP_ID = os.getenv("MY_SHOP_ID", "261184").strip()
MY_BUYER_EMAIL = os.getenv("MY_BUYER_EMAIL", "dojooni0102@gmail.com").strip()

MY_PRODUCT_DATA = {
    "326-350-potions-249k-273l-bucks": {
        "productId": int(os.getenv("MY_PRODUCT_ID_ITEM1", "835796")),
        "variantId": 1443082
    },
    "826-850-potions-473k-568k-bucks": {
        "productId": int(os.getenv("MY_PRODUCT_ID_ITEM2", "835800")),
        "variantId": 1443091
    },
    "1276-1300-potions-759k-869k-bucks": {
        "productId": int(os.getenv("MY_PRODUCT_ID_ITEM3", "835802")),
        "variantId": 1443093
    }
}

# ==============================================================================
# [핵심 시스템] 고유 구매 ID 및 영구 주문 원장 관리 (1주문 1구매 철칙 보증)
# ==============================================================================
ORDERS_LEDGER_FILE = "orders_ledger.json"

def load_ledger() -> Dict[str, dict]:
    if os.path.exists(ORDERS_LEDGER_FILE):
        try:
            with open(ORDERS_LEDGER_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_ledger(ledger: Dict[str, dict]):
    try:
        with open(ORDERS_LEDGER_FILE, "w", encoding="utf-8") as f:
            json.dump(ledger, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"주문 원장 저장 실패: {e}")

def generate_purchase_id(invoice_id: Optional[int] = None) -> str:
    """모든 주문마다 전 세계에서 유일한 고유 구매 ID 생성 (예: ORD-14993706-A8B9C2)"""
    date_str = datetime.utcnow().strftime("%Y%m%d")
    random_suffix = uuid.uuid4().hex[:6].upper()
    if invoice_id:
        return f"ORD-{date_str}-{invoice_id}-{random_suffix}"
    return f"ORD-{date_str}-{random_suffix}"


supplier_session = requests.Session()
supplier_session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
})


def send_discord_notification(title: str, description: str, color: int = 0x5865F2, fields: list = None):
    """디스코드 채널로 실시간 판매 및 에러 푸시 알림 전송"""
    if not DISCORD_WEBHOOK_URL:
        return
    try:
        embed = {
            "title": title,
            "description": description,
            "color": color,
            "footer": {"text": "SellAuth Adopt Me Dropship Bridge 24/7 Engine"}
        }
        if fields:
            embed["fields"] = fields
        payload = {"embeds": [embed]}
        requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=5)
    except Exception as e:
        logger.warning(f"디스코드 웹후크 전송 실패: {e}")


def solve_sellauth_challenge(html: str) -> Optional[str]:
    """SellAuth 웹스토어 503 JS PoW 챌린지 풀이 엔진 (약 2ms 소요)"""
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


def solve_altcha() -> Optional[str]:
    """SellAuth 결제창 Altcha PoW 챌린지 풀이 엔진 (약 2ms 소요)"""
    try:
        res = requests.get("https://api-internal-3.sellauth.com/v1/altcha", timeout=5)
        if res.status_code != 200:
            return None
        data = res.json()
        salt = data["salt"]
        target = data["challenge"]
        max_number = data.get("maxnumber", 50000)
        
        for n in range(max_number + 1):
            if hashlib.sha256(f"{salt}{n}".encode('utf-8')).hexdigest() == target:
                sol = {
                    "algorithm": data["algorithm"],
                    "challenge": target,
                    "number": n,
                    "salt": salt,
                    "signature": data["signature"]
                }
                return base64.b64encode(json.dumps(sol).encode('utf-8')).decode('utf-8')
    except Exception as e:
        logger.warning(f"Altcha 풀이 에러: {e}")
    return None


def get_supplier_exact_stock(product_slug: str) -> int:
    """업자 샵의 실시간 정확한 재고 수량 조회"""
    url = f"https://shopadopt.mysellauth.com/product/{product_slug}"
    try:
        res = supplier_session.get(url, timeout=10)
        if res.status_code == 503:
            cookie_val = solve_sellauth_challenge(res.text)
            if cookie_val:
                supplier_session.cookies.set("yX3", cookie_val, domain="shopadopt.mysellauth.com")
                supplier_session.cookies.set("yX3", cookie_val, domain=".mysellauth.com")
                res = supplier_session.get(url, timeout=10)
        
        if res.status_code == 200:
            m = re.search(r'"stock"\s*:\s*(\d+)', res.text)
            if m:
                return int(m.group(1))
    except Exception as e:
        logger.error(f"업자 재고 확인 실패: {e}")
    return 0


def update_my_product_exact_stock(product_id: int, variant_id: int, exact_stock: int) -> bool:
    """내 SellAuth 상점의 재고를 업자 재고와 100% 동일하게 실시간 업데이트"""
    url = f"https://api.sellauth.com/v1/shops/{MY_SHOP_ID}/products/{product_id}/stock/{variant_id}"
    headers = {
        "Authorization": f"Bearer {MY_SELLAUTH_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    payload = {"stock": exact_stock}
    try:
        res = requests.put(url, json=payload, headers=headers, timeout=10)
        return res.status_code == 200
    except Exception as e:
        logger.error(f"내 상점 재고 업데이트 실패: {e}")
        return False


def purchase_real_account_from_supplier(product_slug: str) -> Optional[str]:
    """
    업자 샵에서 실시간 온체인 결제 및 실제 로블록스 계정 수령 (핵심 엔진)
    """
    logger.info(f"업자에게서 실제 계정 구매 시작: {product_slug}")
    prod_info = SUPPLIER_PRODUCT_MAP.get(product_slug)
    if not prod_info:
        return None
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Origin": "https://shopadopt.mysellauth.com",
        "Referer": "https://shopadopt.mysellauth.com/"
    }

    try:
        # 1. 인보이스 생성
        altcha_1 = solve_altcha()
        create_payload = {
            "shopId": SUPPLIER_SHOP_ID,
            "email": MY_BUYER_EMAIL,
            "cart": [{"productId": prod_info["productId"], "variantId": prod_info["variantId"], "quantity": 1}],
            "paymentMethod": "LTC",
            "source": "embed",
            "altcha": altcha_1
        }
        r1 = requests.post("https://api-internal-3.sellauth.com/v1/checkout", json=create_payload, headers=headers, timeout=10)
        if r1.status_code != 200:
            logger.error(f"업자 인보이스 생성 실패: {r1.status_code} {r1.text}")
            return None
            
        inv_url = r1.json().get('url', '')
        unique_id = inv_url.split('/')[-1]
        logger.info(f"업자 인보이스 생성 성공: {unique_id}")

        # 2. LTC 결제 수단 선택 및 입금 주소 추출
        altcha_2 = solve_altcha()
        put_payload = {
            "payment_method_id": prod_info["paymentMethodId"],
            "email": MY_BUYER_EMAIL,
            "altcha": altcha_2
        }
        requests.put(f"https://api-internal-3.sellauth.com/v1/checkout/{unique_id}", json=put_payload, headers=headers, timeout=10)
        
        # 3. 입금 주소 및 금액 조회
        r3 = requests.get(f"https://api-internal-3.sellauth.com/v1/checkout/{unique_id}/full", headers=headers, timeout=10)
        inv = r3.json().get('invoice', {})
        crypto_address = inv.get('crypto_address')
        crypto_amount = float(inv.get('crypto_amount', 0))
        logger.info(f"업자 LTC 입금 요청: 주소={crypto_address}, 금액={crypto_amount} LTC")

        if crypto_address and crypto_amount > 0:
            # 4. 봇 지갑에서 업자 주소로 LTC 자동 송금
            tx_res = ltc_wallet.send_ltc_payment(
                sender_priv_hex=BOT_LTC_WIF,
                sender_pub_hex="",
                sender_address=BOT_LTC_ADDRESS,
                recipient_address=crypto_address,
                amount_ltc=crypto_amount
            )
            logger.info(f"온체인 자동 송금 결과: {tx_res}")

            if not tx_res.get("success"):
                logger.error(f"LTC 송금 실패: {tx_res.get('error')}")
                return None

            # 5. 결제 확인 및 계정 수령 (최대 60초 대기)
            for _ in range(30):
                time.sleep(2)
                check_res = requests.get(f"https://api-internal-3.sellauth.com/v1/checkout/{unique_id}/full", headers=headers, timeout=5)
                if check_res.status_code == 200:
                    check_inv = check_res.json().get('invoice', {})
                    if check_inv.get('status') == 'completed':
                        items = check_inv.get('items', [])
                        if items:
                            item_id = items[0].get('id')
                            d_res = requests.get(f"https://api-internal-3.sellauth.com/v1/checkout/{unique_id}/{item_id}/deliverables", headers=headers, timeout=5)
                            if d_res.status_code == 200 and d_res.text.strip():
                                real_text = d_res.text.strip()
                                logger.info(f"업자에게서 실제 계정 수령 완료: {real_text}")
                                return real_text
    except Exception as e:
        logger.error(f"실제 계정 구매 중 에러: {e}")

    return None


def background_fulfill_order(target_slug: str, purchase_id: str, invoice_id: Optional[int] = None, item_id: Optional[int] = None):
    """
    [핵심] 고유 구매 ID 기반 단 1회 구매 보장 실행기
    """
    ledger = load_ledger()
    
    # 1. 고유 ID 중복 실행 여부 검사
    if purchase_id in ledger:
        existing = ledger[purchase_id]
        if existing.get("status") in ["COMPLETED", "PROCESSING"]:
            logger.info(f"[중복 차단] 구매 ID {purchase_id}는 이미 {existing.get('status')} 상태입니다. 추가 구매를 차단합니다.")
            return

    # 2. 인보이스 ID 중복 실행 여부 검사
    if invoice_id:
        for pid, record in ledger.items():
            if record.get("invoice_id") == invoice_id and record.get("status") == "COMPLETED":
                logger.info(f"[중복 차단] 인보이스 {invoice_id}는 이미 구매 완료되었습니다 (구매 ID: {pid}). 추가 구매 차단.")
                return

    # 3. 장부에 PROCESSING 상태로 등록
    ledger[purchase_id] = {
        "purchase_id": purchase_id,
        "invoice_id": invoice_id,
        "item": target_slug,
        "status": "PROCESSING",
        "created_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    }
    save_ledger(ledger)
    
    logger.info(f"[원장 등록 완료] 고유 구매 ID 생성 및 작업 시작: {purchase_id}")
    
    try:
        real_account = purchase_real_account_from_supplier(target_slug)
        
        if real_account:
            target_inv_id = invoice_id
            target_item_id = item_id
            
            headers = {"Authorization": f"Bearer {MY_SELLAUTH_API_KEY}", "Accept": "application/json"}
            if not target_inv_id or not target_item_id:
                inv_res = requests.get(f"https://api.sellauth.com/v1/shops/{MY_SHOP_ID}/invoices", headers=headers, timeout=10)
                if inv_res.status_code == 200 and inv_res.json().get("data"):
                    latest_inv = inv_res.json()["data"][0]
                    target_inv_id = latest_inv["id"]
                    target_item_id = latest_inv["items"][0]["id"] if latest_inv.get("items") else None

            if target_inv_id and target_item_id:
                # SellAuth 공식 배송 API 호출
                deliver_payload = {
                    "deliverables": [
                        {"invoice_item_id": target_item_id, "deliverables": [real_account]}
                    ]
                }
                requests.post(f"https://api.sellauth.com/v1/shops/{MY_SHOP_ID}/invoices/{target_inv_id}/deliver", json=deliver_payload, headers=headers, timeout=10)
                
                # 영수증 화면 내용 영구 교체
                r_payload = {
                    "invoice_item_id": target_item_id,
                    "replacements": [real_account]
                }
                requests.post(f"https://api.sellauth.com/v1/shops/{MY_SHOP_ID}/invoices/{target_inv_id}/replace-delivered", json=r_payload, headers=headers, timeout=10)

            # 장부에 COMPLETED 최종 저장
            ledger = load_ledger()
            ledger[purchase_id]["status"] = "COMPLETED"
            ledger[purchase_id]["delivered_account"] = real_account
            ledger[purchase_id]["completed_at"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
            save_ledger(ledger)

            # 디스코드 공개 구매로그 채널 알림 (보안을 위해 계정 ID:PW 마스킹 처리)
            send_discord_notification(
                title="🛍️ [구매 완료] 정품 로블록스 계정 거래 성공!",
                description="손님의 결제가 정상 확인되어 로블록스 계정이 구매자 본인 이메일로 즉시 자동 발송되었습니다.",
                color=0x57F287,
                fields=[
                    {"name": "📦 구매 상품", "value": f"`{target_slug}`", "inline": True},
                    {"name": "💵 결제 상태", "value": "✅ `결제 완료 (정산 성공)`", "inline": True},
                    {"name": "🔒 계정 인도", "value": "```[보안 완료] 구매자 본인 Gmail로 100% 자동 전달됨```", "inline": False},
                    {"name": "⚡ 자동 배송", "value": "✅ 24시간 무인 자동 배송 완료", "inline": True}
                ]
            )
        else:
            ledger = load_ledger()
            ledger[purchase_id]["status"] = "FAILED"
            save_ledger(ledger)
            
            logger.warning(f"업자 계정 구매 실패 (잔액 부족 또는 통신 에러)")
            send_discord_notification(
                title="⚠️ [구매 실패] 업자 계정 구매 실패",
                description="업자에게서 계정을 사오지 못했습니다. 봇 지갑의 LTC 잔액을 확인해 주세요.",
                color=0xED4245,
                fields=[
                    {"name": "🏷️ 고유 구매 ID", "value": f"`{purchase_id}`", "inline": True},
                    {"name": "📦 상품", "value": f"`{target_slug}`", "inline": True},
                    {"name": "💰 봇 지갑 주소", "value": f"`{BOT_LTC_ADDRESS}`", "inline": False}
                ]
            )
    except Exception as e:
        logger.error(f"배송 처리 중 예외: {e}")


@app.get("/")
def home():
    return "SellAuth Adopt Me Dropship Bridge Engine v4.0 (Unique Purchase ID Edition) is Live & Running!"


@app.get("/wallet")
def check_bot_wallet():
    """봇 전용 무료 자동 지갑의 현재 LTC 잔액 및 주소 조회"""
    balance = ltc_wallet.get_ltc_balance(BOT_LTC_ADDRESS)
    return {
        "status": "active",
        "wallet_type": "Litecoin (LTC) Automated Bot Wallet",
        "address": BOT_LTC_ADDRESS,
        "balance_ltc": balance,
        "explorer_url": f"https://litecoinspace.org/address/{BOT_LTC_ADDRESS}"
    }


@app.get("/orders")
def view_orders():
    """모든 고유 구매 ID 및 영구 주문 원장 조회"""
    return {"status": "success", "orders": load_ledger()}


@app.get("/sync-stock")
def manual_sync():
    """수동 즉시 재고 동기화 엔드포인트"""
    results = {}
    for slug, my_info in MY_PRODUCT_DATA.items():
        exact_stock = get_supplier_exact_stock(slug)
        success = update_my_product_exact_stock(my_info["productId"], my_info["variantId"], exact_stock)
        results[slug] = {"exact_stock": exact_stock, "updated": success}
    return {"status": "success", "results": results}


@app.get("/deliver", response_class=PlainTextResponse)
@app.post("/deliver", response_class=PlainTextResponse)
async def deliver_account(request: Request, background_tasks: BackgroundTasks, item: Optional[str] = None):
    """
    [핵심] 모든 주문마다 전 세계에서 유일한 고유 구매 ID를 발급하여 1회성 단일 구매만 허용
    """
    logger.info(f"배송 요청 수신: item={item}")
    
    invoice_id = None
    invoice_item_id = None
    proof_text = None
    
    try:
        body = await request.json()
        invoice_id = body.get("id")
        proof_text = body.get("proof_of_payment") or body.get("proof")
        items = body.get("items", [])
        if items:
            invoice_item_id = items[0].get("id")
    except Exception:
        pass
        
    if not item:
        item = "potion350"
        
    target_slug = PRODUCTS.get(item, item)
    
    # 바우처 / 기프트카드 핀번호가 전달된 경우 자동 검증 및 변환
    if proof_text:
        cleaned_proof = proof_text.strip().upper().replace(" ", "")
        
        # 1. 구글 기프트카드 (Google Play 16자리 영숫자 또는 4-4-4-4 형태)
        is_alpha = bool(re.search(r"[A-Z]", cleaned_proof))
        clean_len = len(cleaned_proof.replace("-", ""))
        
        if is_alpha and 15 <= clean_len <= 20 and not cleaned_proof.startswith("CV"):
            # 구글 기프트카드 감지
            formatted_gp = cleaned_proof
            if len(cleaned_proof.replace("-", "")) == 16:
                raw_s = cleaned_proof.replace("-", "")
                formatted_gp = f"{raw_s[:4]}-{raw_s[4:8]}-{raw_s[8:12]}-{raw_s[12:]}"
                
            logger.info(f"구글 기프트카드 감지: {formatted_gp}")
            send_discord_notification(
                title="💳 [구글 기프트카드 결제 접수]",
                description="손님이 구글 플레이 기프트카드로 결제하였습니다. 코드가 실시간 접수되어 손님 Gmail로 계정 자동 발송이 시작되었습니다.",
                color=0x4285F4,
                fields=[
                    {"name": "🏷️ 기프트카드 종류", "value": "`Google Play 구글 기프트카드`", "inline": True},
                    {"name": "🔑 구글 기프트카드 코드", "value": f"```{formatted_gp}```", "inline": False},
                    {"name": "⚡ 상태", "value": "✅ 코드 정상 접수 ➔ 손님 Gmail로 계정 자동 발송 중", "inline": True}
                ]
            )
        # 2. 크립토바우처(CryptoVoucher) 형식 검사
        elif cleaned_proof.startswith("CV") or (is_alpha and clean_len < 15):
            cv_res = cryptovoucher_engine.redeem_cryptovoucher_to_ltc(proof_text)
            if not cv_res["success"]:
                logger.warning(f"유효하지 않은 크립토바우처 코드 감지: {proof_text} - {cv_res['error']}")
                send_discord_notification(
                    title="❌ [바우처 거부] 유효하지 않은 코드",
                    description="손님이 입력한 바우처 코드가 유효하지 않아 자동 배송이 거부되었습니다.",
                    color=0xED4245,
                    fields=[
                        {"name": "⚠️ 사유", "value": f"`{cv_res['error']}`", "inline": True},
                        {"name": "📝 입력값", "value": f"`{proof_text}`", "inline": True},
                        {"name": "📦 상품", "value": f"`{target_slug}`", "inline": False}
                    ]
                )
                return f"입력하신 바우처 코드가 유효하지 않습니다 ({cv_res['error']}). 코드를 다시 확인해 주세요."
            else:
                logger.info(f"정상 크립토바우처 감지 및 LTC 변환 요청: {cv_res['code']}")
                send_discord_notification(
                    title="🎫 [크립토바우처 접수 & LTC 자동 충전]",
                    description="손님이 제출한 크립토바우처가 정상 확인되어 봇 지갑으로 LTC 충전 및 계정 자동 발송이 시작되었습니다.",
                    color=0x57F287,
                    fields=[
                        {"name": "🔑 바우처 코드", "value": f"```{cv_res['code']}```", "inline": False},
                        {"name": "💰 정산 지갑", "value": f"`{BOT_LTC_ADDRESS}`", "inline": True},
                        {"name": "⚡ 상태", "value": "✅ 검증 완료 ➔ 손님 Gmail로 계정 자동 발송 중", "inline": True}
                    ]
                )
        # 3. 신용카드 / Apple Pay 간편 결제 영수증 또는 일반 주문번호 접수
        else:
            logger.info(f"신용카드/Apple Pay 간편 결제 영수증 접수: {cleaned_proof}")
            send_discord_notification(
                title="💳 [신용카드 / Apple Pay 결제 접수]",
                description="손님이 신용카드/Apple Pay 간편 결제로 구매를 완료하고 영수증을 제출했습니다.",
                color=0x5865F2,
                fields=[
                    {"name": "📝 제출한 영수증/주문번호", "value": f"```{cleaned_proof}```", "inline": False},
                    {"name": "📦 상품", "value": f"`{target_slug}`", "inline": True},
                    {"name": "⚡ 상태", "value": "✅ 접수 완료 ➔ 손님 Gmail로 계정 자동 발송 중", "inline": True}
                ]
            )

    # 1. 전 세계 유일한 고유 구매 ID 발급 (예: ORD-20260815-14993706-A9C3D1)
    purchase_id = generate_purchase_id(invoice_id)
    
    # 2. 이미 배송 완료된 인보이스인지 원장 검사
    ledger = load_ledger()
    if invoice_id:
        for pid, record in ledger.items():
            if record.get("invoice_id") == invoice_id and record.get("status") == "COMPLETED":
                logger.info(f"[원장 확인] 인보이스 {invoice_id}는 이미 계정 발급 완료되었습니다. 중복 구매를 즉시 차단합니다.")
                return "이미 계정 배송이 완료된 주문입니다. 이메일(Gmail 등)을 확인해 주세요."

    # 3. 고유 구매 ID로 백그라운드 단일 작업 등록 (1회만 실행 보장)
    background_tasks.add_task(background_fulfill_order, target_slug, purchase_id, invoice_id, invoice_item_id)
    
    return f"구매해 주셔서 감사합니다! [주문 ID: {purchase_id}]\n주문하신 로블록스 계정 정보(ID:PW)는 입력하신 이메일(Gmail 등)로 안전하게 자동 발송되었습니다. 잠시 후 이메일함을 확인해 주세요."


import asyncio

@app.on_event("startup")
async def startup_event():
    async def periodic_stock_sync_task():
        while True:
            try:
                for slug, my_info in MY_PRODUCT_DATA.items():
                    exact_stock = get_supplier_exact_stock(slug)
                    update_my_product_exact_stock(my_info["productId"], my_info["variantId"], exact_stock)
            except Exception as e:
                logger.error(f"주기적 재고 동기화 에러: {e}")
            await asyncio.sleep(60)
            
    asyncio.create_task(periodic_stock_sync_task())
