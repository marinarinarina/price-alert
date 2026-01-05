# module-overview (모듈 개요)

## 1) UI (Tkinter)
- 사용자가 키워드/사이트/주기/이메일을 입력·선택하고, 검색 후보를 확인(2-step)한 뒤 추적을 시작/중지한다.
- 입력값 검증(주기 최소값, 이메일 도메인 제한 등)과 상태 표시(정상/검색없음/재확인필요/차단의심)를 담당한다.

## 2) Scheduler (주기 실행기)
- 크롤링 주기(최소 15분) 및 알림 주기(최소 1시간~최대 1주)를 기반으로 작업을 실행한다.
- 크롤링 작업과 알림 작업을 분리하여, “크롤링은 자주 / 알림은 덜 자주”가 가능하도록 한다.
- 실패 시 재시도(backoff) 및 지터(jitter: 작은 랜덤 지연)를 적용한다.

## 3) Scraper (사이트별 크롤러/파서)
- 사이트별 검색 결과를 가져오고(키워드→후보 N개), 사용자 선택 항목을 추적(선택된 상품 URL 기반)한다.
- DanawaScraper / GmarketScraper 두 어댑터로 분리하며, 공통 스키마로 정규화한다.

## 4) Normalizer (정규화/검증)
- 사이트별 결과를 공통 형식으로 통일한다.
- 오매칭 방지용 핵심 토큰 규칙(스펙 토큰 포함 여부 등)과 이상징후(가격 급변/상품명 변경)를 판정한다.

## 5) Notifier (이메일 알림)
- 사용자가 입력한 수신 이메일로 최저가+링크 요약을 발송한다.
- MVP는 SMTP 기반(예: 앱 비밀번호)으로 구성한다.
- 도메인은 UI에서 gmail.com / naver.com만 선택 가능하게 제한한다.

## 6) State Store (최소 상태 저장)
- 대규모 가격 스냅샷을 누적 저장하지 않는다.
- 알림/재확인/쿨다운을 위해 “최소 상태”만 로컬 파일로 저장한다.
  - 예: 선택된 상품 URL, 마지막 가격, 마지막 알림 시각, 사용자 설정값, 상태(active/needs_confirmation 등)


# feature-requirements (기능 요구사항)

## A. 입력/설정 (Tkinter UI)
1) 키워드 입력
- 필수 입력. 공백/특수문자 처리 등 기본 정제 수행.

2) 사이트 선택
- danawa / gmarket / both 중 선택.

3) 크롤링 주기 선택 (자유 입력 금지)
- 드롭다운 고정 선택지 제공.
- 최소 15분 강제 (차단 리스크 완화 목적).
- 기본값: 30분(권장).

권장 선택지(예):
- 15m, 30m, 1h, 2h, 4h, 8h, 12h, 24h

4) 알림 주기 선택 (자유 입력 금지)
- 드롭다운 고정 선택지 제공.
- 최소 1시간 ~ 최대 1주.
- 기본값: 24시간(권장).

권장 선택지(예):
- 1h, 3h, 6h, 12h, 24h, 3d, 7d

5) 이메일 입력 (도메인 제한)
- 로컬파트(예: user123) 입력 + 도메인 선택(gmail.com / naver.com)으로 구성.
- 최종 수신 주소는 `${local}@${domain}` 형태로 조합.
- 잘못된 문자(공백, @ 포함 등) 검증 및 에러 안내.

6) 버튼/동작
- [검색/후보 가져오기] : 사이트별 Top N 후보 조회 후 리스트 표시
- [추적 시작] : 후보 중 선택된 항목(상품 URL) 기준으로 주기 추적 시작
- [중지] : 스케줄러 중지 및 상태 유지
- [테스트 알림] : 이메일 설정 정상 여부 확인(샌드박스 메시지)

7) 상태 표시
- 마지막 조회 시각, 마지막 가격, 마지막 알림 시각, 현재 상태(active/not_found/needs_confirmation/blocked_suspected)

---

## B. 2-step 등록(오타/오매칭 방지)
1) 후보 조회
- 키워드로 검색하여 후보 N개(기본 5~10개)를 표시한다.
- 표시 항목: 상품명, 가격(가능 시), 링크(열기), 사이트

2) 사용자 선택
- 사용자는 후보 리스트에서 1개(또는 사이트별 1개) 선택 후 추적 시작한다.
- 선택 이후 추적은 “키워드”가 아닌 “선택된 상품 URL”을 기본 식별자로 사용한다.

3) 검색 결과 없음 처리
- 결과 0건이면 명확히 안내하고, 키워드 수정 가이드를 표시한다.
- (확장) URL 등록 모드 제공 가능.

---

## C. 크롤링/가격 조회
1) 조회 로직 우선순위
- 1차: HTTP 요청 + HTML 파싱으로 가격/링크 추출
- 2차: 동적 렌더링 필요 시 Headless(Playwright)로 확장(옵션)

2) 공통 출력 스키마(정규화)
- site: danawa|gmarket
- title: 상품명
- price: 정수(원화 기준)
- product_url: 구매 링크
- fetched_at: 조회 시각(로컬 타임존)

