# slack-notion-bridge

Slack과 Notion을 잇는 봇을 만들 때 참고하는 **빌딩블록 키트**입니다. 완성된 템플릿이 아니라 필요한 조각을 골라 조합하는 방식.

## 언제 쓰나

다음 같은 봇을 만들고 싶을 때 Claude에게 자연어로 요청하면 이 스킬이 자동 호출됩니다:

- 특정 Slack 채널 메시지를 Notion DB에 자동 기록
- Slack 스레드 댓글을 Notion 페이지 본문에 누적 기록
- 특정 이모지 리액션으로 Notion 상태 변경
- `/커맨드` 슬래시 커맨드 + 모달로 구조화 입력
- Notion 상태/날짜 속성 변경 시 Slack 스레드 자동 알림

## 사용 예시

Claude Code에서:

```
> Slack 채널에 올라온 요청 메시지를 노션에 자동으로 기록하는 봇 만들고 싶어
```

또는

```
> 노션에서 상태가 완료로 바뀌면 원래 슬랙 메시지 스레드에 알림 가게 해줘
```

Claude가 스킬을 자동 로드 → 필요한 정보(채널, DB 스키마, 도메인 규칙)를 질문 → 블록을 조합해 사용자 프로젝트에 코드를 작성해줍니다.

## 제공하는 것

```
skills/slack-notion-bridge/
├── SKILL.md                    # 인터뷰 플로우 + 블록 조합 가이드
├── reference/
│   ├── architecture.md         # Socket Mode + 폴링 구조
│   ├── slack-setup.md          # App scope 매트릭스
│   ├── notion-patterns.md      # API 사용 패턴
│   └── notion-schema-guide.md  # DB 속성 정의 가이드
└── blocks/
    ├── slack-to-notion/        # 메시지/스레드/리액션/모달/이미지
    ├── notion-to-slack/        # 상태 폴러, 날짜 변경 알림
    └── shared/                 # 매핑 매니저, 기한 파싱, 진입점 등
```

## 제공하지 않는 것

- **자동 프로젝트 스캐폴드 명령** — 사용자 리포에 블록을 복사하고 도메인 로직을 사용자와 대화로 채워넣는 방식
- **Notion DB 자동 생성** — `notion-schema-guide.md`에 스키마 가이드만 제공. 사용자가 자기 워크스페이스에 직접 DB 생성
- **Slack App 자동 등록** — `slack-setup.md` 가이드대로 사용자가 api.slack.com에서 직접 설정

## 전제

- Python 3.10+
- Slack Socket Mode 사용 (`SLACK_APP_TOKEN` 필수)
- Notion Integration이 대상 DB에 Connection으로 추가되어 있어야 함
- 이미지 블록 기능을 쓸 경우 `SLACK_USER_TOKEN` 추가 필요

## 참고 프로젝트

`#2-vc관리본부_개선사항요청` 채널용 요청 수집 봇이 이 스킬의 실제 구현 예시. (내부 리포)
