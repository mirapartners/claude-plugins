"""
Slack 리액션 → Notion 속성 변경.

사용 시점: 특정 이모지 리액션을 상태/체크박스 같은 속성 변경으로 매핑할 때.
예: ✅ 리액션 → 상태를 "완료"로.

CUSTOMIZE 포인트:
  - TRIGGER_REACTION: 감지할 이모지 이름 (콜론 없이)
  - 매핑된 Notion 속성 변경 로직
"""

import logging

logger = logging.getLogger(__name__)

# CUSTOMIZE: 감지할 리액션 이모지 이름
TRIGGER_REACTION = "white_check_mark"  # ✅


def register(app, notion, state):
    """Slack Bolt App에 리액션 핸들러 등록."""

    @app.event("reaction_added")
    def handle_reaction(event, client):
        import config  # CUSTOMIZE

        reaction = event.get("reaction")
        item = event.get("item", {})

        if reaction != TRIGGER_REACTION:
            return
        if item.get("channel") != config.SLACK_CHANNEL_ID:
            return

        item_ts = item.get("ts")
        page_id = state.get(item_ts)

        # fallback: Notion DB에서 Slack TS로 검색
        if not page_id:
            try:
                page_id = notion.find_page_by_slack_ts(item_ts)
                if page_id:
                    state.set(item_ts, page_id)
                    logger.info(f"리액션 fallback 매핑 복구: ts={item_ts}")
            except Exception as e:
                logger.warning(f"리액션 fallback 검색 실패: {e}")

        if not page_id:
            logger.warning(f"리액션 처리 실패: ts={item_ts} 매핑 없음")
            return

        try:
            # CUSTOMIZE: 리액션에 따른 속성 변경
            notion.update_page_status(page_id, config.STATUS_DONE)
            logger.info(f"리액션 → 상태 변경: ts={item_ts} → page_id={page_id}")
        except Exception as e:
            logger.error(f"속성 업데이트 실패: {e}")


# ── 다중 리액션 → 다중 속성 매핑 예시 ────────────────────────────────
#
# REACTION_TO_STATUS = {
#     "white_check_mark": "완료",
#     "eyes": "진행 중",
#     "x": "시작 전",
# }
#
# if reaction in REACTION_TO_STATUS:
#     notion.update_page_status(page_id, REACTION_TO_STATUS[reaction])
