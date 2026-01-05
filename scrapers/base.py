"""스크래퍼 기본 인터페이스"""

from abc import ABC, abstractmethod
from typing import List, Optional
import requests
from bs4 import BeautifulSoup
from core.models import Candidate, PriceResult
from config.constants import USER_AGENT, REQUEST_TIMEOUT


class BaseScraper(ABC):
    """스크래퍼 기본 클래스"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": USER_AGENT,
                "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            }
        )

    @abstractmethod
    def search(self, keyword: str, limit: int = 10) -> List[Candidate]:
        """
        키워드로 검색하여 후보 목록 반환

        Args:
            keyword: 검색 키워드
            limit: 반환할 최대 후보 개수

        Returns:
            Candidate 객체 리스트
        """
        pass

    @abstractmethod
    def fetch(self, product_url: str) -> Optional[PriceResult]:
        """
        특정 상품 URL에서 가격 정보 조회

        Args:
            product_url: 상품 페이지 URL

        Returns:
            PriceResult 객체 또는 None
        """
        pass

    def _get_html(self, url: str) -> Optional[BeautifulSoup]:
        """
        URL에서 HTML 가져오기 (공통 로직)

        Returns:
            BeautifulSoup 객체 또는 None
        """
        try:
            response = self.session.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            return BeautifulSoup(response.text, "lxml")
        except requests.RequestException as e:
            print(f"[ERROR] HTTP 요청 실패 ({url}): {e}")
            return None
        except Exception as e:
            print(f"[ERROR] HTML 파싱 실패: {e}")
            return None

    @abstractmethod
    def get_site_name(self) -> str:
        """사이트 이름 반환 (danawa | gmarket)"""
        pass
