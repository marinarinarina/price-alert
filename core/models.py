"""데이터 모델 정의"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Candidate:
    """검색 후보 상품"""

    site: str  # danawa | gmarket
    title: str
    price: Optional[int]  # 가격 없을 수도 있음
    product_url: str

    def to_dict(self):
        return {
            "site": self.site,
            "title": self.title,
            "price": self.price,
            "product_url": self.product_url,
        }


@dataclass
class PriceResult:
    """가격 조회 결과"""

    site: str
    title: str
    price: int
    product_url: str
    fetched_at: str  # ISO 8601 형식

    def to_dict(self):
        return {
            "site": self.site,
            "title": self.title,
            "price": self.price,
            "product_url": self.product_url,
            "fetched_at": self.fetched_at,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(**data)


@dataclass
class TrackingState:
    """추적 상태 (최소 상태만 저장)"""

    keyword: str
    selected_sites: list  # ["danawa", "gmarket"]
    crawl_interval: int  # minutes
    notify_interval: int  # minutes
    email: str

    # 사이트별 선택된 상품 URL
    selected_products: dict  # {site: url}

    # 최소 상태
    last_prices: dict  # {site: price}
    last_crawl_at: Optional[str]  # ISO 8601
    last_notify_at: Optional[str]  # ISO 8601

    status: str  # active | not_found | needs_confirmation | blocked_suspected
    backoff_count: int = 0  # 재시도 카운트

    def to_dict(self):
        return {
            "keyword": self.keyword,
            "selected_sites": self.selected_sites,
            "crawl_interval": self.crawl_interval,
            "notify_interval": self.notify_interval,
            "email": self.email,
            "selected_products": self.selected_products,
            "last_prices": self.last_prices,
            "last_crawl_at": self.last_crawl_at,
            "last_notify_at": self.last_notify_at,
            "status": self.status,
            "backoff_count": self.backoff_count,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(**data)

    def update_price(self, site: str, price: int):
        """가격 업데이트"""
        self.last_prices[site] = price
        self.last_crawl_at = datetime.now().isoformat()

    def update_notify(self):
        """알림 시각 업데이트"""
        self.last_notify_at = datetime.now().isoformat()

    def reset_backoff(self):
        """백오프 카운트 초기화"""
        self.backoff_count = 0

    def increment_backoff(self):
        """백오프 카운트 증가"""
        self.backoff_count += 1
