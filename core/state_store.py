"""최소 상태 저장/로드 (JSON 기반)"""

import json
import os
from pathlib import Path
from typing import Optional
from core.models import TrackingState


class StateStore:
    """상태 저장소 (가격 히스토리는 저장하지 않음)"""

    def __init__(self, filepath: str = "data/state.json"):
        self.filepath = Path(filepath)
        self.filepath.parent.mkdir(parents=True, exist_ok=True)

    def save(self, state: TrackingState) -> bool:
        """상태 저장"""
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(state.to_dict(), f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"[ERROR] 상태 저장 실패: {e}")
            return False

    def load(self) -> Optional[TrackingState]:
        """상태 로드"""
        if not self.filepath.exists():
            return None
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            return TrackingState.from_dict(data)
        except Exception as e:
            print(f"[ERROR] 상태 로드 실패: {e}")
            return None

    def delete(self) -> bool:
        """상태 삭제"""
        try:
            if self.filepath.exists():
                os.remove(self.filepath)
            return True
        except Exception as e:
            print(f"[ERROR] 상태 삭제 실패: {e}")
            return False

    def exists(self) -> bool:
        """상태 파일 존재 여부"""
        return self.filepath.exists()
