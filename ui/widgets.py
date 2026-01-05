"""공통 UI 위젯"""

import tkinter as tk
from tkinter import ttk
from typing import List, Callable, Optional
from core.models import Candidate


class LabeledEntry(tk.Frame):
    """레이블이 있는 입력 필드"""

    def __init__(self, parent, label_text: str, **kwargs):
        super().__init__(parent)

        self.label = tk.Label(self, text=label_text, width=12, anchor="w")
        self.label.pack(side=tk.LEFT, padx=5)

        self.entry = tk.Entry(self, **kwargs)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

    def get(self) -> str:
        return self.entry.get()

    def set(self, value: str):
        self.entry.delete(0, tk.END)
        self.entry.insert(0, value)

    def disable(self):
        self.entry.config(state="disabled")

    def enable(self):
        self.entry.config(state="normal")


class LabeledCombobox(tk.Frame):
    """레이블이 있는 콤보박스"""

    def __init__(self, parent, label_text: str, values: List[str], **kwargs):
        super().__init__(parent)

        self.label = tk.Label(self, text=label_text, width=12, anchor="w")
        self.label.pack(side=tk.LEFT, padx=5)

        self.combobox = ttk.Combobox(self, values=values, state="readonly", **kwargs)
        self.combobox.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        if values:
            self.combobox.current(0)

    def get(self) -> str:
        return self.combobox.get()

    def set(self, value: str):
        self.combobox.set(value)

    def disable(self):
        self.combobox.config(state="disabled")

    def enable(self):
        self.combobox.config(state="readonly")


class CandidateListbox(tk.Frame):
    """후보 선택 리스트박스"""

    def __init__(self, parent, on_select: Optional[Callable] = None):
        super().__init__(parent)

        # 스크롤바
        scrollbar = tk.Scrollbar(self)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 리스트박스
        self.listbox = tk.Listbox(
            self, height=10, selectmode=tk.SINGLE, yscrollcommand=scrollbar.set
        )
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.listbox.yview)

        # 선택 이벤트
        if on_select:
            self.listbox.bind("<<ListboxSelect>>", lambda e: on_select())

        self.candidates: List[Candidate] = []

    def clear(self):
        """리스트 초기화"""
        self.listbox.delete(0, tk.END)
        self.candidates = []

    def add_candidates(self, candidates: List[Candidate]):
        """후보 추가"""
        self.candidates = candidates
        self.listbox.delete(0, tk.END)

        for i, candidate in enumerate(candidates):
            price_text = (
                f"{candidate.price:,}원" if candidate.price else "가격 정보 없음"
            )
            display_text = f"[{candidate.site}] {candidate.title} - {price_text}"
            self.listbox.insert(tk.END, display_text)

    def get_selected(self) -> Optional[Candidate]:
        """선택된 후보 반환"""
        selection = self.listbox.curselection()
        if not selection:
            return None

        index = selection[0]
        return self.candidates[index] if index < len(self.candidates) else None

    def get_all_selected_by_site(self) -> dict:
        """사이트별로 선택된 후보 반환 (다중 선택용)"""
        # 현재는 단일 선택만 지원
        selected = self.get_selected()
        if selected:
            return {selected.site: selected}
        return {}


class StatusBar(tk.Frame):
    """상태 표시줄"""

    def __init__(self, parent):
        super().__init__(parent, relief=tk.SUNKEN, bd=1)

        self.label = tk.Label(self, text="준비", anchor="w")
        self.label.pack(fill=tk.X, padx=5, pady=2)

    def set_status(self, text: str, color: str = "black"):
        """상태 텍스트 설정"""
        self.label.config(text=text, fg=color)

    def set_active(self):
        self.set_status("추적 중...", "green")

    def set_idle(self):
        self.set_status("준비", "black")

    def set_error(self, message: str):
        self.set_status(f"오류: {message}", "red")

    def set_warning(self, message: str):
        self.set_status(f"경고: {message}", "orange")
