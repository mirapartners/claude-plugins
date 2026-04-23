# Notion API 사용 패턴

`notion-client` Python SDK 기준. `pip install notion-client`.

## Integration 연결

1. https://www.notion.so/profile/integrations → **New integration**
2. Associated workspace 선택 → 생성 → **Internal Integration Secret** 복사 (환경변수 `NOTION_TOKEN`, `ntn_` prefix)
3. 대상 DB 페이지 열기 → 우상단 `•••` → **Connections** → 만든 integration 선택해 연결

Integration이 연결되지 않은 DB는 API로 접근 불가 — `object_not_found` 에러가 뜹니다.

## DB ID 획득

DB를 전체 페이지로 열면 URL이 `https://www.notion.so/{workspace}/{DB_TITLE}-{DB_ID}?v=...`. `DB_ID`는 32자 hex (하이픈 없이). `NOTION_DATABASE_ID` 환경변수로 저장.

## 클라이언트 초기화

```python
from notion_client import Client

notion = Client(auth=NOTION_TOKEN)
```

## 페이지 생성 (`pages.create`)

```python
page = notion.pages.create(
    parent={"database_id": database_id},
    properties={
        # 속성 타입별 payload — 아래 표 참고
        "요청 내용": {"title": [{"text": {"content": title}}]},
        "유형": {"select": {"name": "개선"}},
        "상태": {"status": {"name": "시작 전"}},
        "등록일": {"date": {"start": "2026-04-23"}},
        "슬랙 URL": {"url": "https://..."},
        "Slack TS": {"rich_text": [{"text": {"content": "1712345678.123"}}]},
        "담당자": {"people": [{"id": notion_user_id}]},
    },
    children=[  # 페이지 본문 블록
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {"rich_text": [{"text": {"content": "상세 내용..."}}]},
        },
        {
            "object": "block",
            "type": "image",
            "image": {"type": "external", "external": {"url": "https://..."}},
        },
        {
            "object": "block",
            "type": "divider",
            "divider": {},
        },
        {
            "object": "block",
            "type": "heading_3",
            "heading_3": {"rich_text": [{"text": {"content": "스레드 로그"}}]},
        },
    ],
)
page_id = page["id"]
```

**길이 제한**: `rich_text.content`는 2000자 제한. 긴 텍스트는 자르거나 여러 블록으로 쪼갠다.

## 속성 타입별 payload

| 타입 | 읽기 | 쓰기 |
|------|------|------|
| `title` | `props["제목"]["title"][0]["plain_text"]` | `{"title": [{"text": {"content": s}}]}` |
| `rich_text` | `props["X"]["rich_text"][0]["plain_text"]` | `{"rich_text": [{"text": {"content": s}}]}` |
| `select` | `props["X"]["select"]["name"]` | `{"select": {"name": s}}` (미선택: `{"select": None}`) |
| `status` | `props["X"]["status"]["name"]` | `{"status": {"name": s}}` |
| `multi_select` | `[o["name"] for o in props["X"]["multi_select"]]` | `{"multi_select": [{"name": s1}, {"name": s2}]}` |
| `date` | `props["X"]["date"]["start"]` | `{"date": {"start": "2026-04-23"}}` (YYYY-MM-DD 또는 ISO) |
| `url` | `props["X"]["url"]` | `{"url": "https://..."}` |
| `checkbox` | `props["X"]["checkbox"]` | `{"checkbox": True}` |
| `people` | `[p["id"] for p in props["X"]["people"]]` | `{"people": [{"id": notion_user_id}]}` |
| `number` | `props["X"]["number"]` | `{"number": 42}` |

**`select` vs `status`**: `status`는 세 그룹(To-do/In progress/Complete)으로 묶인 select. Notion DB에서 속성 생성 시 "Status" 타입을 명시적으로 골라야 함. 코드에서는 `select` 대신 `status` 키를 씀.

## 페이지 업데이트 (`pages.update`)

```python
notion.pages.update(
    page_id=page_id,
    properties={
        "상태": {"status": {"name": "완료"}},
        "완료일": {"date": {"start": "2026-04-23"}},
    },
)
```

일부 속성만 보내면 나머지는 건드리지 않음 (patch 의미).

