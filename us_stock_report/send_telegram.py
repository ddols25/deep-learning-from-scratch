"""텔레그램 Bot API로 리포트 텍스트를 전송한다.

- TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID 환경변수를 사용한다.
- 4096자 제한을 넘으면 문단(빈 줄) 단위로 잘라 여러 메시지로 나눠 보낸다.
- 429/네트워크 오류 시 지수 백오프로 최대 3회 재시도한다.
- parse_mode를 지정하지 않는다(일반 텍스트) — 자동화 파이프라인에서 마크다운
  이스케이프 실패로 전송이 깨지는 것을 방지하기 위함.
"""
from __future__ import annotations

import os
import sys
import time

import requests

TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"
MAX_LEN = 4000  # 여유를 둔 안전 길이(텔레그램 제한 4096자)


def _split_message(text: str, max_len: int = MAX_LEN) -> list[str]:
    if len(text) <= max_len:
        return [text]

    chunks: list[str] = []
    current = ""
    for paragraph in text.split("\n\n"):
        candidate = f"{current}\n\n{paragraph}" if current else paragraph
        if len(candidate) > max_len:
            if current:
                chunks.append(current)
            current = paragraph[:max_len]
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks


def send(text: str, *, token: str | None = None, chat_id: str | None = None) -> None:
    token = token or os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = chat_id or os.environ["TELEGRAM_CHAT_ID"]
    url = TELEGRAM_API.format(token=token)

    for chunk in _split_message(text):
        _send_with_retry(url, chat_id, chunk)


def _send_with_retry(url: str, chat_id: str, text: str, max_retries: int = 3) -> None:
    delay = 2
    last_exc: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.post(
                url,
                json={"chat_id": chat_id, "text": text, "disable_web_page_preview": True},
                timeout=15,
            )
            if resp.status_code == 200:
                return
            last_exc = RuntimeError(f"telegram API {resp.status_code}: {resp.text}")
        except requests.RequestException as exc:  # noqa: BLE001
            last_exc = exc

        if attempt < max_retries:
            time.sleep(delay)
            delay *= 2

    raise RuntimeError(f"텔레그램 전송 실패 (최대 재시도 초과): {last_exc}")


if __name__ == "__main__":
    message = sys.stdin.read()
    send(message)
    print("텔레그램 전송 완료", file=sys.stderr)
