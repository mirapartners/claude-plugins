# 아키텍처 참고

Slack ↔ Notion 봇의 전형적인 런타임 구조.

## 런타임 구성

```
┌─────────────────────────────────────────────────────────────┐
│  Python 프로세스 (단일, 상시 실행)                              │
│                                                               │
│  ┌─────────────────┐         ┌────────────────────┐          │
│  │ Socket Mode     │         │ Notion Poller      │          │
│  │ Handler (메인)  │         │ (daemon thread)    │          │
│  │                 │         │                    │          │
│  │ Slack 이벤트    │         │ 1분마다 Notion DB  │          │
│  │ 수신 및 처리    │         │ 조회 → 변경 감지   │          │
│  └────────┬────────┘         └─────────┬──────────┘          │
│           │                            │                      │
│           ▼                            ▼                      │
│  ┌─────────────────────────────────────────────┐             │
│  │  공유 자원                                    │             │
│  │  - NotionClient (API 래퍼)                    │             │
│  │  - StateManager (ts↔page_id 매핑)             │             │
│  │  - app.client (Slack WebClient)               │             │
│  └─────────────────────────────────────────────┘             │
└─────────────────────────────────────────────────────────────┘
         ▲                                    │
         │ Socket Mode                        │ HTTPS
         │ WebSocket                          │
         ▼                                    ▼
    ┌─────────┐                          ┌─────────┐
    │  Slack  │                          │  Notion │
    └─────────┘                          └─────────┘
```

왜 **Socket Mode**인가 — HTTP Events API는 공인 URL이 필요하지만 Socket Mode는 아웃바운드 WebSocket만 쓰면 돼서 사내 NAT 환경에서 바로 돌림. `SLACK_APP_TOKEN` (xapp-) 필수.

왜 **폴링**인가 — Notion은 웹훅이 없음. 1분 주기 DB `query` 로 변경을 감지하고, 이미 알린 건은 파일에 기록해 중복 방지.

## Slack → Notion 이벤트 흐름

```
Slack 메시지 이벤트
    │
    ▼
@app.event("message")
    │
    ├─ 대상 채널 필터링 (config.SLACK_CHANNEL_ID)
    ├─ 봇 메시지/수정/삭제 subtype 필터링
    │
    ├─ 최상위 메시지 (thread_ts 없음)
    │    │
    │    ├─ state.has(ts) → 중복 처리 방지
    │    ├─ message_parser → 제목/유형/구분/이미지 추출
    │    ├─ extract_mentions → 멘션된 사용자 ID
    │    ├─ assignee_router → 담당자 결정 (도메인 규칙)
    │    ├─ files.sharedPublicURL → 이미지 공개 URL 획득 (이미지 있을 때)
    │    ├─ notion.create_request_page → 페이지 생성
    │    └─ state.set(ts, page_id) → 매핑 저장
    │
    └─ 스레드 댓글 (thread_ts 존재, ts ≠ thread_ts)
         │
         ├─ state.get(thread_ts) → 매핑된 page_id 조회
         │    └─ 없으면 fallback: notion.find_page_by_slack_ts
         ├─ parse_deadline → 날짜 추출되면 notion.update_page_deadline
         └─ notion.append_thread_log → 본문에 paragraph 블록 추가
```

## Notion → Slack 이벤트 흐름

```
NotionPoller (daemon thread, 60초 주기)
    │
    ├─ notion.query_pages_by_status("완료")
    │    └─ 각 페이지:
    │         ├─ _notified_status[page_id] == "완료" → skip
    │         ├─ 완료일 비었으면 오늘 날짜로 세팅
    │         ├─ page의 Slack TS → slack.chat_postMessage(thread_ts=...)
    │         └─ _notified_status[page_id] = "완료" → notified_status.json 저장
    │
    └─ notion.query_pages_with_expected_date
         └─ 각 페이지:
              ├─ _notified_expected[page_id] == expected → skip
              ├─ 스레드 알림 발송
              └─ _notified_expected[page_id] = expected → notified_expected.json 저장
```

**중복 방지 핵심**: `notified_*.json` 파일이 "이미 알린 값"을 기록. 담당자가 완료를 해제했다가 다시 완료로 바꿔도 같은 값이면 재알림 없음. 필요 시 수동으로 해당 레코드를 지우고 재알림.

## 매핑 저장소

### StateManager — Slack ts ↔ Notion page_id

```python
# 메모리 dict + JSON 파일 이중 저장
# 읽기는 메모리 우선, 쓰기는 즉시 파일 동기화
{
    "1712345678.123456": "abcd1234-...",  # slack_ts: page_id
    ...
}
```

**Fallback 검색**: 메모리에 없으면 Notion DB를 `Slack TS` rich_text 속성으로 검색. 서버 재기동 후 JSON 파일 유실돼도 복구 가능.

### 알림 기록

```python
notified_status.json:   {page_id: "완료"}
notified_expected.json: {page_id: "2026-05-01"}  # 마지막 알림한 값
```

## 모듈 의존성 그래프

```
main.py
  ├─ config (전역 상수)
  ├─ NotionClient ──────────────┐
  ├─ StateManager ──────────┐   │
  ├─ AssigneeRouter         │   │
  ├─ register_handlers ─────┼───┤
  │                         │   │
  └─ NotionPoller ──────────┴───┘

message_parser  → config  (키워드 맵, REQUEST_TYPE_MAP)
slack_handler   → config, NotionClient, StateManager, AssigneeRouter, message_parser
notion_poller   → config, NotionClient, StateManager, slack_client
```

**의존성 주입 (DI)**: `main.py`가 모든 인스턴스를 생성해서 `register_handlers(app, notion, state, router)` 에 넘겨줌. 모듈 간 순환 import 없음, 테스트 시 mock 주입 용이.

## 에러 처리 철학

- **Slack 이벤트 핸들러 안에서 예외는 `logger.error(..., exc_info=True)` 로 남기고 삼킨다.** 한 이벤트의 예외가 봇 전체를 죽이면 안 됨.
- **Notion API 실패는 재시도하지 않는다.** (notion-client 내부에 기본 재시도 있음). 사용자가 로그 보고 수동 조치.
- **Notion DB 스키마 누락**은 시작 시점에 `_ensure_db_properties` 로 체크해 자동 추가 시도. 실패해도 기동은 계속.
