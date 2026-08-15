import re
import logging

logger = logging.getLogger("VoucherValidator")

def clean_pin_string(raw_input: str) -> str:
    """공백, 하이픈(-), 특수문자 제거 후 숫자만 추출"""
    if not raw_input:
        return ""
    return re.sub(r"[^0-9]", "", str(raw_input).strip())

def identify_and_validate_voucher(raw_pin: str) -> dict:
    """
    한국 문화상품권 (컬쳐랜드, 해피머니, 북앤라이프, 온라인문상) 핀번호 유효성 및 형식 자동 판별 엔진
    """
    clean_digits = clean_pin_string(raw_pin)
    length = len(clean_digits)
    
    # 1. 핀번호 길이 기본 검증 (16자리 또는 18자리 필수)
    if length not in [16, 18]:
        return {
            "is_valid_format": False,
            "voucher_type": "UNKNOWN",
            "clean_pin": clean_digits,
            "formatted_pin": raw_pin,
            "reason": f"유효하지 않은 자릿수 ({length}자리 - 16자리 또는 18자리 필수)"
        }
        
    # 2. 명백한 허위 핀번호 필터링 (동일 숫자 반복, 단순 연속 숫자 등)
    if len(set(clean_digits)) <= 3: # 예: 1111111111111111 등
        return {
            "is_valid_format": False,
            "voucher_type": "FAKE_SUSPECTED",
            "clean_pin": clean_digits,
            "formatted_pin": raw_pin,
            "reason": "허위 의심 핀번호 (동일 숫자 과다 반복)"
        }

    # 3. 상품권 종류별 정밀 패턴 분석
    if length == 16:
        # 16자리: 컬쳐랜드(구형) / 해피머니 / 북앤라이프(도서문상)
        # 컬쳐랜드 16자리 형식 (4-4-4-4)
        formatted = f"{clean_digits[:4]}-{clean_digits[4:8]}-{clean_digits[8:12]}-{clean_digits[12:]}"
        
        # 앞자리 프리픽스 패턴 분석
        first_4 = clean_digits[:4]
        if first_4.startswith(('21', '22', '23', '24', '31', '32', '41')):
            vtype = "컬쳐랜드 16자리 문화상품권"
        elif first_4.startswith(('42', '43', '44', '51', '52')):
            vtype = "해피머니 상품권"
        elif first_4.startswith(('11', '12', '13', '14')):
            vtype = "북앤라이프(도서문화상품권)"
        else:
            vtype = "16자리 통합 문화상품권"
            
        return {
            "is_valid_format": True,
            "voucher_type": vtype,
            "clean_pin": clean_digits,
            "formatted_pin": formatted,
            "reason": "정상적인 16자리 핀번호 규격 확인 완료"
        }
        
    elif length == 18:
        # 18자리: 온라인 문화상품권 (지앤미 / 모바일 문상) (4-4-4-6)
        formatted = f"{clean_digits[:4]}-{clean_digits[4:8]}-{clean_digits[8:12]}-{clean_digits[12:]}"
        return {
            "is_valid_format": True,
            "voucher_type": "온라인 18자리 문화상품권 (지앤미/모바일)",
            "clean_pin": clean_digits,
            "formatted_pin": formatted,
            "reason": "정상적인 18자리 핀번호 규격 확인 완료"
        }

    return {
        "is_valid_format": False,
        "voucher_type": "UNKNOWN",
        "clean_pin": clean_digits,
        "formatted_pin": raw_pin,
        "reason": "인식할 수 없는 상품권 규격"
    }

if __name__ == "__main__":
    test_cases = [
        "2134-5678-9012-3456",
        "4234567890123456",
        "1234-5678-9012-345678",
        "1111-1111-1111-1111",
        "abcd-1234-5678",
        "4123-9988-7766-5544"
    ]
    for tc in test_cases:
        res = identify_and_validate_voucher(tc)
        print(f"[{tc}] -> Valid: {res['is_valid_format']} | Type: {res['voucher_type']} | Formatted: {res['formatted_pin']} | Reason: {res['reason']}")
