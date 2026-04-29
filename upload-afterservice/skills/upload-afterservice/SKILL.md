---
name: upload-afterservice
description: Use when the user wants to upload portfolio company documents to mirafaan for post-investment management. Triggers include "재무제표 업로드", "미라판 업로드", "사후관리 업로드", "파일 업로드", "full_audit 실행", "주주명부 업로드", "등기부 업로드", "upload-afterservice".
---

사후관리 피투자기업 자료를 미라판에 업로드합니다.

## 사전 확인 (반드시 사용자에게 물어볼 것)

아래 내용을 한 번에 모아서 물어보세요. 전문 용어 없이 쉽게 질문하세요:

1. **스크립트 폴더 위치** — `full_audit.py` 파일이 있는 폴더 경로를 알려주세요.
   (예: `C:\Users\홍길동\Desktop\사후관리 업로드`)

2. **파일이 있는 Google Drive 폴더 링크** — 업로드할 파일들이 들어있는 Google Drive 폴더의 URL을 알려주세요.
   - `[완료]`라고 표시된 폴더는 이미 끝난 폴더라서 자동으로 건너뜁니다.
   (예: `https://drive.google.com/drive/folders/1AhOkM3wHx3AyZTPC54muWfqTCdZrFHn5`)

3. **미라판 페이지 URL** — 업로드할 미라판 화면의 주소를 알려주세요.
   브라우저에서 해당 페이지를 열고 주소창의 URL을 그대로 붙여넣어 주세요.
   (예: `https://mirafaan.com/mira-adm/after-service/U8IgUOsKzpgjK/all-report`)

4. **이번에 업로드할 회사 목록** — 특정 회사만 업로드할지, 아니면 아직 업로드 안 된 회사를 자동으로 찾아서 전부 할지 알려주세요.

## 진행 절차

사용자 답변을 받은 후:

### 1단계: 설정 확인 및 수정

사용자가 알려준 정보로 `{스크립트 폴더}/full_audit.py`를 읽어서 아래 값을 확인하세요:
- `PARENT_FOLDER_ID` — Drive 폴더 URL에서 마지막 `/` 이후 문자열이 ID입니다. 일치하지 않으면 수정하세요.
- `REAL_URL` — 사용자가 알려준 미라판 페이지 URL과 일치하는지 확인하세요. 다르면 수정하세요.

### 2단계: 미리보기 실행

사용자에게 이렇게 안내하고 동의를 받으세요:

> 먼저 실제 업로드 없이 **어떤 회사가 누락됐는지 목록만 확인**해볼게요.
> 브라우저가 잠깐 열렸다 닫힐 수 있습니다.
> 진행할까요?

동의하면 아래를 Bash로 실행하세요:
```
cd "{스크립트 폴더}" && python full_audit.py --dry-run
```

### 3단계: 결과 확인 후 업로드 실행

미리보기 결과(누락 회사 수, 목록)를 정리해서 보여주세요. 그리고:

> 총 N개 회사에 파일을 업로드할 예정입니다.
> 파일 종류(재무제표/주주명부/등기부 등)는 파일명을 보고 자동으로 구분해서 올립니다.
> 브라우저가 열리고 자동으로 진행됩니다. 완료까지 시간이 걸릴 수 있습니다.
> 지금 시작할까요?

동의하면 아래를 Bash로 실행하세요:
```
cd "{스크립트 폴더}" && python full_audit.py
```

### 4단계: 결과 보고

완료 후 `full_audit_result.json`을 읽어서 아래 형식으로 요약하세요:
- 업로드 완료: N개 회사
- 실패: N개 (있으면 회사명과 원인)
- 파일 없음: N개 (Drive에서 해당 파일을 찾지 못한 경우)

실패나 누락이 있으면 다음 조치를 제안하세요.

## 내부 처리 규칙 (항상 준수)

- **hash_id 고정 금지** — 매번 미라판 "보기" 버튼 클릭으로 동적 추출. 이전에 저장한 값 재사용 불가
- **[완료] 폴더 스킵** — 사용자가 직접 표시한 완료 폴더, 건드리지 않음
- 미라판 URL이 달라지면 hash_id도 달라짐 — URL마다 별개 시스템
- 같은 종류 파일 여러 개면 ZIP으로 묶어서 업로드 (자동 처리)
- 제출 버튼 순서: `button.confirm_submit_open` 클릭 → `button.basic_info_save_btn` 클릭
