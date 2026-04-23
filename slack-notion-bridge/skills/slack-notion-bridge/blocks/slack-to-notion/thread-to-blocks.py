"""
Slack 스레드 댓글 → 기존 Notion 페이지 본문에 블록 추가.

사용 시점: 최상위 메시지로 생성한 페이지의 본문에 스레드 댓글을
          시간순으로 누적 기록하고 싶을 때.

병합 가이드:
  message-to-page.py와 같은 `@app.event("message")` 핸들러에 합칩니다.
  thread_ts 존재 여부로 분기.

CUSTOMIZE 포인트:
  - 날짜 감지 후 속성 업데이트(예: 요청 기한) — 필요 없으면 제거
  - append_thread_log(): 블록 포맷 (timestamp prefix, author, text)
"""

import logging

logger = logging.getLogger(__name__)


def handle_thread_reply(event, client, notion, state, parse_deadline=None):
    """스레드 댓글을 Notion 페이지 본문에 paragraph 블록으로 추가.

    Args:
        parse_deadline: callable(text) -> "YYYY-MM-DD" | None
            스레드에서 기한을 감지해 페이지 속성에 업데이트하고 싶으면 전달.
            필요 없으면 None.
    """
    thread_ts = event.get("thread_ts")
    user_id = event.get("user")
    text = event.get("text", "")

    page_id = state.get(thread_ts)

    # fallback: state에 없으면 Notion DB에서 Slack TS로 검색 후 매핑 복구
    if not page_id:
        try:
            page_id = notion.find_page_by_slack_ts(thread_ts)
            if page_id:
                state.set(thread_ts, page_id)
                logger.info(f"스레드 fallback 매핑 복구: ts={thread_ts}")
        except Exception as e:
            logger.warning(f"스레드 fallback 검색 실패: {e}")

    if not page_id:
        logger.debug(f"스레드 매핑 없음: thread_ts={thread_ts}")
        return

    author = _get_user_name(client, user_id)

    # CUSTOMIZE: 스레드 댓글에서 날짜 감지 → 페이지 속성 업데이트
    if parse_deadline:
        deadline = parse_deadline(text)
        if deadline:
            try:
                notion.update_page_deadline(page_id, deadline)
                client.chat_postMessage(
                    channel=event.get("channel"),
                    thread_ts=thread_ts,
                    text=f":pushpin: 요청 기한이 {deadline}로 등록되었습니다.",
                )
                logger.info(f"스레드에서 기한 감지: {deadline} → page_id={page_id}")
            except Exception as e:
                logger.error(f"기한 업데이트 실패: {e}")

    # 스레드 댓글을 페이지 본문에 append
    try:
        notion.append_thread_log(
            page_id=page_id,
            author=author,
            text=text,
            image_urls=[],  # image-attachment.py와 병합 시 채움
        )
    except Exception as e:
        logger.error(f"스레드 로그 실패: {e}", exc_info=True)


def _get_user_name(client, user_id: str) -> str:
    try:
        result = client.users_info(user=user_id)
        profile = result["user"]["profile"]
        return profile.get("real_name") or profile.get("display_name") or user_id
    except Exception:
        return user_id


# ── Notion 측 헬퍼 (notion_client.py에 들어가야 함) ──────────────────
#
# def append_thread_log(self, page_id, author, text, image_urls=None):
#     from datetime import datetime
#     timestamp = datetime.now().strftime("%m/%d %H:%M")
#     content = f"[{timestamp}] {author}: {text}"[:2000]
#
#     children = [
#         {
#             "object": "block",
#             "type": "paragraph",
#             "paragraph": {"rich_text": [{"text": {"content": content}}]},
#         }
#     ]
#     for url in image_urls or []:
#         children.append({
#             "object": "block",
#             "type": "image",
#             "image": {"type": "external", "external": {"url": url}},
#         })
#
#     self.client.blocks.children.append(block_id=page_id, children=children)
