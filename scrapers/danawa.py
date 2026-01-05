"""다나와 스크래퍼(실제 HTML 파싱 적용 완료)"""

from typing import List, Optional
from datetime import datetime
from urllib.parse import quote
import re

from scrapers.base import BaseScraper
from core.models import Candidate, PriceResult
from core.normalizer import Normalizer


class DanawaScraper(BaseScraper):
    """다나와 가격 비교 사이트 스크래퍼"""

    BASE_SEARCH_URL = "https://search.danawa.com/dsearch.php"

    def get_site_name(self) -> str:
        return "danawa"

    def search(self, keyword: str, limit: int = 10) -> List[Candidate]:
        """
        다나와 검색 결과 파싱 (실제 상품만)

        - ul.product_list > li.prod_item 중에서
        id가 productItem{숫자} 형태인 항목만 실제 상품으로 취급
        (adSmartAreaTop, adSmartAreaBottomB 같은 추천/광고 영역은 자동 제외)
        - 가격은 input#min_price_{pcode} 값 우선 사용
        """
        candidates: List[Candidate] = []
        search_url = f"{self.BASE_SEARCH_URL}?query={quote(keyword)}"
        soup = self._get_html(search_url)
        if not soup:
            return candidates

        # 실제 상품만: id="productItem123456" 형태만 허용
        product_id_pattern = re.compile(r"^productItem(\d+)$")

        items = soup.select("ul.product_list > li.prod_item")
        for item in items:
            if len(candidates) >= limit:
                break

            try:
                item_id = (item.get("id") or "").strip()
                m = product_id_pattern.match(item_id)

                # ✅ 광고/추천 영역(adSmartAreaTop 등) 및 기타 비상품 블록 제외
                if not m:
                    continue

                pcode = m.group(1)

                # 상품명/링크: p.prod_name > a (표준 상품 타이틀)
                link_elem = item.select_one("p.prod_name a")
                if not link_elem:
                    continue

                title_raw = link_elem.get_text(" ", strip=True)
                title = Normalizer.clean_title(title_raw)

                product_url = (link_elem.get("href") or "").strip()
                if not product_url:
                    continue
                # danawa는 보통 https://prod.danawa.com/info/?pcode=... 형태
                if product_url.startswith("//"):
                    product_url = "https:" + product_url

                # 최저가: hidden input의 min_price_{pcode} 값을 우선 사용
                price = None
                price_input = item.select_one(f"input#min_price_{pcode}")
                if price_input and price_input.get("value"):
                    v = price_input["value"].strip()
                    if v.isdigit():
                        price = int(v)
                    else:
                        # 혹시 쉼표/원 표기가 섞인 경우 대비
                        price = Normalizer.parse_price(v)
                else:
                    # fallback: 페이지에 표시된 가격 중 첫 번째 price_sect 사용
                    price_elem = item.select_one(
                        ".prod_pricelist .price_sect, .price_sect"
                    )
                    if price_elem:
                        price = Normalizer.parse_price(
                            price_elem.get_text(" ", strip=True)
                        )

                candidates.append(
                    Candidate(
                        site=self.get_site_name(),
                        title=title,
                        price=price,
                        product_url=product_url,
                    )
                )

            except Exception as e:
                print(f"[WARN] 다나와 후보 파싱 오류: {e}")
                continue

        return candidates

    def fetch(self, product_url: str) -> Optional[PriceResult]:
        """
        다나와 상품 상세 페이지에서 '쇼핑몰별 최저가'의 최저가(첫 항목/lowest 배지)를 가져온다.

        - ul.list__mall-price 내에서 .box__price.lowest(최저가 배지)가 있는 li를 우선 선택
        - 없으면 첫 번째 li를 fallback
        - price: .box__price .text__num
        - buy_link: a.link__full-cover[href]  (다나와 브릿지 링크)
        """
        soup = self._get_html(product_url)
        if not soup:
            return None

        try:
            # 1) 상품명 (페이지 구조가 변할 수 있어 여러 셀렉터를 시도)
            title_raw = ""
            title_elem = soup.select_one("h3.prod_tit, h1.prod_tit, .prod_tit")
            if title_elem:
                title_raw = title_elem.get_text(" ", strip=True)
            else:
                og = soup.select_one("meta[property='og:title']")
                if og and og.get("content"):
                    title_raw = og["content"].strip()

            title = Normalizer.clean_title(title_raw) if title_raw else ""

            # 2) 쇼핑몰별 최저가 리스트
            mall_items = soup.select("ul.list__mall-price > li.list-item")
            if not mall_items:
                return None

            # 2-1) '최저가' 표식이 있는 항목 우선 (.box__price.lowest / .badge__lowest)
            lowest_item = None
            for li in mall_items:
                if li.select_one(".box__price.lowest") or li.select_one(
                    ".badge__lowest"
                ):
                    lowest_item = li
                    break

            # 2-2) 없으면 첫 번째 항목 fallback (요구사항: 첫 항목이 최저가)
            target = lowest_item or mall_items[0]

            # 3) 가격 추출
            price_num = target.select_one(".box__price .text__num")
            if not price_num:
                return None
            price = Normalizer.parse_price(price_num.get_text(" ", strip=True))
            if price is None:
                return None

            # 4) 최저가 쇼핑몰 링크(브릿지 링크)
            link_elem = target.select_one("a.link__full-cover")
            buy_url = (link_elem.get("href") or "").strip() if link_elem else ""
            if buy_url.startswith("//"):
                buy_url = "https:" + buy_url

            # buy_url이 비어있으면 최소한 product_url이라도 남김
            final_url = buy_url if buy_url else product_url

            return PriceResult(
                site=self.get_site_name(),
                title=title,
                price=price,
                product_url=final_url,  # ✅ "구매 링크" 용도로 최저가 쇼핑몰 링크를 반환
                fetched_at=datetime.now().isoformat(),
            )

        except Exception as e:
            print(f"[ERROR] 다나와 가격 조회 실패: {e}")
            return None
