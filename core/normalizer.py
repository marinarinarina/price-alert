"""가격 파싱, 토큰 추출, 이상징후 감지"""

import re
from typing import Optional, Set
from config.constants import PRICE_CHANGE_THRESHOLD, TOKEN_MISMATCH_THRESHOLD


class Normalizer:
    """가격/상품명 정규화 및 검증"""

    @staticmethod
    def parse_price(price_text: str) -> Optional[int]:
        """
        가격 문자열 파싱
        예: "1,234,567원" → 1234567
        """
        if not price_text:
            return None

        # 숫자만 추출
        digits = re.sub(r"[^\d]", "", price_text)

        try:
            return int(digits) if digits else None
        except ValueError:
            return None

    @staticmethod
    def extract_core_tokens(title: str) -> Set[str]:
        """
        상품명에서 핵심 토큰 추출
        예: "삼성 RTX 4070 Ti SUPER 16GB" → {삼성, rtx, 4070, ti, super, 16gb}
        """
        if not title:
            return set()

        # 소문자 변환 및 특수문자 제거
        normalized = re.sub(r"[^\w\s가-힣]", " ", title.lower())

        # 토큰 분리 (의미있는 단어만)
        tokens = set()
        for token in normalized.split():
            # 2글자 이상 또는 숫자 포함 토큰만
            if len(token) >= 2 or re.search(r"\d", token):
                tokens.add(token)

        return tokens

    @staticmethod
    def check_token_mismatch(title1: str, title2: str) -> bool:
        """
        두 상품명의 핵심 토큰 불일치 여부 확인
        Returns: True if mismatch detected
        """
        tokens1 = Normalizer.extract_core_tokens(title1)
        tokens2 = Normalizer.extract_core_tokens(title2)

        if not tokens1 or not tokens2:
            return True

        # 교집합 비율 계산
        intersection = tokens1 & tokens2
        union = tokens1 | tokens2

        similarity = len(intersection) / len(union) if union else 0

        return similarity < (1 - TOKEN_MISMATCH_THRESHOLD)

    @staticmethod
    def check_abnormal_price_change(old_price: int, new_price: int) -> bool:
        """
        가격 급변 여부 확인 (±30% 이상)
        Returns: True if abnormal
        """
        if old_price <= 0:
            return False

        change_ratio = abs(new_price - old_price) / old_price

        return change_ratio > PRICE_CHANGE_THRESHOLD

    @staticmethod
    def clean_title(title: str, max_length: int = 100) -> str:
        """상품명 정리 (공백 제거, 길이 제한)"""
        cleaned = " ".join(title.split())
        return cleaned[:max_length] if len(cleaned) > max_length else cleaned
