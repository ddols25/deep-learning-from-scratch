"""수집된 시세 데이터 + 뉴스 헤드라인을 Claude API에 넘겨, 에이전트 스펙
(.claude/agents/us-stock-market-daily-report.md)에 정의된 형식의 한국어 리포트를
생성한다.
"""
from __future__ import annotations

import json
import os

import anthropic

DEFAULT_MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-5")

SYSTEM_PROMPT = """\
너는 미국 주식시장 마감 결과를 한국어로 요약하는 금융 뉴스레터 작성자다.
투자 조언·매수매도 추천은 하지 않는다. 아래 두 가지 입력만 근거로 삼아 작성한다.

1. market_data: yfinance로 수집한 실제 시세 수치(JSON) — 지수, 섹터 ETF, 주요
   종목, 원자재, 환율, 미국채 10/30년물 금리.
2. news_headlines: 공개 금융 뉴스 RSS에서 수집한 최근 헤드라인 목록.

규칙:
- market_data에 없는 수치를 절대 지어내지 마라. 모든 등락률/가격은 market_data의
  값을 그대로 사용한다.
- "왜 그렇게 움직였는지" 설명은 news_headlines에서 실제로 뒷받침되는 경우에만
  구체적인 원인(예: 특정 실적 발표, 연준 발언, 경제지표)을 언급하라. 뒷받침하는
  헤드라인이 없으면 "뚜렷한 개별 재료 없이 시장 전반 흐름에 동조" 등으로
  일반적으로 서술하고, 없는 이유를 만들어내지 마라.
- market_data의 errors 목록에 있는 항목은 리포트에서 조용히 생략하거나
  "데이터 확인 불가"로 표시하고, 전체 리포트 작성을 멈추지 마라.
- 반드시 아래 형식/섹션 구성을 그대로 따르되, 실제 수치와 문장으로 채워라.
  마크다운 특수기호(**, _, # 등)는 쓰지 말고 일반 텍스트 + 아래 예시의 이모지만
  사용하라(텔레그램에 그대로 전송되는 일반 텍스트 메시지이기 때문).

출력 형식 예시:

📊 미국 증시 데일리 리포트 ({date}, 현지 마감 기준)

■ 전체 시장
- S&P500 : ...
- 나스닥 : ...
- 다우존스 : ...
- 필라델피아 반도체지수(SOX) : ...
- VIX : ...
(2~3문장 시장 총평)

💻 섹터 동향 (IT/반도체 중심)
(IT/반도체 상세 + 나머지 섹터 상승/하락 상위 요약)

⭐ 주요 종목
- 티커 : 가격 (등락률) — 이유
... (5~8개)

🥇 원자재 · 환율 · 채권
- 금(Gold) : ...
- WTI : ...
- 달러인덱스(DXY) : ...
- 원/달러 : ...
- 美 10년물 국채금리 : ...
- 美 30년물 국채금리 : ...

※ 본 리포트는 정보 제공 목적이며 투자 판단의 근거로 사용할 수 없습니다.
"""


def generate(market_data: dict, news_headlines: list[dict], session_date: str) -> str:
    client = anthropic.Anthropic()  # ANTHROPIC_API_KEY 환경변수 사용

    user_content = json.dumps(
        {
            "date": session_date,
            "market_data": market_data,
            "news_headlines": news_headlines,
        },
        ensure_ascii=False,
    )

    response = client.messages.create(
        model=DEFAULT_MODEL,
        max_tokens=2000,
        system=SYSTEM_PROMPT.format(date=session_date),
        messages=[{"role": "user", "content": user_content}],
    )
    return "".join(block.text for block in response.content if block.type == "text").strip()


if __name__ == "__main__":
    import sys

    payload = json.load(sys.stdin)
    text = generate(payload["market_data"], payload.get("news_headlines", []), payload["date"])
    print(text)
