"""
Slack 최상위 메시지 → Notion 페이지 생성.

사용 시점: 대상 채널에 올라온 새 메시지를 Notion DB에 페이지로 기록할 때.

병합 가이드:
  이 핸들러는 `@app.event("message")` 하나에 묶입니다.
  같은 핸들러 안에서 스레드 댓글(thread-to-blocks.py)도 처리하려면
  thread_ts 분기로 둘을 합치세요 — 아래 dispatch 예시 참고.

CUSTOMIZE 포인트:
  - config.SLACK_CHANNEL_ID: 대상 채널 ID
  - parse_message(): 도메인별 메시지 파싱 (제목/유형/카테고리 추출)
  - 담당자 결정 로직: 팀 규칙에 맞춰 수정
  - notion.create_request_page(): DB 스키마에 맞춰 필드 조정
"""

import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def register(app, notion, state, parse_message, resolve_assignee):
    """Slack Bolt App에 메시지 핸들러를 등록한다.

    Args:
        app: slack_bolt.App 인스턴스
        notion: NotionClient 래퍼 (create_request_page, find_page_by_slack_ts 구현 필요)
        state: StateManager (ts↔page_id 매핑)
        parse_message: callable(event: dict) -> dict | None
            반환 dict 예시: {"title", "detail", "request_type", "category", "images"}
        resolve_assignee: callable(event, parsed) -> dict
            반환 dict 예시: {"slack_id", "name", "notion_id"}  (없으면 빈 dict)
    """

    @app.event("message")
    def handle_message(event, client, say):
        import config  # CUSTOMIZE: 프로젝트 config

        channel = event.get("channel")
        subtype = event.get("subtype")
        thread_ts = event.get("thread_ts")
        ts = event.get("ts")

        # 대상 채널 필터
        if channel != config.SLACK_CHANNEL_ID:
            return
        # 봇/수정/삭제 메시지 무시
        if subtype in ("bot_message", "message_changed", "message_deleted"):
            return
        # 스레드 댓글은 다른 블록에서 처리 (dispatch)
        if thread_ts and thread_ts != ts:
            # CUSTOMIZE: thread-to-blocks.py와 병합하려면 여기서 handle_thread_reply 호출
            return

        _handle_new_request(event, client, notion, state, parse_message, resolve_assignee)


def _handle_new_request(event, client, notion, state, parse_message, resolve_assignee):
    ts = event.get("ts")
    user_id = event.get("user")

    # 중복 방지: 이미 처리된 ts면 skip
    if state.has(ts):
        return

    # fallback: Notion DB에 이미 있으면 매핑만 복구
    existing = notion.find_page_by_slack_ts(ts)
    if existing:
        state.set(ts, existing)
        return

    parsed = parse_message(event)
    if not parsed:
        logger.debug(f"파싱 불가 메시지 무시: ts={ts}")
        return

    # 요청자 이름 조회
    requester = _get_user_name(client, user_id)

    # 담당자 결정
    assignee = resolve_assignee(event, parsed) or {}

    # Slack permalink
    slack_link = _get_permalink(client, event.get("channel"), ts)

    # 등록일 = 메시지 타임스탬프
    request_date = datetime.fromtimestamp(float(ts)).strftime("%Y-%m-%d")

    try:
        page_id = notion.create_request_page(
            title=parsed["title"],
            request_type=parsed.get("request_type", ""),
            requester=requester,
            detail=parsed.get("detail", ""),
            category=parsed.get("category", ""),
            request_date=request_date,
            slack_link=slack_link,
            slack_ts=ts,
            image_urls=parsed.get("image_urls", []),  # image-attachment.py 참고
            assignee_notion_id=assignee.get("notion_id", ""),
            deadline=parsed.get("deadline", ""),
        )
        state.set(ts, page_id)
        logger.info(f"페이지 생성: {parsed['title']} (ts={ts})")

    except Exception as e:
        logger.error(f"페이지 생성 실패: {e}", exc_info=True)


def _get_user_name(client, user_id: str) -> str:
    """Slack 사용자 실명 조회."""
    try:
        result = client.users_info(user=user_id)
        profile = result["user"]["profile"]
        return profile.get("real_name") or profile.get("display_name") or user_id
    except Exception:
        return user_id


def _get_permalink(client, channel: str, ts: str) -> str:
    try:
        result = client.chat_getPermalink(channel=channel, message_ts=ts)
        return result.get("permalink", "")
    except Exception:
        return ""
