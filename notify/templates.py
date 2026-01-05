"""이메일 템플릿"""

from typing import Dict, List
from core.models import PriceResult


def create_price_alert_email(keyword: str, results: List[PriceResult]) -> tuple:
    """
    가격 알림 이메일 생성

    Returns:
        (subject, body) 튜플
    """
    subject = f"[최저가 알림] {keyword}"

    # 사이트별 정보
    site_info = []
    for result in results:
        site_name = "다나와" if result.site == "danawa" else "지마켓"
        site_info.append(
            f"""
【{site_name}】
상품명: {result.title}
가격: {result.price:,}원
링크: {result.product_url}
조회시각: {result.fetched_at}
        """.strip()
        )

    body = f"""
안녕하세요, 최저가 알림이입니다.

관심상품 '{keyword}'의 최신 가격 정보를 알려드립니다.

{chr(10).join(site_info)}

---
본 알림은 자동으로 발송되었습니다.
배송비, 카드할인, 쿠폰 등은 포함되지 않은 표시가 기준입니다.
    """.strip()

    return subject, body


def create_test_email() -> tuple:
    """테스트 이메일 생성"""
    subject = "[테스트] 최저가 알림이 이메일 설정 확인"
    body = """
안녕하세요, 최저가 알림이입니다.

이메일 설정이 정상적으로 완료되었습니다.
실제 가격 알림은 설정하신 주기에 따라 자동으로 발송됩니다.

감사합니다.
    """.strip()

    return subject, body


def create_status_alert_email(keyword: str, status: str, message: str) -> tuple:
    """
    상태 알림 이메일 생성 (차단 의심, 재확인 필요 등)

    Returns:
        (subject, body) 튜플
    """
    status_text = {
        "not_found": "검색 결과 없음",
        "needs_confirmation": "재확인 필요",
        "blocked_suspected": "접속 차단 의심",
    }.get(status, "알 수 없는 상태")

    subject = f"[상태 알림] {keyword} - {status_text}"

    body = f"""
안녕하세요, 최저가 알림이입니다.

관심상품 '{keyword}'에 문제가 발생했습니다.

상태: {status_text}
내용: {message}

프로그램을 확인해주시기 바랍니다.

---
본 알림은 자동으로 발송되었습니다.
    """.strip()

    return subject, body
