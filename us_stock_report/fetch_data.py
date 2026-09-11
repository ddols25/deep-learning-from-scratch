"""yfinance로 지수/섹터/주요종목/원자재/환율/채권 시세를 수집해 dict(JSON 직렬화
가능)로 반환한다. 네트워크/데이터 오류가 난 개별 티커는 조용히 건너뛰고
`errors` 리스트에 기록한다(리포트 전체를 실패시키지 않기 위함).
"""
from __future__ import annotations

import json
import sys
from typing import Any

import yfinance as yf

INDICES = {
    "^GSPC": "S&P500",
    "^IXIC": "나스닥종합지수",
    "^DJI": "다우존스산업평균",
    "^SOX": "필라델피아반도체지수(SOX)",
    "^VIX": "VIX",
}

SECTOR_ETFS = {
    "XLK": "정보기술(Technology)",
    "SMH": "반도체(Semiconductors)",
    "XLE": "에너지",
    "XLF": "금융",
    "XLV": "헬스케어",
    "XLI": "산업재",
    "XLP": "필수소비재",
    "XLY": "임의소비재",
    "XLC": "커뮤니케이션서비스",
    "XLU": "유틸리티",
    "XLRE": "부동산",
    "XLB": "소재",
}

KEY_STOCKS = {
    "AAPL": "Apple",
    "MSFT": "Microsoft",
    "NVDA": "NVIDIA",
    "GOOGL": "Alphabet(구글)",
    "AMZN": "Amazon",
    "META": "Meta",
    "TSLA": "Tesla",
    "AVGO": "Broadcom",
    "AMD": "AMD",
}

COMMODITIES = {
    "GC=F": "금(Gold)",
    "CL=F": "WTI유",
    "BZ=F": "브렌트유",
}

FX = {
    "DX-Y.NYB": "달러인덱스(DXY)",
    "KRW=X": "원/달러 환율",
}

# ^TNX, ^TYX는 Yahoo Finance 관례상 "수익률 x 10" 스케일로 제공된다.
BONDS = {
    "^TNX": "미국채 10년물 금리",
    "^TYX": "미국채 30년물 금리",
}

ALL_GROUPS = {
    "indices": INDICES,
    "sectors": SECTOR_ETFS,
    "key_stocks": KEY_STOCKS,
    "commodities": COMMODITIES,
    "fx": FX,
    "bonds": BONDS,
}


def _pct_change(prev: float, last: float) -> float:
    if prev == 0:
        return 0.0
    return (last - prev) / prev * 100.0


def fetch_all() -> dict[str, Any]:
    all_tickers = [t for group in ALL_GROUPS.values() for t in group]
    result: dict[str, Any] = {"errors": []}

    data = yf.download(
        all_tickers,
        period="5d",
        interval="1d",
        group_by="ticker",
        auto_adjust=False,
        progress=False,
        threads=True,
    )

    for group_name, tickers in ALL_GROUPS.items():
        group_out = {}
        for ticker, label in tickers.items():
            try:
                closes = data[ticker]["Close"].dropna()
                if len(closes) < 2:
                    raise ValueError(f"insufficient history for {ticker}")
                last = float(closes.iloc[-1])
                prev = float(closes.iloc[-2])
                scale = 0.1 if group_name == "bonds" else 1.0
                entry = {
                    "label": label,
                    "last": round(last * scale, 4),
                    "prev": round(prev * scale, 4),
                    "change": round((last - prev) * scale, 4),
                    "pct_change": round(_pct_change(prev, last), 3),
                    "as_of": str(closes.index[-1].date()),
                }
                group_out[ticker] = entry
            except Exception as exc:  # noqa: BLE001 - 개별 티커 실패는 리포트 전체를 막지 않는다
                result["errors"].append(f"{ticker} ({label}): {exc}")
        result[group_name] = group_out

    return result


if __name__ == "__main__":
    payload = fetch_all()
    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
