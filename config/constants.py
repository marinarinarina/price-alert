"""프로그램 전역 상수 정의"""

# 크롤링 주기 선택지 (분 단위, 최소 15분)
CRAWL_INTERVALS = [1, 15, 30, 60, 120, 240, 480, 720, 1440]

# 알림 주기 선택지 (분 단위, 1시간~1주)
NOTIFY_INTERVALS = [1, 60, 180, 360, 720, 1440, 4320, 10080]

# 이메일 도메인 제한
EMAIL_DOMAINS = ["gmail.com", "naver.com"]

# 기본값
DEFAULT_CRAWL_INTERVAL = 30  # 기본: 30분, 테스트: 1분
DEFAULT_NOTIFY_INTERVAL = 1440  # 24시간
DEFAULT_CANDIDATE_COUNT = 10  # 검색 결과 후보 개수

# 지터 설정 (초 단위)
JITTER_MIN = 0
JITTER_MAX = 20

# 백오프 설정 (분 단위)
BACKOFF_DELAYS = [1, 5, 15]  # 1분 → 5분 → 15분 → 다음 주기

# 오매칭 감지 임계값
PRICE_CHANGE_THRESHOLD = 0.30  # ±30%
TOKEN_MISMATCH_THRESHOLD = 0.5  # 핵심 토큰 50% 이상 불일치

# 상태 코드
STATE_ACTIVE = "active"
STATE_NOT_FOUND = "not_found"
STATE_NEEDS_CONFIRMATION = "needs_confirmation"
STATE_BLOCKED_SUSPECTED = "blocked_suspected"

# User-Agent (봇 차단 완화)
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

# 타임아웃 (초)
REQUEST_TIMEOUT = 15
