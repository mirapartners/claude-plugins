"""
Slack 멘션 추출 + 실명 치환.

사용 시점:
  - 메시지에서 멘션된 사용자를 담당자로 자동 지정할 때
  - 제목/상세에 <@UXXXXXXX> 대신 @이름 으로 표기하고 싶을 때

CUSTOMIZE:
  - user_map.json 경로 (Slack ID → {name, notion_id} 매핑)
  - users.info 폴백 사용 여부 (scope `users:read` 필요)
"""

import json
import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

_user_map_cache: dict | None = None
_name_cache: dict[str, str] = {}


def extract_mentions(text: str) -> list[str]:
    """텍스트에서 Slack 멘션 사용자 ID 목록 추출. 순서 보존."""
    return re.findall(r"<@([A-Z0-9]+)>", text or "")


def load_user_map(map_path: Path) -> dict:
    """slack_notion_user_map.json 로드. 구조: {slack_id: {name, notion_id}}."""
    global _user_map_cache
    if _user_map_cache is None:
        if map_path.exists():
            with open(map_path, "r", encoding="utf-8") as f:
                _user_map_cache = json.load(f)
        else:
            _user_map_cache = {}
    return _user_map_cache


def lookup_user_name(slack_client, slack_id: str, user_map: dict) -> str:
    """Slack ID를 실명으로 변환. user_map 우선, 없으면 users.info. 결과 캐싱."""
    if slack_id in _name_cache:
        return _name_cache[slack_id]

    # 1차: user_map
    entry = user_map.get(slack_id, {})
    if entry.get("name"):
        _name_cache[slack_id] = entry["name"]
        return entry["name"]

    # 2차: Slack users.info (scope: users:read)
    try:
        result = slack_client.users_info(user=slack_id)
        profile = result["user"]["profile"]
        name = profile.get("real_name") or profile.get("display_name") or slack_id
    except Exception:
        name = slack_id

    _name_cache[slack_id] = name
    return name


def replace_mentions_with_names(text: str, slack_client, user_map: dict) -> str:
    """텍스트 내 <@UXXXX> 패턴을 @실명으로 치환."""
    if not text:
        return text

    def _sub(m):
        slack_id = m.group(1)
        name = lookup_user_name(slack_client, slack_id, user_map)
        return f"@{name}"

    return re.sub(r"<@([A-Z0-9]+)>", _sub, text)


# ── 담당자 자동 지정 예시 ────────────────────────────────────────────
#
# def resolve_assignee(event, parsed, user_map, requester_id):
#     """담당자 결정: 멘션된 사람 > 유형별 고정 > 기본값."""
#     mentions = extract_mentions(event.get("text", ""))
#
#     # 1) 멘션된 사람 (요청자 본인 제외)
#     for mid in mentions:
#         if mid != requester_id and mid in user_map:
#             return user_map[mid]
#
#     # 2) 유형별 고정 (예: 데이터 관련 → 데이터팀 리더)
#     if parsed.get("request_type") == "데이터 관련":
#         return user_map.get(DATA_TEAM_LEAD_SLACK_ID, {})
#
#     # 3) 기본값
#     return user_map.get(DEFAULT_ASSIGNEE_SLACK_ID, {})
