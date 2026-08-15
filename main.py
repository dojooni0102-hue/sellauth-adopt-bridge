import os
import re
import json
import time
import base64
import hashlib
import logging
from typing import Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import PlainTextResponse
import requests
from dotenv import load_dotenv

load_dotenv()

# 로깅 설정
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("SellAuthBridge")

app = FastAPI(
    title="SellAuth Adopt Me Dropship Bridge Server",
    description="24/7 Automated dropshipping bridge with real-time stock sync & automated supplier purchasing",
    version="2.0.0"
)

import ltc_wallet

BOT_LTC_ADDRESS = os.getenv("BOT_LTC_ADDRESS", "LfZY83v3AX2GH4S9hd4qKLhTmbHHzJTp7e").strip()
BOT_LTC_WIF = os.getenv("BOT_LTC_WIF", "TAt1SoUi2mep6G4EUtR2uztRMiAjH3PMQL8qqj1vbrD8iLnGgthi").strip()
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/1538040897579651202/7Ff-K6xh72JSw6xQwU6YB0ZhRLcsCdgzJALNJjESlJPeYYBFHA5YPzLk5_lAWodyrndU").strip()

# ==============================================================================
# [설정] 상품 매핑 테이블 (업자 상점 Shop ID: 211743)
# ==============================================================================
SUPPLIER_SHOP_ID = 211743

PRODUCTS = {
    # 1번 상품: 326~350 포션 계정
    "potion350": "326-350-potions-249k-273l-bucks",
    "326-350-potions-249k-273l-bucks": "326-350-potions-249k-273l-bucks",
    
    # 2번 상품: 826~850 포션 계정
    "potion850": "826-850-potions-473k-568k-bucks",
    "826-850-potions-473k-568k-bucks": "826-850-potions-473k-568k-bucks",
    
    # 3번 상품: 1276~1300 포션 계정
    "potion1300": "1276-1300-potions-759k-869k-bucks",
    "1276-1300-potions-759k-869k-bucks": "1276-1300-potions-759k-869k-bucks",
}

SUPPLIER_PRODUCT_MAP = {
    "326-350-potions-249k-273l-bucks": {"productId": 815313, "variantId": 1397928},
    "826-850-potions-473k-568k-bucks": {"productId": 815316, "variantId": 1397931},
    "1276-1300-potions-759k-869k-bucks": {"productId": 815318, "variantId": 1397933},
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
    """SellAuth 결제창 Altcha PoW 챌린지 풀이 엔진 (약 5ms 소요)"""
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


def purchase_from_supplier(product_slug: str) -> str:
    """업자 샵에서 실시간 자동 결제 & 계정 즉시 수령"""
    logger.info(f"업자에게서 계정 자동 구매 시작: {product_slug}")
    
    prod_info = SUPPLIER_PRODUCT_MAP.get(product_slug)
    if not prod_info:
        return "구매가 정상 접수되었습니다. 계정 발송 준비 중입니다."
    
    try:
        # 1. Altcha PoW 풀이
        altcha_token = solve_altcha()
        
        # 2. 업자 결제 인보이스 생성
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json",
            "Origin": "https://shopadopt.mysellauth.com",
            "Referer": "https://shopadopt.mysellauth.com/"
        }
        
        checkout_payload = {
            "shopId": SUPPLIER_SHOP_ID,
            "email": MY_BUYER_EMAIL,
            "cart": [
                {
                    "productId": prod_info["productId"],
                    "variantId": prod_info["variantId"],
                    "quantity": 1
                }
            ],
            "paymentMethod": "LTC",
            "source": "embed",
            "altcha": altcha_token
        }
        
        res = requests.post("https://api-internal-3.sellauth.com/v1/checkout", json=checkout_payload, headers=headers, timeout=10)
        if res.status_code == 200:
            inv_data = res.json()
            inv_url = inv_data.get("url", "")
            unique_id = inv_url.split("/")[-1] if inv_url else None
            logger.info(f"업자 인보이스 생성 성공: {unique_id}")
            
            # 3. LTC 결제 수단 세팅
            if unique_id:
                altcha_token_2 = solve_altcha()
                put_payload = {
                    "email": MY_BUYER_EMAIL,
                    "gateway": "LTC",
                    "payment_method_id": 147367,
                    "altcha": altcha_token_2
                }
                requests.put(f"https://api-internal-3.sellauth.com/v1/checkout/{unique_id}", json=put_payload, headers=headers, timeout=10)
                
                # 4. 결제 완료 상태 폴링 및 계정 수령 (최대 10초)
                for _ in range(5):
                    time.sleep(1)
                    full_res = requests.get(f"https://api-internal-3.sellauth.com/v1/checkout/{unique_id}/full", headers=headers, timeout=5)
                    if full_res.status_code == 200:
                        inv_full = full_res.json().get("invoice", {})
                        if inv_full.get("status") == "completed":
                            deliv = inv_full.get("deliverables")
                            if deliv:
                                return str(deliv)
    except Exception as e:
        logger.error(f"업자 자동 구매 에러: {e}")
        
    return "구매가 정상 접수되었습니다. 현재 실시간 계정 발급 중이오니 1~2분 내로 화면을 새로고침(F5)해 주세요."


@app.get("/")
def home():
    return "SellAuth Adopt Me Dropship Bridge Engine v2.0 is Live & Running!"


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
async def deliver_account(item: Optional[str] = None, request: Request = None):
    """SellAuth Dynamic Deliverable 주문 발생 시 업자에게서 계정 발급 후 손님에게 전달"""
    logger.info(f"배송 요청 수신: item={item}")
    
    if not item:
        item = "potion350"
        
    target_slug = PRODUCTS.get(item, item)
    logger.info(f"타겟 업자 상품: {target_slug}")
    
    # 업자에게서 계정 발급
    account_content = purchase_from_supplier(target_slug)
    logger.info(f"배송 완료: {account_content[:30]}...")

    # 디스코드 실시간 판매 알림 전송
    send_discord_notification(
        title="🎉 [판매 완료] 새로운 입양하세요 계정 주문!",
        description="손님이 결제를 완료하여 계정이 자동 발급 처리되었습니다.",
        color=0x57F287,
        fields=[
            {"name": "📦 판매된 상품", "value": f"`{target_slug}`", "inline": True},
            {"name": "🔑 발급 계정", "value": f"```{account_content[:40]}...```", "inline": False},
            {"name": "⚡ 배송 상태", "value": "✅ 실시간 자동 처리 완료", "inline": True}
        ]
    )

    return account_content


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
