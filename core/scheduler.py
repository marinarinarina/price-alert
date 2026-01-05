"""크롤링/알림 주기 실행기 (백오프, 지터 포함)"""

import time
import random
import threading
from datetime import datetime, timedelta
from typing import Optional, Callable, List
from core.models import TrackingState, PriceResult
from core.state_store import StateStore
from core.normalizer import Normalizer
from config.constants import (
    JITTER_MIN,
    JITTER_MAX,
    BACKOFF_DELAYS,
    STATE_ACTIVE,
    STATE_NEEDS_CONFIRMATION,
    STATE_BLOCKED_SUSPECTED,
)


class Scheduler:
    """주기 실행 스케줄러"""

    def __init__(
        self,
        state: TrackingState,
        state_store: StateStore,
        scrapers: dict,  # {site: scraper}
        emailer,
        on_status_change: Optional[Callable] = None,
    ):
        """
        Args:
            state: 추적 상태
            state_store: 상태 저장소
            scrapers: 사이트별 스크래퍼 딕셔너리
            emailer: 이메일 발송기
            on_status_change: 상태 변경 콜백 (UI 업데이트용)
        """
        self.state = state
        self.state_store = state_store
        self.scrapers = scrapers
        self.emailer = emailer
        self.on_status_change = on_status_change

        self.running = False
        self.thread: Optional[threading.Thread] = None

        # 다음 실행 시각 계산
        self.next_crawl_at = datetime.now()
        self.next_notify_at = datetime.now()

    def start(self):
        """스케줄러 시작"""
        if self.running:
            print("[WARN] 스케줄러가 이미 실행 중입니다.")
            return

        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        print("[INFO] 스케줄러 시작")

    def stop(self):
        """스케줄러 중지"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        print("[INFO] 스케줄러 중지")

    def _run_loop(self):
        """메인 루프"""
        while self.running:
            now = datetime.now()

            # 크롤링 실행 시각 체크
            if now >= self.next_crawl_at:
                self._crawl_tick()
                self._schedule_next_crawl()

            # 알림 실행 시각 체크
            if now >= self.next_notify_at:
                self._notify_tick()
                self._schedule_next_notify()

            # 1초 대기
            time.sleep(1)

    def _crawl_tick(self):
        """크롤링 실행"""
        # 지터 적용 (랜덤 지연)
        jitter = random.uniform(JITTER_MIN, JITTER_MAX)
        time.sleep(jitter)

        print(f"[INFO] 크롤링 시작 (지터: {jitter:.1f}초)")

        results: List[PriceResult] = []

        for site, product_url in self.state.selected_products.items():
            scraper = self.scrapers.get(site)
            if not scraper:
                continue

            try:
                result = scraper.fetch(product_url)

                if result:
                    results.append(result)
                    self._validate_result(site, result)
                else:
                    self._handle_fetch_failure(site)

            except Exception as e:
                print(f"[ERROR] 크롤링 오류 ({site}): {e}")
                self._handle_fetch_failure(site)

        # 결과 저장
        if results:
            for result in results:
                self.state.update_price(result.site, result.price)

            self.state.reset_backoff()
            self.state_store.save(self.state)

            if self.on_status_change:
                self.on_status_change(self.state)

    def _validate_result(self, site: str, result: PriceResult):
        """결과 검증 (오매칭 감지)"""
        old_price = self.state.last_prices.get(site)

        # 가격 급변 체크
        if old_price and Normalizer.check_abnormal_price_change(
            old_price, result.price
        ):
            print(f"[WARN] 가격 급변 감지 ({site}): {old_price} → {result.price}")
            self.state.status = STATE_NEEDS_CONFIRMATION
            self.state_store.save(self.state)

            if self.on_status_change:
                self.on_status_change(self.state)

    def _handle_fetch_failure(self, site: str):
        """크롤링 실패 처리"""
        self.state.increment_backoff()

        # 백오프 카운트가 임계값을 넘으면 차단 의심
        if self.state.backoff_count >= len(BACKOFF_DELAYS):
            self.state.status = STATE_BLOCKED_SUSPECTED
            print(f"[WARN] 차단 의심 ({site})")

        self.state_store.save(self.state)

        if self.on_status_change:
            self.on_status_change(self.state)

    def _notify_tick(self):
        """알림 발송"""
        # 상태가 정상이 아니면 알림 스킵
        if self.state.status != STATE_ACTIVE:
            print(f"[INFO] 상태 비정상 ({self.state.status}), 알림 스킵")
            return

        # 최신 가격 결과 수집
        results = []
        for site, url in self.state.selected_products.items():
            price = self.state.last_prices.get(site)
            if price:
                # 임시로 PriceResult 생성 (실제 제목은 저장된 것 사용)
                results.append(
                    PriceResult(
                        site=site,
                        title=f"{self.state.keyword} ({site})",
                        price=price,
                        product_url=url,
                        fetched_at=self.state.last_crawl_at
                        or datetime.now().isoformat(),
                    )
                )

        if not results:
            print("[WARN] 알림할 가격 정보 없음")
            return

        # 이메일 발송
        from notify.templates import create_price_alert_email

        subject, body = create_price_alert_email(self.state.keyword, results)

        success = self.emailer.send(self.state.email, subject, body)

        if success:
            self.state.update_notify()
            self.state_store.save(self.state)
            print("[INFO] 알림 발송 완료")

    def _schedule_next_crawl(self):
        """다음 크롤링 시각 계산"""
        # 백오프 적용
        delay_minutes = self.state.crawl_interval

        if self.state.backoff_count > 0:
            backoff_idx = min(self.state.backoff_count - 1, len(BACKOFF_DELAYS) - 1)
            delay_minutes = BACKOFF_DELAYS[backoff_idx]
            print(f"[INFO] 백오프 적용: {delay_minutes}분 대기")

        self.next_crawl_at = datetime.now() + timedelta(minutes=delay_minutes)

    def _schedule_next_notify(self):
        """다음 알림 시각 계산"""
        self.next_notify_at = datetime.now() + timedelta(
            minutes=self.state.notify_interval
        )
