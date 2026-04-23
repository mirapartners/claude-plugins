"""
Notion 상태 변경 감지 → Slack 스레드 알림.

사용 시점: 특정 Notion 상태(예: "완료")로 변경된 페이지를 감지해
          원본 Slack 메시지 스레드에 알림을 보내고 싶을 때.

동작:
  1. 데몬 스레드로 interval(기본 60초)마다 DB 쿼리
  2. 해당 상태인 페이지 목록 획득
  3. notified_status.json에 기록 없는 신규 건만 처리
  4. 페이지의 Slack TS → chat_postMessage(thread_ts=...)
  5. notified_status.json에 기록

중복 방지: page_id → last_notified_status 맵을 JSON 파일에 저장.
          담당자가 완료를 해제했다가 다시 완료로 바꿔도 같은 값이면 재알림 없음.

CUSTOMIZE 포인트:
  - WATCH_STATUS: 감지할 상태값 (예: "완료", "승인됨")
  - 알림 메시지 포맷
  - 추가 속성 업데이트 (예: 완료일 자동 세팅)
"""

import json
import logging
import threading
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# CUSTOMIZE: 감지할 상태값
WATCH_STATUS = "완료"


class StatusPoller:
    """Notion DB를 주기 폴링하여 특정 상태로 변경된 페이지에 Slack 알림."""

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
            logger.info(f"상태 알림 기록 로드: {len(self._notified)}건")

    def _save(self):
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(self._notified, f, ensure_ascii=False, indent=2)

    def start(self):
        thread = threading.Thread(target=self._loop, daemon=True)
        thread.start()
        logger.info(f"상태 폴러 시작 (간격: {self.interval}초, 감시: {WATCH_STATUS})")

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
        pages = self.notion.query_pages_by_status(WATCH_STATUS)
        for page in pages:
            page_id = page["id"]
            if self._notified.get(page_id) == WATCH_STATUS:
                continue

            # CUSTOMIZE: 완료일 자동 세팅 (필요한 경우만)
            completed_date = self.notion.get_page_completed_date(page)
            if not completed_date:
                completed_date = datetime.now().strftime("%Y-%m-%d")
                try:
                    self.notion.update_page_completed_date(page_id, completed_date)
                except Exception as e:
                    logger.error(f"완료일 입력 실패: page_id={page_id}, error={e}")

            # CUSTOMIZE: 알림 메시지 포맷
            message = f":tada: [완료] 요청하신 사항이 {completed_date}에 완료 처리되었습니다."

            self._send_thread_message(page, message)
            self._notified[page_id] = WATCH_STATUS
            self._save()

    def _send_thread_message(self, page: dict, message: str):
        """페이지에 연결된 Slack 스레드에 메시지 전송."""
        page_id = page["id"]

        # Slack TS 우선 페이지 속성에서, 없으면 StateManager 역조회
        slack_ts = self.notion.get_page_slack_ts(page)
        if not slack_ts:
            slack_ts = self.state.get_ts_by_page_id(page_id)
        if not slack_ts:
            logger.debug(f"Slack TS 없음, 알림 skip: page_id={page_id}")
            return

        try:
            self.slack_client.chat_postMessage(
                channel=self.channel_id,
                thread_ts=slack_ts,
                text=message,
            )
            logger.info(f"스레드 알림 발송: page_id={page_id}")
        except Exception as e:
            logger.error(f"스레드 알림 실패: page_id={page_id}, error={e}")


# ── Notion 측 헬퍼 (notion_client.py에 있어야 함) ────────────────────
#
# def query_pages_by_status(self, status: str) -> list[dict]:
#     result = self.client.databases.query(
#         database_id=self.database_id,
#         filter={"property": "상태", "status": {"equals": status}},
#     )
#     return result.get("results", [])
#
# @staticmethod
# def get_page_slack_ts(page: dict) -> str:
#     rt = page.get("properties", {}).get("Slack TS", {}).get("rich_text", [])
#     return rt[0].get("plain_text", "") if rt else ""
