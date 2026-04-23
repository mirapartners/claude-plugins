---
name: slack-notion-bridge
description: Use when the user wants to build a Slack ↔ Notion integration — any bot that records Slack activity into a Notion database, or notifies a Slack thread when a Notion property changes. Triggers include "Slack 노션 연동", "슬랙 메시지를 노션에 기록", "Notion 상태 바뀌면 Slack 알림", "요청 수집 봇", "Slack → Notion 자동화", and similar bidirectional-sync requests. This skill is a reference kit (patterns + building blocks, Python with slack_bolt + notion-client over Socket Mode) — it does NOT scaffold a ready-to-run project. You assemble the bot with the user by picking the blocks they need and filling in their domain logic.
---

# Slack ↔ Notion 연동 스킬

Slack과 Notion을 잇는 봇을 만들 때 참고하는 **빌딩블록 키트**입니다. 사용자의 유스케이스마다 필요한 조각이 달라서 완성된 템플릿 대신 패턴과 코드 블록을 골라 조합하는 방식을 씁니다.

## 언제 이 스킬을 쓰나

- 사용자가 Slack 이벤트(메시지/스레드/리액션/슬래시커맨드)를 Notion DB 페이지로 옮기는 봇을 만들고 싶어할 때
- Notion 속성 변경(상태, 날짜 등)을 감지해서 Slack 스레드에 자동 알림을 보내고 싶어할 때
- 위 둘을 조합한 양방향 연동 (요청 수집, 회의록 기록, 태스크 트래커 등) 을 만들고 싶어할 때

## 이 스킬이 제공하지 않는 것

- **자동 스캐폴드 명령** — 사용자 입력을 받아 프로젝트 디렉토리를 자동 생성하지 않습니다. 필요한 블록을 골라 사용자 리포에 복사·편집하면서 만듭니다.
- **Notion DB 자동 생성** — `notion-schema-guide.md`에 필요한 속성 정의만 문서화되어 있습니다. 사용자가 자기 Notion 워크스페이스에 수동으로 DB를 만듭니다.
- **특정 도메인의 분류 규칙** — 유형/구분 키워드, 담당자 매핑 등은 사용자의 팀 상황에 맞게 대화하며 정의합니다.

## 작업 흐름

사용자가 이 스킬을 트리거하면 다음 순서로 진행합니다.

### 1) 인터뷰 — 무엇을 만들지 좁히기

아래 질문을 한 번에 다 던지지 말고, 사용자의 초기 설명에서 빠진 것만 골라서 물어봅니다:

1. **방향** — Slack→Notion 단방향? Notion→Slack 단방향? 양방향?
2. **Slack 입력 채널** — 특정 공개 채널 하나? 여러 채널? DM?
3. **Slack 이벤트 종류** — 아래 중 어떤 것들이 필요한가? (복수 선택)
   - 최상위 메시지 → Notion 페이지 생성
   - 스레드 댓글 → 기존 페이지에 블록 추가
   - 리액션 → 페이지 속성 변경 (예: ✅ → 완료)
   - 슬래시 커맨드 + 모달 → 구조화된 입력
   - 첨부 이미지 → Notion image 블록으로 삽입
4. **Notion DB 속성** — 제목/상태 외에 어떤 속성이 있나? 담당자는 person인지 text인지?
5. **Notion→Slack 알림 트리거** — 어떤 속성이 바뀔 때 알림? (상태, 날짜, 담당자 등)
6. **도메인 분류 로직** — 메시지 유형/카테고리를 자동 분류할 필요가 있나? 있다면 키워드는?
7. **담당자 자동 지정** — 규칙이 있나? (멘션→그 사람, 특정 유형→고정인, 기본→디폴트)

사용자가 이미 설명한 내용은 다시 묻지 말고 이해한 내용을 요약해 확인받은 뒤 빠진 것만 물어봅니다.

### 2) 블록 선택 — 필요한 것만 골라 복사

아래 표에서 사용자 요구에 맞는 블록을 고릅니다. 각 블록은 독립적인 Python 파일이며, `# CUSTOMIZE:` 주석이 달린 곳을 사용자 로직에 맞춰 수정합니다.

