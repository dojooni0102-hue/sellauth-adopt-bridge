import os
import re
import json
import time
import base64
import hashlib
import logging
from datetime import datetime
import requests

logger = logging.getLogger("LiveStockDiscord")

# 실시간 재고 업데이트 전용 디스코드 웹후크 URL
WEBHOOK_URL = "https://discord.com/api/webhooks/1538763716437213214/AHU3OwVaLuZ0q0_hUTV54UwO4FklfA81N-8pf2WoXmS2tlCfYsryp4-nUBJfFcNe4TZh"
MSG_ID_FILE = "discord_stock_msg_id.txt"

MY_SELLAUTH_API_KEY = os.getenv("MY_SELLAUTH_API_KEY", "6041435|EbpGObFUfemI3XElDjR99Y6EQc9rwFkoU1WGQF1L7ee51812").strip()
MY_SHOP_ID = os.getenv("MY_SHOP_ID", "261184").strip()

SUPPLIER_DOMAIN = "shopadopt"
SUPPLIER_URL = f"https://{SUPPLIER_DOMAIN}.mysellauth.com"

# 매핑 테이블 (내 상품 slug -> 업자 상품 slug)
SLUG_MAP = {
    "potion350": "326-350-potions-249k-273l-bucks",
    "326-350-potions-249k-273l-bucks": "326-350-potions-249k-273l-bucks",
    "potion850": "826-850-potions-473k-568k-bucks",
    "826-850-potions-473k-568k-bucks": "826-850-potions-473k-568k-bucks",
    "potion1300": "1276-1300-potions-759k-869k-bucks",
    "1276-1300-potions-759k-869k-bucks": "1276-1300-potions-759k-869k-bucks",
}

supplier_session = requests.Session()
supplier_session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
})

def solve_sellauth_challenge(html: str):
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

def get_supplier_exact_stock(product_slug: str) -> int:
    """업자 샵에서 실시간 정확한 재고 수량 조회"""
    target_slug = SLUG_MAP.get(product_slug, product_slug)
    url = f"{SUPPLIER_URL}/product/{target_slug}"
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
        logger.error(f"업자 재고 확인 실패 ({product_slug}): {e}")
    return 0

def fetch_all_shop_products():
    """내 상점의 모든 상품 목록을 가져옴"""
    url = f"https://api.sellauth.com/v1/shops/{MY_SHOP_ID}/products"
    headers = {"Authorization": f"Bearer {MY_SELLAUTH_API_KEY}", "Accept": "application/json"}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            return res.json().get("data", [])
    except Exception as e:
        logger.error(f"내 상점 상품 목록 조회 실패: {e}")
    return []

def get_saved_msg_id() -> str:
    if os.path.exists(MSG_ID_FILE):
        try:
            with open(MSG_ID_FILE, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception:
            return ""
    return ""

def save_msg_id(msg_id: str):
    try:
        with open(MSG_ID_FILE, "w", encoding="utf-8") as f:
            f.write(msg_id.strip())
    except Exception as e:
        logger.error(f"메시지 ID 저장 실패: {e}")

def update_live_stock_embed() -> bool:
    """모든 상품의 재고 수량만 이쁘게 표시하여 단 1개의 디스코드 메시지로 계속 수정(PATCH) 업데이트"""
    products = fetch_all_shop_products()
    if not products:
        logger.warning("상품 목록을 불러오지 못했습니다.")
        return False
        
    fields = []
    total_stock = 0
    
    for prod in products:
        prod_name = prod.get("name", "상품")
        prod_path = prod.get("path", "")
        # 가격 제외, 재고 수량만 계산
        stock = get_supplier_exact_stock(prod_path)
        if stock == 0 and prod.get("stock_count") is not None:
            stock = prod.get("stock_count")
            
        total_stock += stock
        status_str = f"`{stock}개` (즉시 구매 가능)" if stock > 0 else "`품절 (재입고 대기 중)`"
        
        fields.append({
            "name": f"🧪 {prod_name}",
            "value": f"└ **현재 실시간 재고**: {status_str}",
            "inline": False
        })
        
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S KST")
    
    embed = {
        "title": "📦 [상점 전 품목 실시간 재고 현황판]",
        "description": f"24시간 실시간 무인 갱신되는 상점 전체 상품 재고 목록입니다.\n**전체 실시간 합산 재고**: `{total_stock}개`\n*(도준 샵 전용 실시간 현황판)*",
        "color": 0x2ECC71 if total_stock > 0 else 0xE74C3C,
        "fields": fields,
        "footer": {
            "text": f"🔄 마지막 실시간 업데이트: {now_str} (단일 메시지 수정 모드)"
        }
    }
    
    payload = {"embeds": [embed]}
    msg_id = get_saved_msg_id()
    
    # 1. 기존 메시지가 존재하면 PATCH로 1개 메시지만 계속 수정
    if msg_id:
        patch_url = f"{WEBHOOK_URL}/messages/{msg_id}"
        try:
            res = requests.patch(patch_url, json=payload, timeout=5)
            if res.status_code == 200:
                logger.info(f"디스코드 단일 재고 메시지 수정(PATCH) 성공! (Msg ID: {msg_id})")
                return True
            else:
                logger.warning(f"메시지 수정 실패 ({res.status_code}), 메시지를 신규 생성합니다.")
        except Exception as e:
            logger.error(f"메시지 PATCH 실패: {e}")
            
    # 2. 기존 메시지가 없거나 404면 신규 생성 (POST + wait=true)
    try:
        post_url = f"{WEBHOOK_URL}?wait=true"
        res = requests.post(post_url, json=payload, timeout=5)
        if res.status_code in [200, 201]:
            new_msg_id = res.json().get("id")
            if new_msg_id:
                save_msg_id(new_msg_id)
                logger.info(f"디스코드 단일 재고 메시지 신규 작성 완료! (Msg ID: {new_msg_id})")
                return True
    except Exception as e:
        logger.error(f"메시지 POST 실패: {e}")
        
    return False

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("Updating live stock embed on Discord...")
    success = update_live_stock_embed()
    print("Execution Success:", success)
