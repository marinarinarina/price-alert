"""지마켓 스크래퍼 (실제 구현 필요)"""

from typing import List, Optional
from datetime import datetime
from urllib.parse import quote
from scrapers.base import BaseScraper
from core.models import Candidate, PriceResult
from core.normalizer import Normalizer


class GmarketScraper(BaseScraper):
    """지마켓 스크래퍼"""

    BASE_SEARCH_URL = "https://browse.gmarket.co.kr/search"

    def get_site_name(self) -> str:
        return "gmarket"

    def search(self, keyword: str, limit: int = 10) -> List[Candidate]:
        """
        지마켓 검색 결과 파싱

        TODO: 실제 지마켓 HTML 구조에 맞게 구현 필요
        """
        candidates = []

        # 검색 URL 생성
        search_url = f"{self.BASE_SEARCH_URL}?keyword={quote(keyword)}"

        # HTML 가져오기
        soup = self._get_html(search_url)
        if not soup:
            return candidates

        # TODO: 실제 셀렉터로 교체
        items = soup.select(".box__item-container")[:limit]

        for item in items:
            try:
                # TODO: 실제 셀렉터로 교체
                title_elem = item.select_one(".link__item")
                price_elem = item.select_one(".box__price-seller strong")
                link_elem = item.select_one("a.link__item")

                if not all([title_elem, link_elem]):
                    continue

                title = Normalizer.clean_title(title_elem.get_text(strip=True))
                price = None
                if price_elem:
                    price = Normalizer.parse_price(price_elem.get_text(strip=True))

                product_url = link_elem.get("href", "")
                if product_url and not product_url.startswith("http"):
                    product_url = f"https://item.gmarket.co.kr{product_url}"

                candidates.append(
                    Candidate(
                        site=self.get_site_name(),
                        title=title,
                        price=price,
                        product_url=product_url,
                    )
                )

            except Exception as e:
                print(f"[WARN] 지마켓 후보 파싱 오류: {e}")
                continue

        return candidates

    def fetch(self, product_url: str) -> Optional[PriceResult]:
        """
        지마켓 상품 페이지에서 가격 조회

        TODO: 실제 지마켓 상품 페이지 구조에 맞게 구현
        """
        soup = self._get_html(product_url)
        if not soup:
            return None

        try:
            # TODO: 실제 셀렉터로 교체
            title_elem = soup.select_one(".itemtit")
            price_elem = soup.select_one(".price_innerwrap strong")

            if not all([title_elem, price_elem]):
                return None

            title = Normalizer.clean_title(title_elem.get_text(strip=True))
            price = Normalizer.parse_price(price_elem.get_text(strip=True))

            if price is None:
                return None

            return PriceResult(
                site=self.get_site_name(),
                title=title,
                price=price,
                product_url=product_url,
                fetched_at=datetime.now().isoformat(),
            )

        except Exception as e:
            print(f"[ERROR] 지마켓 가격 조회 실패: {e}")
            return None


# 주의: 위 코드는 스켈레톤입니다.
# 실제 지마켓 사이트 HTML 구조를 분석하여 셀렉터를 수정해야 합니다.