## DB 쿼리 (`databases.query`)

```python
# 상태가 "완료"인 페이지
result = notion.databases.query(
    database_id=database_id,
    filter={"property": "상태", "status": {"equals": "완료"}},
)
pages = result["results"]

# 날짜 비어있지 않음
result = notion.databases.query(
    database_id=database_id,
    filter={"property": "완료 예정일", "date": {"is_not_empty": True}},
)

# rich_text 정확 일치 (Slack TS로 페이지 찾기)
result = notion.databases.query(
    database_id=database_id,
    filter={"property": "Slack TS", "rich_text": {"equals": slack_ts}},
)
```

**Filter 타입별 연산자**는 [Notion 공식 문서](https://developers.notion.com/reference/post-database-query-filter) 참고.

**페이지네이션**: 결과가 많으면 `result["has_more"]`와 `result["next_cursor"]`로 다음 페이지 조회.
```python
result = notion.databases.query(database_id=..., start_cursor=result["next_cursor"])
```

## 블록 추가 (`blocks.children.append`)

```python
notion.blocks.children.append(
    block_id=page_id,  # 페이지 ID도 block_id로 사용 가능
    children=[
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {"rich_text": [{"text": {"content": f"[{timestamp}] {author}: {text}"}}]},
        },
    ],
)
```

**주의**: `children` 배열은 한 번에 최대 100개. 블록을 페이지 중간에 삽입하는 API는 없음 — 항상 끝에 append됨.

## DB 속성 자동 추가 (`databases.update`)

봇 시작 시 누락된 속성을 추가할 수 있음:

```python
db = notion.databases.retrieve(database_id=database_id)
props = db["properties"]

updates = {}
if "Slack TS" not in props:
    updates["Slack TS"] = {"rich_text": {}}
if "슬랙 URL" not in props:
    updates["슬랙 URL"] = {"url": {}}

if updates:
    notion.databases.update(database_id=database_id, properties=updates)
```

**단, `select`/`status`/`people` 같은 enum 속성은 옵션값까지는 자동 설정 어려움** — 사용자가 Notion UI에서 수동으로 options 추가해야 하는 경우가 많음. 스킬은 "이런 속성 만드세요" 가이드를 주고, 자동 추가는 `rich_text`/`url`/`date` 같은 옵션 없는 타입에만 쓴다.

## 멱등성 패턴

같은 Slack 메시지가 재전송되거나 봇이 재시작될 때 중복 페이지 방지:

1. **StateManager** (메모리 + JSON) 에 `ts` 존재 여부 먼저 체크
2. 없으면 Notion DB를 `Slack TS` 필드로 검색 (fallback)
3. 둘 다 없을 때만 새 페이지 생성

```python
if state.has(ts):
    return  # 이미 처리됨

page_id = notion.find_page_by_slack_ts(ts)
if page_id:
    state.set(ts, page_id)
    return  # Notion에 있음, 매핑만 복구

# 신규 생성
page_id = notion.create_request_page(...)
state.set(ts, page_id)
```

## 사람(people) 속성 세팅

`people` 속성은 Slack 사용자와 달리 **Notion 사용자 ID**를 요구. Slack ID → Notion ID 매핑이 필요:

```json
// data/slack_notion_user_map.json
{
  "U083FRA17T6": {
    "name": "문찬수",
    "notion_id": "abc12345-..."
  }
}
```

Notion user ID는 `users.list()` API로 조회하거나 Notion 워크스페이스 설정 → Members에서 각 사람 ID 확인. 매핑 테이블은 수동 관리.

## API 속도 제한

Notion은 초당 3요청 제한. 벌크 마이그레이션(백필)할 땐 요청 간 `time.sleep(0.5)` 정도 넣는다. 실시간 봇에서는 거의 부딪치지 않음.

## 에러 처리

- `APIResponseError` 에서 `.status` 와 `.code` 확인 가능.
- 400 (validation_error): payload 형식 틀림 — property 이름/타입 확인.
- 404 (object_not_found): DB나 페이지에 integration 연결 안 됨.
- 409 (conflict_error): 동시 업데이트 충돌, 재시도 가능.
