"""
Slack 메시지/스레드 첨부 이미지 → Notion image 블록.

사용 시점: 스크린샷 등 이미지를 Notion 페이지 본문에 임베드하고 싶을 때.

주의: Slack의 `url_private`는 인증 필요. Notion이 접근 가능한 공개 URL을
     얻으려면 `files.sharedPublicURL` 호출 → `permalink_public`에서
     `pub_secret` 추출 → `url_private?pub_secret=...` 조합.

     이 API는 **User Token(`xoxp-`)**만 호출 가능 — Bot Token으로는 불가.
     SLACK_USER_TOKEN 환경변수 필수, User Token Scope에 `files:write` 추가.

병합 가이드:
  message-to-page.py와 thread-to-blocks.py 양쪽에서 호출 가능.
  `parsed["images"]` → 이 모듈의 `make_images_public()` → `page_id` 생성/업데이트 시 URL 리스트 전달.
"""

import logging
import re

from slack_sdk import WebClient

logger = logging.getLogger(__name__)

_user_client: WebClient | None = None


def get_user_client(user_token: str | None) -> WebClient | None:
    """User Token 기반 Slack 클라이언트 (lazy init)."""
    global _user_client
    if _user_client is None and user_token:
        _user_client = WebClient(token=user_token)
    return _user_client


def extract_image_files(files: list) -> list[dict]:
    """event.files에서 이미지만 필터링."""
    images = []
    for f in files or []:
        if f.get("mimetype", "").startswith("image/"):
            images.append({
                "id": f.get("id"),
                "url_private": f.get("url_private", ""),
                "name": f.get("name", ""),
            })
    return images


def make_images_public(user_client: WebClient, images: list[dict]) -> list[str]:
    """이미지 파일을 공개 처리하여 Notion external URL로 쓸 수 있는 URL 리스트 반환.

    각 파일에 대해:
      1) files.sharedPublicURL 호출 → permalink_public 획득
      2) permalink_public 끝 hex 부분을 pub_secret으로 추출
      3) url_private?pub_secret=... 로 조합

    already_public 에러 시 files.info fallback.
    """
    public_urls = []
    for img in images:
        file_id = img.get("id")
        url_private = img.get("url_private", "")
        if not file_id or not url_private:
            continue

        try:
            result = user_client.files_sharedPublicURL(file=file_id)
            permalink_public = result.get("file", {}).get("permalink_public", "")

            if not permalink_public:
                logger.warning(f"이미지 공개 URL 없음: file_id={file_id}")
                continue

            match = re.search(r"-([a-f0-9]+)$", permalink_public)
            if not match:
                logger.warning(f"pub_secret 추출 실패: {permalink_public}")
                continue

            public_url = f"{url_private}?pub_secret={match.group(1)}"
            public_urls.append(public_url)
            logger.info(f"이미지 공개 처리 완료: file_id={file_id}")

        except Exception as e:
            # already_public 에러면 files.info로 기존 permalink_public 조회
            if "already_public" in str(e):
                try:
                    info = user_client.files_info(file=file_id)
                    permalink_public = info.get("file", {}).get("permalink_public", "")
                    match = re.search(r"-([a-f0-9]+)$", permalink_public)
                    if match:
                        public_url = f"{url_private}?pub_secret={match.group(1)}"
                        public_urls.append(public_url)
                        logger.info(f"이미 공개된 이미지 URL 획득: file_id={file_id}")
                        continue
                except Exception:
                    pass
            logger.warning(f"이미지 공개 처리 실패: file_id={file_id}, error={e}")

    return public_urls


# ── Notion 측 — image 블록 삽입 페이로드 ─────────────────────────────
#
# children = [
#     {
#         "object": "block",
#         "type": "image",
#         "image": {
#             "type": "external",
#             "external": {"url": public_url},
#         },
#     }
#     for public_url in public_urls
# ]
#
# notion.blocks.children.append(block_id=page_id, children=children)
