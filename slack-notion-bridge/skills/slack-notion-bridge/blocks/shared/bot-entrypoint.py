"""
Socket Mode 봇 진입점 스켈레톤 (main.py).

사용 시점: 거의 항상. 선택한 블록들을 조립해 하나의 프로세스로 실행.

구성:
  - 환경변수 검증
  - 중복 실행 방지 (PID 파일)
  - 로거 설정 (파일 + 콘솔)
  - Slack Bolt App + Socket Mode Handler
  - Notion 폴러 (선택적, 데몬 스레드)

CUSTOMIZE:
  - 선택한 빌딩블록의 register/start 함수 호출
  - 필요한 환경변수 목록
"""

import logging
import os
import sys

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

import config  # CUSTOMIZE: 프로젝트 config


def setup_logging():
    config.LOG_DIR.mkdir(parents=True, exist_ok=True)
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler = logging.FileHandler(config.LOG_FILE, encoding="utf-8")
    file_handler.setFormatter(formatter)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(file_handler)
    root.addHandler(console_handler)


def check_pid():
    """중복 실행 방지."""
    if config.PID_FILE.exists():
        old_pid = config.PID_FILE.read_text().strip()
        try:
            os.kill(int(old_pid), 0)
            print(f"이미 실행 중입니다 (PID: {old_pid})")
            sys.exit(1)
        except (OSError, ValueError):
            pass
    config.PID_FILE.write_text(str(os.getpid()))


def cleanup_pid():
    if config.PID_FILE.exists():
        config.PID_FILE.unlink()


def validate_config():
    """필수 환경변수 검증."""
    # CUSTOMIZE: 선택한 블록에 따라 필수 항목 조정
    required = {
        "SLACK_BOT_TOKEN": config.SLACK_BOT_TOKEN,
        "SLACK_APP_TOKEN": config.SLACK_APP_TOKEN,
        "SLACK_CHANNEL_ID": config.SLACK_CHANNEL_ID,
        "NOTION_TOKEN": config.NOTION_TOKEN,
        "NOTION_DATABASE_ID": config.NOTION_DATABASE_ID,
    }
    missing = [k for k, v in required.items() if not v]
    if missing:
        print(f"필수 환경변수 누락: {', '.join(missing)}")
        print("'.env' 파일을 확인하세요.")
        sys.exit(1)


def main():
    validate_config()
    check_pid()
    setup_logging()

    logger = logging.getLogger(__name__)
    logger.info("Slack-Notion 봇 시작")

    try:
        # ── 공유 자원 초기화 ──
        # CUSTOMIZE: 선택한 블록에 맞춰 import 및 초기화
        from modules.notion_client import NotionClient
        from modules.state_manager import StateManager

        notion = NotionClient()
        state = StateManager(config.TS_PAGE_MAP_PATH)

        # ── Slack Bolt App ──
        app = App(token=config.SLACK_BOT_TOKEN)

        # ── 선택한 블록의 핸들러 등록 ──
        # CUSTOMIZE: 필요한 블록만 호출
        #
        # from modules.slack_handler import register_handlers
        # register_handlers(app, notion, state, router)

        # ── Notion 폴러 시작 (선택적) ──
        # CUSTOMIZE: notion-to-slack 블록 썼으면 추가
        #
        # from modules.notion_poller import NotionPoller
        # poller = NotionPoller(notion, state, app.client)
        # poller.start()

        # ── Socket Mode 실행 (블로킹) ──
        handler = SocketModeHandler(app, config.SLACK_APP_TOKEN)
        logger.info("Socket Mode 연결 시작...")
        handler.start()

    except KeyboardInterrupt:
        logger.info("봇 종료 (사용자 중단)")
    except Exception as e:
        logger.error(f"봇 오류: {e}", exc_info=True)
    finally:
        cleanup_pid()


if __name__ == "__main__":
    main()