3) 차단(악성봇 오인) 리스크 완화
- 크롤링 주기는 최소 15분.
- 요청 전 지터(0~20초 랜덤 지연) 적용.
- 실패 시 즉시 연타 금지: backoff 재시도(1m → 5m → 15m → 다음 주기).

---

## D. 오매칭/이상징후 감지 및 재확인
1) 재확인(needs_confirmation) 트리거 예시
- 상품명 핵심 토큰 불일치 증가
- 가격이 비정상적으로 급변(예: ±30%)
- 품절/차단/오류 페이지로 변경(403/캡차 의심/리다이렉트 등)

2) 재확인 처리
- 알림 대신 “재확인 필요” 상태로 전환
- UI에서 후보 재조회/재선택 흐름을 제공

---

## E. 알림(이메일)
1) 알림 방식
- 알림 주기마다 “최신 최저가 요약”을 발송(MVP).
- (확장) 목표가 이하/하락폭 이상 즉시 알림 추가 가능.

2) 알림 메시지 내용
- 상품명, 사이트, 현재 최저가, 링크, 조회 시각

3) 스팸 방지
- 동일 내용 반복 알림은 최소 1회/알림주기 단위로 제한
- 상태 오류(차단/재확인 필요)도 알림주기 이상 간격으로만 발송

---

## F. 저장 정책(최소 상태만)
- 가격 스냅샷을 장기 누적 저장하지 않는다.
- 저장 허용 범위(최소 상태):
  - 사용자 설정(주기/이메일/사이트)
  - 선택된 상품 URL/상품명
  - 마지막 가격/마지막 조회 시각/마지막 알림 시각
  - 상태(active/not_found/needs_confirmation/blocked_suspected)


# relevant-codes (관련 코드)

## 1) 주기 선택지(고정 값)
- CRAWL_INTERVALS = [15, 30, 60, 120, 240, 480, 720, 1440]  # minutes
- NOTIFY_INTERVALS = [60, 180, 360, 720, 1440, 4320, 10080] # minutes

## 2) 이메일 입력(도메인 제한)
- EMAIL_DOMAINS = ["gmail.com", "naver.com"]
- email = f"{local_part}@{domain}"

## 3) 스케줄러(개념 코드)
- next_crawl_at, next_notify_at을 분리 관리
- crawl_tick():
    - sleep(jitter)
    - try fetch_price()
    - on fail: backoff
- notify_tick():
    - if now >= next_notify_at: send_email()

## 4) 스크래퍼 인터페이스(어댑터 패턴)
- class BaseScraper:
    - search(keyword) -> list[Candidate]
    - fetch(product_url) -> PriceResult

## 5) 정규화 스키마
- Candidate: {site, title, price?, product_url}
- PriceResult: {site, title, price, product_url, fetched_at}


# file-instruction (파일 구조)

price-alert/
  README.md
  requirements.txt
  main.py                      # 프로그램 엔트리: UI 실행
  config/
    constants.py               # 주기 선택지, 도메인 제한, 기본값
  ui/
    app.py                     # Tkinter 메인 윈도우/위젯/이벤트 핸들러
    widgets.py                 # 공통 위젯(드롭다운/리스트/상태바 등)
  core/
    scheduler.py               # 크롤링/알림 주기 실행, backoff/jitter
    models.py                  # Candidate/PriceResult/State 모델
    normalizer.py              # 가격 파싱, 토큰 추출, 이상징후 감지
    state_store.py             # 최소 상태 저장(JSON/SQLite)
  scrapers/
    base.py                    # BaseScraper 인터페이스
    danawa.py                  # DanawaScraper (검색/파싱)
    gmarket.py                 # GmarketScraper (검색/파싱)
  notify/
    emailer.py                 # SMTP 이메일 발송
    templates.py               # 이메일 템플릿(제목/본문)
  logs/
    app.log                    # 실행 로그(로테이션 권장)
  data/
    state.json                 # 최소 상태 저장 파일(누적가격 저장 금지)

※ 저장 정책상 data/에는 state.json만 두고, 가격 히스토리/CSV 누적 저장은 하지 않는다.


# rules (규칙)

1) API 사용 불가 → 크롤링 기반으로만 구현한다.
2) 자동 구매/결제/로그인 자동화는 구현하지 않는다.
3) 사용자 입력 주기값은 자유 입력 금지. UI 드롭다운 선택만 허용한다.
   - 크롤링 주기: 최소 15분
   - 알림 주기: 최소 1시간 ~ 최대 1주
4) 이메일 도메인은 UI에서 gmail.com / naver.com만 제공한다.
5) 오타/미존재/오매칭 방지를 위해 “2-step 등록(후보 조회 → 사용자 선택)”을 필수로 한다.
6) 추적 기준은 키워드가 아니라 “선택된 상품 URL”을 우선으로 한다.
7) 사이트가 프로그램을 악성봇으로 오인해 차단할 수 있으므로,
   - 지터(랜덤 지연), 백오프(잠시 쉬었다 재시도), 조회 빈도 제한을 적용한다.
8) 가격 데이터는 장기 저장/재판매/분석 목적의 누적 저장을 하지 않는다.
   - 알림/운영을 위한 최소 상태만 로컬에 저장한다.
9) 차단 의심/재확인 필요 상태에서는 가격 알림 대신 “상태 알림”만 제한적으로 발송한다(스팸 방지).