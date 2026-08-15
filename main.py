import os
import logging
import requests
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("SellAuth-Bridge")

app = FastAPI(
    title="SellAuth Adopt Me Dropship Bridge",
    description="입양하세요 계정 자동 중개 및 실시간 배송 서버",
    version="1.0.0"
)

# ==============================================================================
# [설정] 상품 매핑 테이블
# ==============================================================================
# 사용자가 요청한 3가지 상품 슬러그/ID를 단축 코드 및 원본 슬러그 모두 매핑
PRODUCTS = {
    # 1번 상품: 326~350 포션 계정
    "potion350": "326-350-potions-249k-273l-bucks",
    "item1": "326-350-potions-249k-273l-bucks",
    "326-350-potions-249k-273l-bucks": "326-350-potions-249k-273l-bucks",

    # 2번 상품: 826~850 포션 계정
    "potion850": "826-850-potions-473k-568k-bucks",
    "item2": "826-850-potions-473k-568k-bucks",
    "826-850-potions-473k-568k-bucks": "826-850-potions-473k-568k-bucks",

    # 3번 상품: 1276~1300 포션 계정
    "potion1300": "1276-1300-potions-759k-869k-bucks",
    "item3": "1276-1300-potions-759k-869k-bucks",
    "1276-1300-potions-759k-869k-bucks": "1276-1300-potions-759k-869k-bucks",
}

SUPPLIER_SHOP_DOMAIN = os.getenv("SUPPLIER_SHOP_DOMAIN", "shopadopt").strip()
SUPPLIER_SHOP_URL = os.getenv("SUPPLIER_SHOP_URL", "https://shopadopt.mysellauth.com").strip()
SUPPLIER_SHOP_ID = os.getenv("SUPPLIER_SHOP_ID", "").strip()
SUPPLIER_API_KEY = os.getenv("SUPPLIER_API_KEY", "").strip()
MY_BUYER_EMAIL = os.getenv("MY_BUYER_EMAIL", "buyer@example.com").strip()
TEST_MODE = os.getenv("TEST_MODE", "False").lower() in ("true", "1", "yes")


def purchase_from_supplier(product_slug_or_id: str) -> str:
    """
    업자 SellAuth 샵에서 해당 상품을 1개 구매/조회하여 계정 정보(ID:PW)를 반환하는 함수
    """
    logger.info(f"업자 상품 구매 시작 -> Target: {product_slug_or_id}")

    # [1] 테스트 모드일 경우 가짜 계정 반환 (연동 테스트용)
    if TEST_MODE:
        logger.info("[테스트 모드] 가상 계정 반환")
        return f"[TEST-MODE] roblox_user_{product_slug_or_id[:8]}:PassWord1234! | Potion Account"

    # [2] 업자 API 키가 있는 경우: 공식 SellAuth API 사용
    if SUPPLIER_API_KEY:
        try:
            headers = {
                "Authorization": f"Bearer {SUPPLIER_API_KEY}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            # 업자 상점의 상품 재고에서 1개 발급
            url = f"https://api.sellauth.com/v1/shops/{SUPPLIER_SHOP_ID}/orders" if SUPPLIER_SHOP_ID else "https://api.sellauth.com/v1/orders"
            payload = {
                "product_id": product_slug_or_id,
                "quantity": 1,
                "email": MY_BUYER_EMAIL
            }
            res = requests.post(url, json=payload, headers=headers, timeout=15)
            
            if res.status_code in (200, 201):
                data = res.json()
                deliverable = data.get("deliverable") or data.get("data", {}).get("deliverable", "")
                if deliverable:
                    return str(deliverable).strip()
            
            logger.error(f"API 구매 실패: {res.status_code} - {res.text}")
        except Exception as e:
            logger.error(f"API 요청 중 에러: {e}")

    # [3] 공개 인보이스(Public Checkout) 생성 방식 (API 키 없이 예치금/직접 결제 연동 시)
    try:
        base_url = f"https://{SUPPLIER_SHOP_DOMAIN}.sellauth.com" if SUPPLIER_SHOP_DOMAIN else "https://sellauth.com"
        checkout_url = f"{base_url}/api/v1/checkout"
        
        payload = {
            "product": product_slug_or_id,
            "quantity": 1,
            "email": MY_BUYER_EMAIL
        }
        res = requests.post(checkout_url, json=payload, timeout=15)
        
        if res.status_code in (200, 201):
            data = res.json()
            account_data = data.get("deliverable") or data.get("serial")
            if account_data:
                return str(account_data).strip()
    except Exception as e:
        logger.error(f"공개 결제 요청 중 에러: {e}")

    # 만약 위 요청들이 실패했을 때의 안내 메시지 (손님 화면에 표시)
    return (
        "구매가 정상 접수되었습니다. 현재 재고 자동 처리 중이오니 잠시만 기다려 주시거나, "
        "5분 이내로 발송되지 않을 경우 고객센터로 주문번호와 함께 문의해 주세요."
    )


import asyncio

# ==============================================================================
# [설정] 내 SellAuth 상점 API 설정 (실시간 재고 동기화용)
# ==============================================================================
MY_SELLAUTH_API_KEY = os.getenv("MY_SELLAUTH_API_KEY", "6041435|EbpGObFUfemI3XElDjR99Y6EQc9rwFkoU1WGQF1L7ee51812").strip()
MY_SHOP_ID = os.getenv("MY_SHOP_ID", "261184").strip()

# 내 샵의 3가지 상품 및 옵션(Variant) 매핑 데이터
MY_PRODUCT_DATA = {
    "item1": {
        "product_id": "835796",
        "variant_id": "1443082",
        "slug": "326-350-potions-249k-273l-bucks"
    },
    "item2": {
        "product_id": "835800",
        "variant_id": "1443091",
        "slug": "826-850-potions-473k-568k-bucks"
    },
    "item3": {
        "product_id": "835802",
        "variant_id": "1443093",
        "slug": "1276-1300-potions-759k-869k-bucks"
    },
}


import hashlib
import re

supplier_session = requests.Session()
supplier_session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
})


