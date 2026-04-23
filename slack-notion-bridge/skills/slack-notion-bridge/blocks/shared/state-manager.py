"""
Slack ts ↔ Notion page_id 매핑 관리.

사용 시점: 거의 항상 필요. 최상위 메시지로 페이지를 만든 후,
          스레드 댓글이나 리액션 이벤트가 왔을 때 해당 페이지를 찾아야 함.

동작:
  - 메모리 dict + JSON 파일 이중 저장
  - 읽기는 메모리 우선, 쓰기는 즉시 파일 동기화
  - page_id로 ts 역조회 지원 (Notion 폴러에서 사용)
  - 서버 재기동 후 파일 유실돼도 Notion DB의 Slack TS 속성으로 fallback 복구 가능
    (이 fallback 로직은 slack_handler 쪽에서 호출 — NotionClient.find_page_by_slack_ts)
"""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class StateManager:
    def __init__(self, map_path: Path):
        self.map_path = map_path
        self._mapping: dict[str, str] = {}
        self._load()

    def _load(self):
        if self.map_path.exists():
            with open(self.map_path, "r", encoding="utf-8") as f:
                self._mapping = json.load(f)
            logger.info(f"매핑 데이터 로드: {len(self._mapping)}건")
        else:
            self._mapping = {}

    def _save(self):
        self.map_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.map_path, "w", encoding="utf-8") as f:
            json.dump(self._mapping, f, ensure_ascii=False, indent=2)

    def set(self, slack_ts: str, page_id: str):
        self._mapping[slack_ts] = page_id
        self._save()
        logger.info(f"매핑 저장: ts={slack_ts} → page_id={page_id}")

    def get(self, slack_ts: str) -> str | None:
        return self._mapping.get(slack_ts)

    def has(self, slack_ts: str) -> bool:
        return slack_ts in self._mapping

    def get_ts_by_page_id(self, page_id: str) -> str | None:
        """page_id로 slack_ts 역조회 (Notion 폴러의 스레드 알림에 사용)."""
        for ts, pid in self._mapping.items():
            if pid == page_id:
                return ts
        return None