| 블록 | 경로 | 언제 필요한가 |
|------|------|--------------|
| 메시지 → 페이지 | `blocks/slack-to-notion/message-to-page.py` | 채널에 올라온 최상위 메시지를 Notion 페이지로 만들 때 |
| 스레드 → 블록 추가 | `blocks/slack-to-notion/thread-to-blocks.py` | 기존 Notion 페이지 본문에 스레드 댓글을 누적 기록할 때 |
| 리액션 → 속성 변경 | `blocks/slack-to-notion/reaction-to-status.py` | 특정 이모지 리액션을 상태/체크박스 등 속성 변경으로 매핑할 때 |
| 슬래시 커맨드 + 모달 | `blocks/slack-to-notion/slash-command-modal.py` | `/커맨드` 로 Block Kit 모달을 띄워 구조화된 입력을 받을 때 |
| 이미지 첨부 | `blocks/slack-to-notion/image-attachment.py` | 메시지 첨부 이미지를 Notion image 블록으로 임베드할 때 (User Token 필요) |
| 상태 폴러 | `blocks/notion-to-slack/status-poller.py` | 특정 상태로 변경된 페이지를 감지해 Slack 스레드에 알림 보낼 때 |
| 날짜 변경 알림 | `blocks/notion-to-slack/date-change-notifier.py` | 완료예정일/마감일 같은 날짜 속성 변경을 감지해 알림 보낼 때 |
| TS↔page_id 매핑 | `blocks/shared/state-manager.py` | Slack 메시지 ts와 Notion page_id를 양방향 매핑해야 할 때 (거의 항상 필요) |
| 자연어 기한 파싱 | `blocks/shared/deadline-parser.py` | 자유 텍스트에서 "내일", "이번주 금요일" 같은 날짜 표현을 추출할 때 |
| 멘션 추출 | `blocks/shared/mention-extractor.py` | 메시지 본문에서 `<@U...>` Slack ID를 뽑아 담당자 자동 지정 등에 쓸 때 |
| 봇 진입점 | `blocks/shared/bot-entrypoint.py` | `main.py`로 쓸 Socket Mode 부트스트랩 스켈레톤 (대부분 필요) |
| `.env.example` | `blocks/shared/env-example.txt` | 환경변수 템플릿 |

### 3) 조합 — 사용자 리포에 파일 생성

선택한 블록을 사용자의 프로젝트 디렉토리에 복사하고, `# CUSTOMIZE:` 포인트를 대화하며 채워 넣습니다. 전형적인 레이아웃:

```
user-project/
├── main.py                    # bot-entrypoint.py 기반
├── config.py                  # 환경변수, 상수
├── modules/
│   ├── slack_handler.py       # 선택한 slack-to-notion 블록들 병합
│   ├── notion_client.py       # Notion API 래퍼 (notion-patterns.md 참고)
│   ├── notion_poller.py       # 선택한 notion-to-slack 블록 병합
│   └── state_manager.py       # shared/state-manager.py
├── data/                      # JSON 매핑 파일들
├── .env
└── requirements.txt
```

**주의**: 블록은 "같은 이벤트 핸들러 안에서 쓰일 것"을 전제로 짰기 때문에, 여러 slack-to-notion 블록을 고르면 하나의 `@app.event("message")` 핸들러에 합쳐야 합니다. 블록 파일 상단의 `# 병합 가이드` 주석을 따릅니다.

### 4) Notion DB 스키마 안내

사용자 요구사항에 맞는 DB 속성 정의를 `reference/notion-schema-guide.md` 기반으로 뽑아서 알려줍니다. Claude가 DB를 직접 생성하지 않고, "이 속성들을 이 타입으로 만드세요" 가이드만 제공합니다 (사용자가 자기 토큰으로 자기 워크스페이스에 만들도록).

### 5) Slack App 설정 안내

선택한 블록에 필요한 OAuth scope와 이벤트 구독 목록을 `reference/slack-setup.md` 표에서 추려서 사용자에게 알려줍니다. Socket Mode는 기본 전제.

## 참고 문서

- `reference/architecture.md` — Socket Mode 이벤트 흐름, 폴링 구조, 인메모리+파일 매핑 패턴
- `reference/slack-setup.md` — 필요 기능별 Bot/User Token scope 매트릭스, Socket Mode 설정
- `reference/notion-patterns.md` — `pages.create` / `databases.query` / `blocks.children.append` 사용 패턴, property 타입별 payload 예시
- `reference/notion-schema-guide.md` — 표준 DB 속성 정의 (제목/상태/담당자/날짜 등), 선택 가이드

## 원칙

- **도메인 로직은 블록에 하드코딩하지 말고** `config.py`의 매핑 테이블이나 JSON 파일로 분리한다. 팀이 바뀌어도 코드 수정 없이 운영 가능하게.
- **블록을 그대로 복사하지 말고** 사용자의 실제 DB 스키마/채널/이모지에 맞춰 편집한다. placeholder (`# CUSTOMIZE:` 주석)를 남기지 말 것.
- **사용자의 Notion/Slack 토큰은 사용자 환경변수에서만** 읽는다. 스킬이 토큰을 요구하거나 저장하지 않는다.
- **완성 후 실행 안내**: `pip install -r requirements.txt` → `.env` 작성 → `python main.py` 순서로 돌리도록 README 수준의 안내를 마지막에 제공한다.