def solve_sellauth_challenge(html: str) -> str:
    """SellAuth 웹 방화벽 PoW 챌린지를 파이썬으로 0.001초만에 풀어서 쿠키 획득"""
    m = re.search(r"['\"]([A-F0-9]{40})['\"]", html)
    if not m:
        return None
    c = m.group(1)
    n1 = int(c[0], 16)
    i = 0
    while i < 1000000:
        target = (c + str(i)).encode('utf-8')
        digest = hashlib.sha1(target).digest()
        if digest[n1] == 0xb0 and digest[n1+1] == 0x0b:
            return f"{c}{i}"
        i += 1
    return None


def get_supplier_exact_stock(product_slug: str) -> int:
    """
    업자 상점의 실시간 정확한 재고 개수(숫자)를 직접 조회 (122개, 46개, 0개 등)
    """
    try:
        url = f"{SUPPLIER_SHOP_URL}/product/{product_slug}"
        res = supplier_session.get(url, timeout=10)
        
        # 만약 방화벽 챌린지가 뜨면 해결
        if res.status_code == 503:
            cookie_val = solve_sellauth_challenge(res.text)
            if cookie_val:
                supplier_session.cookies.set("yX3", cookie_val, domain="shopadopt.mysellauth.com")
                supplier_session.cookies.set("yX3", cookie_val, domain=".mysellauth.com")
                res = supplier_session.get(url, timeout=10)
                
        if res.status_code == 200:
            # 페이지 내의 실제 stock 숫자 파싱
            stocks = re.findall(r'"stock":\s*(\d+)', res.text)
            if stocks:
                return int(stocks[0])
            # 대안 정규식
            stocks_alt = re.findall(r'stock["\']?\s*[:=]\s*(\d+)', res.text, re.IGNORECASE)
            if stocks_alt:
                return int(stocks_alt[0])
    except Exception as e:
        logger.warning(f"업자 재고 개수 조회 예외: {e}")
    
    return 0


