# Mira DX Claude Plugins

사내 Claude Code 플러그인 마켓플레이스.

## 설치 (팀원용)

Claude Code를 열고 아래 명령을 한 줄씩 입력하세요:

```
/plugin marketplace add mirapartners/claude-plugins
/plugin install slack-notion-bridge@mirapartners
```

설치 후 Claude Code를 재시작하면 플러그인이 활성화됩니다.

## 수록된 플러그인

| 이름 | 설명 |
|------|------|
| [`slack-notion-bridge`](./slack-notion-bridge) | Slack ↔ Notion 연동 봇을 만들 때 참고하는 빌딩블록 키트 |
| [`upload-afterservice`](./upload-afterservice) | 사후관리 피투자기업 자료를 Google Drive에서 받아 미라판에 자동 업로드 |

## 업데이트

```
/plugin marketplace update mirapartners
/plugin upgrade upload-afterservice@mirapartners
```

## 새 플러그인 추가하기

1. repo 루트에 `<plugin-name>/` 디렉토리 생성
2. `<plugin-name>/.claude-plugin/plugin.json` 작성 (`name`, `version`, `description`)
3. 필요한 스킬/커맨드/에이전트 배치:
   - Skills: `<plugin-name>/skills/<skill-name>/SKILL.md`
   - Commands: `<plugin-name>/commands/<command-name>.md`
   - Agents: `<plugin-name>/agents/<agent-name>.md`
4. 루트 `.claude-plugin/marketplace.json` 의 `plugins` 배열에 항목 추가
5. PR → 머지 → 팀원은 `/plugin marketplace update` 로 받음

## 참고

- Claude Code 공식 문서: https://code.claude.com/docs/en/plugin-marketplaces
