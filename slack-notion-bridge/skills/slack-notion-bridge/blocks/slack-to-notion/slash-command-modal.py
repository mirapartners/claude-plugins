"""
Slack 슬래시 커맨드 + Block Kit 모달 → 구조화된 Notion 페이지 생성.

사용 시점: 자유 텍스트 파싱 대신 필드 명시적으로 입력받고 싶을 때.
         또는 템플릿 강제해서 데이터 품질 확보하고 싶을 때.

CUSTOMIZE 포인트:
  - COMMAND_NAME: 슬래시 커맨드 이름 (Slack App 설정과 일치)
  - _build_modal(): 모달 뷰 — 필드 구성, 옵션값, 라벨
  - handle_modal_submission(): 제출 처리, Notion 페이지 생성 매핑
"""

import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# CUSTOMIZE: Slack App에 등록한 슬래시 커맨드 이름
COMMAND_NAME = "/요청"

# CUSTOMIZE: 모달 콜백 ID (고유)
MODAL_CALLBACK_ID = "request_modal"


def register(app, notion, state):
    """슬래시 커맨드 + 모달 핸들러 등록."""

    @app.command(COMMAND_NAME)
    def handle_command(ack, body, client):
        ack()
        view = _build_modal()
        client.views_open(trigger_id=body["trigger_id"], view=view)

    @app.view(MODAL_CALLBACK_ID)
    def handle_submission(ack, body, client, view):
        import config  # CUSTOMIZE
        ack()

        user_id = body["user"]["id"]
        values = view["state"]["values"]

        # ── 입력값 추출 ──
        title = values["title_block"]["title_input"]["value"]
        type_sel = values["type_block"]["type_select"].get("selected_option")
        request_type = type_sel["value"] if type_sel else ""

        detail = values["detail_block"]["detail_input"].get("value") or ""

        deadline = values["deadline_block"]["deadline_picker"].get("selected_date") or ""

        assignee_sel = values.get("assignee_block", {}).get("assignee_select", {})
        assignee_slack_id = assignee_sel.get("selected_user")

        # CUSTOMIZE: Slack ID → Notion ID 매핑 (user_map.json 조회)
        assignee_notion_id = _lookup_notion_id(assignee_slack_id)

        requester = _get_user_name(client, user_id)
        request_date = datetime.now().strftime("%Y-%m-%d")

        try:
            # Notion 페이지 생성
            page_id = notion.create_request_page(
                title=title,
                request_type=request_type,
                requester=requester,
                detail=detail,
                request_date=request_date,
                slack_link="",
                slack_ts="",
                deadline=deadline,
                assignee_notion_id=assignee_notion_id,
            )

            # 채널에 확인 메시지 게시
            msg = f":clipboard: *[{request_type}] {title}*\n요청자: {requester}"
            if deadline:
                msg += f" | 기한: {deadline}"
            result = client.chat_postMessage(channel=config.SLACK_CHANNEL_ID, text=msg)

            # ts→page_id 매핑 + Notion에 Slack URL/TS 업데이트
            msg_ts = result["ts"]
            state.set(msg_ts, page_id)
            permalink = _get_permalink(client, config.SLACK_CHANNEL_ID, msg_ts)
            notion.update_page_slack_info(page_id, permalink, msg_ts)

            logger.info(f"모달 요청 접수: {title} (요청자={requester})")

        except Exception as e:
            logger.error(f"모달 요청 실패: {e}", exc_info=True)


def _build_modal():
    """Block Kit 모달 뷰 생성. CUSTOMIZE: 필드 구성을 도메인에 맞춰 수정."""
    # CUSTOMIZE: 유형 옵션
    type_options = [
        {"text": {"type": "plain_text", "text": t}, "value": t}
        for t in ["수정", "오류", "개선", "신규"]
    ]

    return {
        "type": "modal",
        "callback_id": MODAL_CALLBACK_ID,
        "title": {"type": "plain_text", "text": "요청 등록"},
        "submit": {"type": "plain_text", "text": "제출"},
        "close": {"type": "plain_text", "text": "취소"},
        "blocks": [
            # 제목
            {
                "type": "input",
                "block_id": "title_block",
                "label": {"type": "plain_text", "text": "요청 내용"},
                "element": {
                    "type": "plain_text_input",
                    "action_id": "title_input",
                    "placeholder": {"type": "plain_text", "text": "요청 제목"},
                },
            },
            # 유형
            {
                "type": "input",
                "block_id": "type_block",
                "label": {"type": "plain_text", "text": "유형"},
                "element": {
                    "type": "static_select",
                    "action_id": "type_select",
                    "placeholder": {"type": "plain_text", "text": "유형 선택"},
                    "options": type_options,
                },
            },
            # 상세 내용
            {
                "type": "input",
                "block_id": "detail_block",
                "label": {"type": "plain_text", "text": "상세 내용"},
                "optional": True,
                "element": {
                    "type": "plain_text_input",
                    "action_id": "detail_input",
                    "multiline": True,
                },
            },
            # 요청 기한
            {
                "type": "input",
                "block_id": "deadline_block",
                "label": {"type": "plain_text", "text": "요청 기한"},
                "optional": True,
                "element": {
                    "type": "datepicker",
                    "action_id": "deadline_picker",
                },
            },
            # 담당자
            {
                "type": "input",
                "block_id": "assignee_block",
                "label": {"type": "plain_text", "text": "담당자"},
                "optional": True,
                "element": {
                    "type": "users_select",
                    "action_id": "assignee_select",
                    "placeholder": {"type": "plain_text", "text": "담당자 선택"},
                },
            },
        ],
    }


def _lookup_notion_id(slack_id: str | None) -> str:
    """CUSTOMIZE: slack_notion_user_map.json에서 Notion ID 조회."""
    if not slack_id:
        return ""
    import json
    from pathlib import Path
    map_path = Path("data/slack_notion_user_map.json")
    if not map_path.exists():
        return ""
    with open(map_path, "r", encoding="utf-8") as f:
        user_map = json.load(f)
    return user_map.get(slack_id, {}).get("notion_id", "")


def _get_user_name(client, user_id: str) -> str:
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


# ── 동적 필드 변경 (dispatch_action) 예시 ────────────────────────────
#
# 특정 유형 선택 시 담당자를 자동 고정하는 등 동적 동작은
# input 블록에 "dispatch_action": True 를 주고, @app.action(action_id)로
# 변경 이벤트를 받아 client.views_update로 뷰를 새로 그립니다.
# 현재 입력값을 보존하려면 body["view"]["state"]["values"]를 읽어
# _build_modal에 넣어 재생성하세요.
