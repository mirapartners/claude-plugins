# Slack App 설정 가이드

## 앱 생성

1. https://api.slack.com/apps → **Create New App** → **From scratch**
2. App Name, Workspace 선택
3. **Socket Mode**는 기본 전제 — 사내 NAT 환경에서 공인 URL 없이 이벤트 수신 가능.

## 토큰 3종

| 토큰 | Prefix | 환경변수 | 용도 |
|------|--------|---------|------|
| Bot User OAuth Token | `xoxb-` | `SLACK_BOT_TOKEN` | 대부분의 API 호출 (메시지 전송, 사용자 조회 등) |
| App-Level Token | `xapp-` | `SLACK_APP_TOKEN` | Socket Mode WebSocket 연결 |
| User OAuth Token | `xoxp-` | `SLACK_USER_TOKEN` | **이미지 공개 처리 전용** (`files:write` user scope) |

### Bot Token 발급
**OAuth & Permissions** → **Install to Workspace** 클릭 → `xoxb-` 토큰 복사.

### App-Level Token 발급
**Basic Information** → **App-Level Tokens** → **Generate Token and Scopes**
- Scope: `connections:write` (Socket Mode 필수)
- 이름 지정 후 생성 → `xapp-` 토큰 복사.

### User Token 발급 (이미지 블록 필요할 때만)
**OAuth & Permissions** → **User Token Scopes**에 `files:write` 추가 → Reinstall → `xoxp-` 토큰 복사.

## Socket Mode 활성화

**Socket Mode** 메뉴 → **Enable Socket Mode** 토글 ON.

## 기능별 필요 Scope 매트릭스

선택한 빌딩블록에 따라 필요한 Bot Token scope가 다릅니다.

| 빌딩블록 | channels:history | channels:read | chat:write | commands | files:read | reactions:read | users:read | groups:history\* |
|---------|:---------------:|:-------------:|:---------:|:--------:|:----------:|:--------------:|:----------:|:----------------:|
| message-to-page | ✓ | ✓ | ✓ | | | | ✓ | (△) |
| thread-to-blocks | ✓ | | ✓ | | | | ✓ | (△) |
| reaction-to-status | | | | | | ✓ | | |
| slash-command-modal | | | ✓ | ✓ | | | ✓ | |
| image-attachment | | | | | ✓ | | | |
| status-poller | | | ✓ | | | | | |
| date-change-notifier | | | ✓ | | | | | |

\* **private 채널**에서도 봇이 동작해야 하면 `groups:history`, `groups:read` 도 추가.

**User Token Scope** (이미지 블록 쓸 때만):
- `files:write` — `files.sharedPublicURL` 호출용

## 이벤트 구독

**Event Subscriptions** → **Enable Events** → **Subscribe to bot events**:

| 이벤트 | 필요한 빌딩블록 |
|-------|---------------|
| `message.channels` | message-to-page, thread-to-blocks (public 채널) |
| `message.groups` | private 채널 쓸 때 |
| `reaction_added` | reaction-to-status |

## 슬래시 커맨드 등록

**Slash Commands** → **Create New Command**:
- Command: `/요청` (또는 원하는 이름)
- Short Description: "요청 등록"
- Request URL: Socket Mode면 **비워두거나 더미값**

모달 제출 응답도 Socket Mode로 받으므로 별도 설정 불필요.

## 봇 채널 초대

봇 계정을 대상 채널에 초대해야 `channels:history` 로 이벤트를 받을 수 있음.
```
/invite @YourBotName
```

## 채널 ID 획득

채널 이름 우클릭 → **View channel details** → 맨 아래 **Channel ID** 복사.
또는 채널 URL `https://{workspace}.slack.com/archives/C09XXXXXXXX` 의 `C09XXXXXXXX` 부분.

## 봇 표시 이름 커스터마이징

`chat_postMessage` 호출 시 `username` 파라미터로 덮어쓸 수 있습니다. (`chat:write.customize` scope 필요할 수 있음)

```python
client.chat_postMessage(channel=..., text=..., username="DX팀")
```

## 트러블슈팅

- **`not_in_channel` 에러** → 봇을 해당 채널에 `/invite` 로 초대.
- **`missing_scope` 에러** → OAuth & Permissions에서 scope 추가 → **Reinstall** 필수 (변경사항 반영).
- **이벤트가 안 들어옴** → Socket Mode 활성화 확인, Event Subscriptions에서 이벤트 체크 확인, 앱 재설치.
- **`already_public`** (`files.sharedPublicURL`) → 이미 공개된 파일. `files.info`로 `permalink_public` 조회해 `pub_secret` 추출 fallback.
- **`files.sharedPublicURL`이 `not_allowed_token_type`** → Bot Token으로 호출 불가. User Token 사용 필수.
