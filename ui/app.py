"""Tkinter 메인 UI"""

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Optional, Dict
from datetime import datetime

from ui.widgets import LabeledEntry, LabeledCombobox, CandidateListbox, StatusBar
from core.models import TrackingState, Candidate
from core.state_store import StateStore
from core.scheduler import Scheduler
from scrapers.danawa import DanawaScraper
from scrapers.gmarket import GmarketScraper
from notify.emailer import Emailer
from notify.templates import create_test_email
from config.constants import (
    CRAWL_INTERVALS,
    NOTIFY_INTERVALS,
    EMAIL_DOMAINS,
    DEFAULT_CRAWL_INTERVAL,
    DEFAULT_NOTIFY_INTERVAL,
    STATE_ACTIVE,
)


class PriceAlertApp:
    """최저가 알림이 메인 애플리케이션"""

    def __init__(self, root):
        self.root = root
        self.root.title("최저가 알림이")
        self.root.geometry("700x650")

        # 상태
        self.state_store = StateStore()
        self.scheduler: Optional[Scheduler] = None
        self.scrapers = {"danawa": DanawaScraper(), "gmarket": GmarketScraper()}
        self.emailer: Optional[Emailer] = None

        self._setup_ui()
        self._load_saved_state()

    def _setup_ui(self):
        """UI 구성"""
        # 메인 프레임
        main_frame = tk.Frame(self.root, padx=10, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # === 입력 섹션 ===
        input_frame = tk.LabelFrame(main_frame, text="크롤링 설정", padx=10, pady=10)
        input_frame.pack(fill=tk.X, pady=5)

        # 키워드
        self.keyword_entry = LabeledEntry(input_frame, "상품 키워드:", width=40)
        self.keyword_entry.pack(fill=tk.X, pady=3)

        # 사이트 선택
        self.site_combo = LabeledCombobox(
            input_frame, "사이트 선택:", values=["다나와", "지마켓", "둘 다"]
        )
        self.site_combo.pack(fill=tk.X, pady=3)

        # 크롤링 주기
        crawl_labels = [f"{m}분" if m < 60 else f"{m//60}시간" for m in CRAWL_INTERVALS]
        self.crawl_interval_combo = LabeledCombobox(
            input_frame, "크롤링 주기:", values=crawl_labels
        )
        self.crawl_interval_combo.set("30분")
        self.crawl_interval_combo.pack(fill=tk.X, pady=3)

        # 알림 주기
        notify_labels = []
        for m in NOTIFY_INTERVALS:
            if m < 60:
                notify_labels.append(f"{m}분")
            elif m < 1440:
                notify_labels.append(f"{m//60}시간")
            else:
                notify_labels.append(f"{m//1440}일")

        self.notify_interval_combo = LabeledCombobox(
            input_frame, "알림 주기:", values=notify_labels
        )
        self.notify_interval_combo.set("24시간")
        self.notify_interval_combo.pack(fill=tk.X, pady=3)

        # 이메일 (로컬파트 + 도메인)
        email_frame = tk.Frame(input_frame)
        email_frame.pack(fill=tk.X, pady=3)

        tk.Label(email_frame, text="수신 이메일:", width=12, anchor="w").pack(
            side=tk.LEFT, padx=5
        )
        self.email_local_entry = tk.Entry(email_frame, width=20)
        self.email_local_entry.pack(side=tk.LEFT, padx=5)

        tk.Label(email_frame, text="@").pack(side=tk.LEFT)

        self.email_domain_combo = ttk.Combobox(
            email_frame, values=EMAIL_DOMAINS, state="readonly", width=15
        )
        self.email_domain_combo.current(0)
        self.email_domain_combo.pack(side=tk.LEFT, padx=5)

        # 검색 버튼
        self.search_btn = tk.Button(
            input_frame,
            text="검색/후보 가져오기",
            command=self._search_candidates,
            bg="lightblue",
        )
        self.search_btn.pack(fill=tk.X, pady=5)

        # === 후보 리스트 섹션 ===
        candidate_frame = tk.LabelFrame(
            main_frame, text="검색 결과 (선택 후 크롤링 시작)", padx=10, pady=10
        )
        candidate_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.candidate_list = CandidateListbox(candidate_frame)
        self.candidate_list.pack(fill=tk.BOTH, expand=True)

        # === 제어 버튼 ===
        control_frame = tk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=5)

        self.start_btn = tk.Button(
            control_frame,
            text="추적 시작",
            command=self._start_tracking,
            bg="lightgreen",
            width=15,
        )
        self.start_btn.pack(side=tk.LEFT, padx=5)

        self.stop_btn = tk.Button(
            control_frame,
            text="중지",
            command=self._stop_tracking,
            bg="salmon",
            width=15,
            state="disabled",
        )
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        self.test_email_btn = tk.Button(
            control_frame, text="테스트 알림", command=self._send_test_email, width=15
        )
        self.test_email_btn.pack(side=tk.LEFT, padx=5)

        # === 상태 표시 ===
        status_frame = tk.LabelFrame(main_frame, text="현재 상태", padx=10, pady=10)
        status_frame.pack(fill=tk.X, pady=5)

        self.status_text = tk.Text(status_frame, height=5, state="disabled")
        self.status_text.pack(fill=tk.X)

        # === 하단 상태바 ===
        self.status_bar = StatusBar(self.root)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _search_candidates(self):
        """후보 검색"""
        keyword = self.keyword_entry.get().strip()
        if not keyword:
            messagebox.showwarning("입력 오류", "키워드를 입력하세요.")
            return

        self.status_bar.set_status("검색 중...", "blue")
        self.candidate_list.clear()

        # 사이트 선택 변환
        site_selection = self.site_combo.get()
        sites = []
        if site_selection == "다나와":
            sites = ["danawa"]
        elif site_selection == "지마켓":
            sites = ["gmarket"]
        else:
            sites = ["danawa", "gmarket"]

        # 검색 실행
        all_candidates = []
        for site in sites:
            scraper = self.scrapers.get(site)
            if scraper:
                try:
                    candidates = scraper.search(keyword, limit=10)
                    all_candidates.extend(candidates)
                except Exception as e:
                    messagebox.showerror("검색 오류", f"{site} 검색 실패: {e}")

        if not all_candidates:
            messagebox.showinfo(
                "검색 결과", "검색 결과가 없습니다.\n키워드를 수정해주세요."
            )
            self.status_bar.set_status("검색 결과 없음", "orange")
            return

        self.candidate_list.add_candidates(all_candidates)
        self.status_bar.set_status(f"{len(all_candidates)}개 후보 검색 완료", "green")

    def _start_tracking(self):
        """추적 시작"""
        # 선택 검증
        selected = self.candidate_list.get_selected()
        if not selected:
            messagebox.showwarning("선택 오류", "추적할 상품을 선택하세요.")
            return

        # 이메일 검증
        email_local = self.email_local_entry.get().strip()
        email_domain = self.email_domain_combo.get()

        if not email_local:
            messagebox.showwarning("입력 오류", "이메일 주소를 입력하세요.")
            return

        email = f"{email_local}@{email_domain}"

        if not Emailer.validate_email(email):
            messagebox.showerror("입력 오류", "유효하지 않은 이메일 주소입니다.")
            return

        # 주기 파싱
        crawl_interval = self._parse_interval(
            self.crawl_interval_combo.get(), CRAWL_INTERVALS
        )
        notify_interval = self._parse_interval(
            self.notify_interval_combo.get(), NOTIFY_INTERVALS
        )

        # 상태 생성
        keyword = self.keyword_entry.get().strip()
        state = TrackingState(
            keyword=keyword,
            selected_sites=[selected.site],
            crawl_interval=crawl_interval,
            notify_interval=notify_interval,
            email=email,
            selected_products={selected.site: selected.product_url},
            last_prices={},
            last_crawl_at=None,
            last_notify_at=None,
            status=STATE_ACTIVE,
        )

        # 발신자 이메일 설정 (간단한 다이얼로그)
        sender_info = self._get_sender_credentials()
        if not sender_info:
            return

        try:
            self.emailer = Emailer(sender_info[0], sender_info[1])
        except ValueError as e:
            messagebox.showerror("설정 오류", str(e))
            return

        # 스케줄러 시작
        self.scheduler = Scheduler(
            state=state,
            state_store=self.state_store,
            scrapers=self.scrapers,
            emailer=self.emailer,
            on_status_change=self._update_status_display,
        )

        self.scheduler.start()
        self.state_store.save(state)

        # UI 업데이트
        self._set_tracking_mode(True)
        self.status_bar.set_active()
        self._update_status_display(state)

    def _stop_tracking(self):
        """추적 중지"""
        if self.scheduler:
            self.scheduler.stop()
            self.scheduler = None

        self._set_tracking_mode(False)
        self.status_bar.set_idle()

    def _send_test_email(self):
        """테스트 이메일 발송"""
        email_local = self.email_local_entry.get().strip()
        email_domain = self.email_domain_combo.get()

        if not email_local:
            messagebox.showwarning("입력 오류", "이메일 주소를 입력하세요.")
            return

        recipient = f"{email_local}@{email_domain}"

        sender_info = self._get_sender_credentials()
        if not sender_info:
            return

        try:
            emailer = Emailer(sender_info[0], sender_info[1])
            subject, body = create_test_email()

            if emailer.send(recipient, subject, body):
                messagebox.showinfo("성공", "테스트 이메일이 발송되었습니다.")
            else:
                messagebox.showerror("실패", "이메일 발송에 실패했습니다.")

        except Exception as e:
            messagebox.showerror("오류", f"이메일 설정 오류: {e}")

    def _get_sender_credentials(self) -> Optional[tuple]:
        """발신자 이메일 정보 입력 다이얼로그"""
        dialog = tk.Toplevel(self.root)
        dialog.title("발신자 이메일 설정")
        dialog.geometry("400x200")
        dialog.transient(self.root)
        dialog.grab_set()

        result = [None]

        tk.Label(dialog, text="발신자 이메일 (앱 비밀번호 사용)").pack(pady=10)

        email_entry = LabeledEntry(dialog, "이메일:", width=30)
        email_entry.pack(pady=5, padx=20, fill=tk.X)

        password_entry = LabeledEntry(dialog, "앱 비밀번호:", width=30)
        password_entry.entry.config(show="*")
        password_entry.pack(pady=5, padx=20, fill=tk.X)

        def on_ok():
            email = email_entry.get().strip()
            password = password_entry.get().strip()

            if email and password:
                result[0] = (email, password)
                dialog.destroy()
            else:
                messagebox.showwarning("입력 오류", "모든 항목을 입력하세요.")

        tk.Button(dialog, text="확인", command=on_ok).pack(pady=10)

        dialog.wait_window()
        return result[0]

    def _parse_interval(self, label: str, values: list) -> int:
        """주기 레이블을 분 단위로 변환"""
        for i, val in enumerate(values):
            if label.startswith(str(val)):
                return val
            if val >= 60 and label.startswith(str(val // 60)):
                return val
            if val >= 1440 and label.startswith(str(val // 1440)):
                return val
        return values[0]

    def _set_tracking_mode(self, tracking: bool):
        """추적 모드 UI 전환"""
        if tracking:
            self.start_btn.config(state="disabled")
            self.stop_btn.config(state="normal")
            self.search_btn.config(state="disabled")
        else:
            self.start_btn.config(state="normal")
            self.stop_btn.config(state="disabled")
            self.search_btn.config(state="normal")

    def _update_status_display(self, state: TrackingState):
        """상태 표시 업데이트"""
        self.status_text.config(state="normal")
        self.status_text.delete("1.0", tk.END)

        info = f"""
키워드: {state.keyword}
상태: {state.status}
마지막 조회: {state.last_crawl_at or '없음'}
마지막 알림: {state.last_notify_at or '없음'}
추적 사이트: {', '.join(state.selected_sites)}
        """.strip()

        self.status_text.insert("1.0", info)
        self.status_text.config(state="disabled")

    def _load_saved_state(self):
        """저장된 상태 로드 (재시작용)"""
        # 간단한 구현: 저장된 상태 표시만
        if self.state_store.exists():
            state = self.state_store.load()
            if state:
                self._update_status_display(state)

    def run(self):
        """앱 실행"""
        self.root.mainloop()
