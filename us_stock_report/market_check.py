"""미국 증시(NYSE) 기준으로, 지금(KST) 시점에 보고할 만한 정규거래일 마감 데이터가
있는지 확인한다.

KST 07:00 시점을 미국 동부시간(ET)으로 변환하면 항상 "직전 정규장이 마감한 날짜"의
저녁 시간대가 된다. 그 ET 날짜가 NYSE 정규 거래일이었는지를 NYSE 캘린더로 판별하면
주말/공휴일을 모두 자동으로 걸러낼 수 있다.
"""
from __future__ import annotations

import sys
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas_market_calendars as mcal

KST = ZoneInfo("Asia/Seoul")
ET = ZoneInfo("America/New_York")


def last_session_date(now_kst: datetime | None = None) -> "date | None":
    """리포트 대상이 되는 NYSE 정규 거래일(ET 기준 date)을 반환한다.

    해당 ET 날짜가 정규 거래일이 아니었다면(주말/공휴일) None을 반환한다.
    """
    now_kst = now_kst or datetime.now(tz=KST)
    now_et = now_kst.astimezone(ET)
    target_date = now_et.date()

    nyse = mcal.get_calendar("NYSE")
    schedule = nyse.schedule(
        start_date=target_date.replace(day=1) if target_date.day <= 5 else target_date,
        end_date=target_date,
    )
    session_dates = {ts.date() for ts in schedule.index}
    return target_date if target_date in session_dates else None


def is_early_close(session_date) -> bool:
    """조기 폐장일(추수감사절 다음날, 크리스마스 이브 등) 여부."""
    nyse = mcal.get_calendar("NYSE")
    schedule = nyse.schedule(start_date=session_date, end_date=session_date)
    if schedule.empty:
        return False
    close = schedule.iloc[0]["market_close"].tz_convert(ET)
    return close.hour < 16


if __name__ == "__main__":
    # CLI: 거래일이면 "YYYY-MM-DD"를 stdout에 출력하고 exit 0,
    # 거래일이 아니면 아무것도 출력하지 않고 exit 1 (셸 스크립트/워크플로우에서 분기용).
    session = last_session_date()
    if session is None:
        sys.exit(1)
    print(session.isoformat())
