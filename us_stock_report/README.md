# 미국 증시 데일리 리포트

매일 한국시간(KST) 오전 7시, 미국 증시 개장일에 한해 자동으로 지수·섹터
(IT/반도체 중심)·주요 종목·원자재/환율/미국채 금리를 요약해 텔레그램으로
보내주는 파이프라인입니다.

- 리포트 스펙: [`.claude/agents/us-stock-market-daily-report.md`](../.claude/agents/us-stock-market-daily-report.md)
- 스케줄러: [`.github/workflows/us-stock-report.yml`](../.github/workflows/us-stock-report.yml) (GitHub Actions `schedule` cron — 세션과 무관하게 영구 동작)
- 시세: `yfinance` (무료/비공식)
- 해설 문장: Anthropic Claude API 호출로 생성 (뉴스 RSS 헤드라인을 근거로 사용, 지어내지 않도록 프롬프트에서 강제)
- 전송: 텔레그램 Bot API

## 1. 텔레그램 봇 만들기

1. 텔레그램에서 **@BotFather**를 검색해 대화를 시작합니다.
2. `/newbot` 명령을 보내고 안내에 따라 봇 이름/username을 정합니다.
3. 완료되면 BotFather가 **봇 토큰**(`123456789:AAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` 형태)을 줍니다. 이게 `TELEGRAM_BOT_TOKEN`입니다.
4. 리포트를 받을 대화(자기 자신과의 대화, 또는 만든 그룹/채널)에 이 봇을 추가하고 아무 메시지나 한 번 보냅니다(봇이 먼저 메시지를 보낼 수 있으려면 사용자가 먼저 말을 걸어야 합니다).
5. 아래 URL을 브라우저로 열어 `chat.id` 값을 확인합니다(방금 보낸 메시지가 있어야 보입니다):
   ```
   https://api.telegram.org/bot<봇토큰>/getUpdates
   ```
   응답 JSON의 `result[0].message.chat.id` 값이 `TELEGRAM_CHAT_ID`입니다. 그룹에 추가했다면 그룹 chat id는 보통 음수(`-100...`)입니다.

## 2. GitHub repository secrets 등록

리포지토리 **Settings → Secrets and variables → Actions → New repository secret**에서
아래 3개를 등록합니다.

| Secret 이름 | 값 |
|---|---|
| `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com)에서 발급한 API 키 |
| `TELEGRAM_BOT_TOKEN` | 위 1번에서 받은 봇 토큰 |
| `TELEGRAM_CHAT_ID` | 위 1번에서 확인한 chat id |

## 3. 동작 확인

- Secrets 등록 후 **Actions → US Stock Market Daily Report → Run workflow**로 수동 실행해 텔레그램 메시지가 오는지 확인합니다.
- 이후로는 `.github/workflows/us-stock-report.yml`의 스케줄(UTC 기준 일~목 22:00 = KST 월~금 07:00)에 따라 자동 실행됩니다.
- 휴장일(주말/미국 공휴일)에는 `market_check.py`가 자동으로 감지해 아무 메시지도 보내지 않고 조용히 종료합니다.

## 로컬 테스트

```bash
cd us_stock_report
pip install -r requirements.txt
export ANTHROPIC_API_KEY=...
export TELEGRAM_BOT_TOKEN=...
export TELEGRAM_CHAT_ID=...
python main.py
```

개별 단계만 확인하고 싶다면:

```bash
python market_check.py        # 오늘 리포트 대상 거래일 출력 (휴장일이면 exit 1)
python fetch_data.py           # 시세 JSON만 출력
python news.py                  # 뉴스 헤드라인 JSON만 출력
```

## 파일 구성

| 파일 | 역할 |
|---|---|
| `market_check.py` | NYSE 캘린더 기준 개장일 판별(휴장일 자동 스킵) |
| `fetch_data.py` | 지수/섹터ETF/주요종목/원자재/환율/채권 시세 수집 (yfinance) |
| `news.py` | 뉴스 RSS 헤드라인 수집 (해설 근거용) |
| `generate_report.py` | Claude API로 최종 한국어 리포트 텍스트 생성 |
| `send_telegram.py` | 텔레그램 전송 (4096자 초과 시 분할, 재시도 포함) |
| `main.py` | 위 단계를 순서대로 실행하는 진입점 |
