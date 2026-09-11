"""미국 증시 데일리 리포트 파이프라인 진입점.

1. NYSE 개장일(휴장일 자동 스킵) 확인
2. yfinance로 시세 데이터 수집
3. 뉴스 헤드라인 수집
4. Claude API로 한국어 리포트 생성
5. 텔레그램 전송

GitHub Actions에서 매일 KST 07:00 (weekday)에 이 스크립트를 실행하도록 예약한다
(.github/workflows/us-stock-report.yml). 휴장일이면 아무 것도 하지 않고 정상
종료(exit 0)한다.
"""
from __future__ import annotations

import sys

from fetch_data import fetch_all
from generate_report import generate
from market_check import last_session_date
from news import fetch_headlines
from send_telegram import send


def main() -> int:
    session_date = last_session_date()
    if session_date is None:
        print("오늘은 미국 증시 휴장일(주말/공휴일)입니다 — 리포트를 생략합니다.")
        return 0

    print(f"[1/4] 시세 데이터 수집 중... (대상 거래일: {session_date})")
    market_data = fetch_all()
    if market_data.get("errors"):
        print("일부 티커 조회 실패:", market_data["errors"], file=sys.stderr)

    print("[2/4] 뉴스 헤드라인 수집 중...")
    headlines = fetch_headlines()

    print("[3/4] Claude API로 리포트 생성 중...")
    report_text = generate(market_data, headlines, session_date.isoformat())

    print("[4/4] 텔레그램 전송 중...")
    send(report_text)

    print("완료.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
