"""
Notion 날짜 속성 변경 감지 → Slack 스레드 알림.

사용 시점: 완료 예정일, 마감일 등 날짜 속성이 설정/변경될 때마다
          원본 Slack 스레드에 알림하고 싶을 때.

동작:
  1. 데몬 스레드로 interval(기본 60초)마다 DB 쿼리
  2. 해당 날짜 속성이 비어있지 않은 페이지 목록
  3. notified_date.json에 기록된 값과 다를 때만 알림 (변경 감지)
  4. page의 Slack TS → chat_postMessage(thread_ts=...)
  5. notified_date.json에 현재 값 기록

CUSTOMIZE 포인트:
  - WATCH_PROPERTY: 감시할 날짜 속성 이름
  - 알림 메시지 포맷
"""

import json
import logging
import threading
from pathlib import Path

logger = logging.getLogger(__name__)

# CUSTOMIZE: 감시할 날짜 속성 이름 (Notion DB 속성명과 일치)
WATCH_PROPERTY = "완료 예정일"


class DateChangeNotifier:
    """특정 날짜 속성 값 변경을 감지해 Slack 스레드 알림."""

    def __init__(
        self,
        notion,
        state,
        slack_client,
        channel_id: str,
        notified_path: Path,
        interval: int = 60,
    ):
        self.notion = notion
        self.state = state
        self.slack_client = slack_client
        self.channel_id = channel_id
        self.interval = interval

        self._notified: dict[str, str] = {}
        self._path = notified_path
        self._load()

        self._stop_event = threading.Event()

    def _load(self):
        if self._path.exists():
            with open(self._path, "r", encoding="utf-8") as f:
                self._notified = json.load(f)
            logger.info(f"날짜 알림 기록 로드: {len(self._notified)}건")

    def _save(self):
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(self._notified, f, ensure_ascii=False, indent=2)

    def start(self):
        thread = threading.Thread(target=self._loop, daemon=True)
        thread.start()
        logger.info(f"날짜 변경 폴러 시작 (간격: {self.interval}초, 속성: {WATCH_PROPERTY})")

    def stop(self):
        self._stop_event.set()

    def _loop(self):
        while not self._stop_event.is_set():
            try:
                self._check()
            except Exception as e:
                logger.error(f"폴링 오류: {e}", exc_info=True)
            self._stop_event.wait(self.interval)

    def _check(self):
        pages = self.notion.query_pages_with_date(WATCH_PROPERTY)
        for page in pages:
            page_id = page["id"]
            date_value = self.notion.get_page_date(page, WATCH_PROPERTY)
            if not date_value:
                continue
            if self._notified.get(page_id) == date_value:
                continue

            # CUSTOMIZE: 알림 메시지 포맷
            message = f":hourglass_flowing_sand: [완료 예정] 요청하신 사항은 {date_value}에 완료될 예정입니다."

            self._send_thread_message(page, message)
            self._notified[page_id] = date_value
            self._save()

    def _send_thread_message(self, page: dict, message: str):
        page_id = page["id"]

        slack_ts = self.notion.get_page_slack_ts(page)
        if not slack_ts:
            slack_ts = self.state.get_ts_by_page_id(page_id)
        if not slack_ts:
            return

        try:
            self.slack_client.chat_postMessage(
                channel=self.channel_id,
                thread_ts=slack_ts,
                text=message,
            )
            logger.info(f"날짜 변경 알림 발송: page_id={page_id}")
        except Exception as e:
            logger.error(f"알림 실패: page_id={page_id}, error={e}")


# ── Notion 측 헬퍼 (notion_client.py에 있어야 함) ────────────────────
#
# def query_pages_with_date(self, property_name: str) -> list[dict]:
#     result = self.client.databases.query(
#         database_id=self.database_id,
#         filter={"property": property_name, "date": {"is_not_empty": True}},
#     )
#     return result.get("results", [])
#
# @staticmethod
# def get_page_date(page: dict, property_name: str) -> str:
#     prop = page.get("properties", {}).get(property_name, {})
#     date_obj = prop.get("date") or {}
#     return date_obj.get("start", "") or ""