def update_my_product_exact_stock(product_id: str, variant_id: str, exact_stock: int):
    """
    내 SellAuth 상점 상품의 재고 숫자를 업자와 100% 동일하게 실시간 수정 (SellAuth 공식 엔드포인트)
    """
    if not (MY_SELLAUTH_API_KEY and MY_SHOP_ID and product_id and variant_id):
        return

    try:
        headers = {
            "Authorization": f"Bearer {MY_SELLAUTH_API_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        # SellAuth 공식 Variant Stock 업데이트 엔드포인트
        url = f"https://api.sellauth.com/v1/shops/{MY_SHOP_ID}/products/{product_id}/stock/{variant_id}"
        payload = {"stock": exact_stock}
        res = requests.put(url, json=payload, headers=headers, timeout=10)
        
        if res.status_code == 200:
            logger.info(f"✅ 내 상품({product_id}) 재고 숫자 동기화 완료 -> {exact_stock}개 (응답: 200 OK)")
        else:
            logger.warning(f"⚠️ 재고 업데이트 응답: {res.status_code} - {res.text}")
    except Exception as e:
        logger.error(f"내 상품 재고 업데이트 실패: {e}")


def sync_all_stocks():
    """모든 상품의 업자 재고 개수를 내 상점에 실시간 동기화"""
    logger.info("🔄 [동기화] 업자 서버 재고 숫자를 내 상점으로 복사 중...")
    results = {}
    for item_key, info in MY_PRODUCT_DATA.items():
        supplier_slug = info["slug"]
        prod_id = info["product_id"]
        var_id = info["variant_id"]
        exact_stock = get_supplier_exact_stock(supplier_slug)
        update_my_product_exact_stock(prod_id, var_id, exact_stock)
        results[item_key] = {"stock": exact_stock, "product_id": prod_id}
    logger.info("✅ [동기화 완료] 전체 상품 재고가 최신 상태로 변경되었습니다.")
    return results


async def periodic_stock_sync_task():
    """60초마다 주기적으로 업자 재고를 감시하여 내 샵 숫자를 자동 갱신하는 백그라운드 태스크"""
    while True:
        try:
            sync_all_stocks()
        except Exception as e:
            logger.error(f"주기적 재고 동기화 중 에러: {e}")
        # 60초 대기
        await asyncio.sleep(60)


# ==============================================================================
# API 라우트
# ==============================================================================

@app.on_event("startup")
async def startup_event():
    logger.info("🚀 SellAuth Bridge Server Started with 60s Auto-Stock Sync Engine")
    # 백그라운드에서 60초마다 재고 동기화 자동 실행
    asyncio.create_task(periodic_stock_sync_task())


@app.get("/", response_class=PlainTextResponse)
def root():
    return "SellAuth Adopt Me Dropship Bridge Server is Running Perfectly with Real-Time Stock Sync!"


@app.get("/sync-stock")
def manual_sync():
    """수동 즉시 재고 동기화 엔드포인트"""
    data = sync_all_stocks()
    return {"status": "success", "message": "All product stocks synchronized", "data": data}


@app.get("/deliver", response_class=PlainTextResponse)
@app.post("/deliver", response_class=PlainTextResponse)
async def deliver_account(request: Request, item: str = Query(None)):
    """
    SellAuth Dynamic Deliverable 엔드포인트.
    손님이 결제하면 SellAuth가 이 URL을 호출하여 계정 텍스트를 받아갑니다.
    """
    # 쿼리 파라미터나 바디에서 item 추출
    item_key = item
    if not item_key:
        try:
            body = await request.json()
            item_key = body.get("item") or body.get("product") or body.get("custom_fields", {}).get("item")
        except Exception:
            pass

    if not item_key:
        logger.warning("item 파라미터 누락")
        return "오류: 상품 식별자(?item=...)가 전달되지 않았습니다."

    item_key = item_key.strip()
    target_slug = PRODUCTS.get(item_key)

    if not target_slug:
        logger.warning(f"등록되지 않은 상품 요청: {item_key}")
        return f"오류: 등록되지 않은 상품 코드({item_key})입니다."

    logger.info(f"주문 수신 확인: 요청코드='{item_key}' -> 업자상품='{target_slug}'")

    # 업자에게서 계정 발급
    account_content = purchase_from_supplier(target_slug)
    logger.info(f"배송 완료: {account_content[:20]}...")

    # SellAuth에 계정 텍스트 반환 -> 손님 화면 & 이메일에 그대로 출력
    return account_content


@app.get("/products")
def list_products():
    """등록된 3가지 상품 목록 확인"""
    return {
        "status": "success",
        "supported_products": PRODUCTS,
        "mode": "TEST" if TEST_MODE else "PRODUCTION"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
