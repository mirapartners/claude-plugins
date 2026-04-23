# Notion DB 스키마 가이드

사용자가 자기 Notion 워크스페이스에 DB를 **수동으로** 만듭니다. 이 문서는 어떤 속성이 어떤 타입으로 필요한지 가이드.

## 작성 순서

1. Notion에서 새 페이지 생성 → `/database` 입력해 full-page database 생성
2. 아래 "표준 속성" 중 필요한 것만 골라 추가
3. `select`/`status` 속성은 옵션값을 **수동으로** 넣어야 함 (Claude가 API로 옵션까지 자동 생성하기 어려움)
4. Integration을 이 DB에 연결 (`•••` → Connections → 선택)

## 표준 속성 테이블

쓰임새별로 골라 조합합니다. 이름은 팀에 맞게 바꿔도 OK — 단, 블록 코드의 property 이름도 같이 바꿔야 함.

### 필수

| 이름 | 타입 | 비고 |
|------|------|------|
| (제목) | `title` | 어느 DB든 1개 필수. 예: "요청 내용", "회의록 제목", "태스크 이름" |
| `Slack TS` | `rich_text` | Slack 메시지 ts 저장. 중복 방지 + fallback 검색 키 |
| `슬랙 URL` | `url` | 원본 Slack 메시지 permalink |

### 상태 추적용 (대부분 함께)

| 이름 | 타입 | 옵션 예시 |
|------|------|-----------|
| `상태` | `status` | "시작 전" / "진행 중" / "완료" (3그룹 Status 타입) |
| `유형` | `select` | "수정", "오류", "개선", "신규", ... |
| `구분 유형` | `select` | 도메인별 카테고리 |

**`select` vs `status`**: 둘 다 단일 선택. 차이는 Status 타입은 "To-do / In progress / Complete" 3그룹으로 묶여있고 Kanban 보드 뷰와 연동됨. 단순 분류면 select, 워크플로면 status.

### 사람 / 요청자

| 이름 | 타입 | 비고 |
|------|------|------|
| `요청자` | `rich_text` | Slack 사용자 실명 저장 (Notion 계정 없어도 됨) |
| `담당자` | `people` | Notion 사용자 ID 필요. Slack ID → Notion ID 매핑 테이블로 해결 |

**왜 요청자는 text이고 담당자만 people인가?** — 채널 메시지 작성자는 Notion 계정이 없을 수도 있음(외부 요청자 포함). 담당자는 팀 내부니까 모두 Notion 계정 있다고 가정.

### 날짜

| 이름 | 타입 | 누가 채우나 |
|------|------|-------------|
| `등록일` | `date` | 자동 (메시지 타임스탬프) |
| `요청 기한` | `date` | 자동 (자연어 기한 파싱) 또는 수동 |
| `완료 예정일` | `date` | 수동 (담당자가 기입 → poller가 감지해 Slack 알림) |
| `완료일` | `date` | 자동 ("완료" 상태 변경 시 오늘 날짜) |

기한 관련 필드가 많으면 Notion 타임라인 뷰로 로드맵처럼 보기 좋음.

### 이미지 / 파일

별도 속성 없음. 페이지 **본문**에 `image` 블록으로 삽입합니다 (속성 X, 블록 O). 파일 속성은 Notion 내부 파일 호스팅을 쓰므로 외부 URL 임베드 용도에는 맞지 않음.

## 유스케이스별 추천 스키마

### (A) 요청 수집 봇 (현재 예시 프로젝트와 동일)

```
요청 내용 (title)
유형 (select: 수정 / 오류 / 개선 / 신규 / 데이터 관련)
구분 유형 (select: 도메인별)
상태 (status: 시작 전 / 진행 중 / 완료)
요청자 (rich_text)
담당자 (people)
등록일 (date)
요청 기한 (date)
완료 예정일 (date)
완료일 (date)
슬랙 URL (url)
Slack TS (rich_text)
```

### (B) 회의록 수집 봇

```
제목 (title)
주제 (multi_select: 기획 / 개발 / 운영 / ...)
참석자 (people)
회의 일자 (date)
작성자 (rich_text)
슬랙 URL (url)
Slack TS (rich_text)
```

### (C) 간단한 태스크 트래커

```
태스크 (title)
상태 (status: To-do / Doing / Done)
담당자 (people)
마감일 (date)
Slack TS (rich_text)
```

## 사용자에게 전달할 가이드 예시

Claude가 사용자에게 안내할 때 이런 형식으로:

> 다음 속성으로 Notion DB를 만들어주세요:
>
> 1. **요청 내용** — Title 타입 (기본)
> 2. **상태** — Status 타입 (옵션: `시작 전`, `진행 중`, `완료`)
> 3. **담당자** — Person 타입
> 4. **요청 기한** — Date 타입
> 5. **Slack TS** — Text 타입 (봇이 내부용으로 쓰는 키, 숨김 처리 추천)
> 6. **슬랙 URL** — URL 타입
>
> 만든 후 DB 페이지 우상단 `•••` → **Connections** → 아까 만든 integration을 연결해주세요.
> 마지막으로 DB URL에서 ID 부분(32자 hex)을 복사해 `.env`의 `NOTION_DATABASE_ID`에 넣어주세요.

## 속성 이름을 바꾼 경우

블록 코드의 property 이름도 같이 바꿔야 합니다. 찾기 쉽게 `notion_client.py` 상단에 상수로 모아두는 걸 권장:

```python
# notion_client.py 상단
PROP_TITLE = "요청 내용"
PROP_STATUS = "상태"
PROP_ASSIGNEE = "담당자"
PROP_DEADLINE = "요청 기한"
PROP_SLACK_TS = "Slack TS"
PROP_SLACK_URL = "슬랙 URL"
```

사용하는 곳에서 리터럴 대신 상수 참조. 스키마 이름 바뀌면 한 곳만 수정.
