---
name: upload-afterservice
description: Use when the user wants to upload portfolio company documents (financial statements, shareholder registers, corporate registry, insurance, etc.) to mirafaan for post-investment management. Triggers include "재무제표 업로드", "미라판 업로드", "사후관리 업로드", "파일 업로드", "full_audit 실행", "주주명부 업로드", "등기부 업로드".
---

사후관리 피투자기업 자료를 Google Drive에서 찾아 미라판에 일괄 업로드합니다.
파일명 키워드로 유형을 자동 분류하여 각 input에 업로드합니다.

파일 유형 분류 기준:
- 재무/손익/BS/IS/balance/income/표준재무 → finance_file (재무제표)
- 주주 → shareholder_file (주주명부)
- 등기 → certify_file (등기부등본)
- 보험/4대/사대 → insurance_file (4대보험)
- 그 외 → etc_file (기타자료)

## 사전 확인 (반드시 사용자에게 물어볼 것)

다음 정보를 사용자에게 한 번에 모아서 질문하세요:

1. **작업 디렉토리** — full_audit.py가 있는 프로젝트 폴더 경로
2. **Drive 부모 폴더 ID** — 이번에 업로드할 GP 파일들이 있는 Google Drive 폴더 ID
   - [완료] 태그가 붙은 폴더는 스킵됨. 스캔 대상 폴더에 태그가 없는지 확인 요청
3. **미라판 프로그램 코드** — 기본값 U8IgUOsKzpgjK (사후관리 화면). 다른 프로그램이면 알려달라고 요청
4. **업로드 대상 회사 목록 기준** — finance_upload_result.json의 uploaded 리스트 사용 여부, 또는 별도 목록이 있는지 확인

## 진행 절차

사용자 답변을 받은 후:

### 1단계: full_audit.py 설정 확인

{작업디렉토리}/full_audit.py 파일을 읽어서 아래 값이 사용자가 답한 내용과 일치하는지 확인하세요:
- PARENT_FOLDER_ID: Drive 부모 폴더 ID
- REAL_URL: 미라판 프로그램 코드 포함 여부

일치하지 않으면 파일을 수정하세요.

### 2단계: 드라이런으로 진단 먼저

사용자에게 안내하고 동의를 받으세요:

> 실행 예정: python full_audit.py --dry-run
> 실제 업로드 없이 대기중 회사 목록만 출력합니다.
> 실행할까요?

동의하면 Bash로 실행합니다.

### 3단계: 드라이런 결과 요약 후 본실행 확인

드라이런 결과(대기중 회사 수, 목록)를 정리해서 보여주세요. 그리고:

> 본실행 예정: python full_audit.py
> 위 N개 회사에 파일을 업로드합니다. 파일명으로 유형을 자동 분류하여 각 항목에 업로드합니다.
> 실행할까요?

동의하면 Bash로 실행합니다.

### 4단계: 결과 보고

실행 완료 후 full_audit_result.json을 읽어서 결과를 요약하세요:
- 완료 N개 / 실패 N개 / 파일없음 N개 / hash없음 N개
- 실패나 누락이 있으면 원인과 다음 조치를 제안하세요

## 주의사항

- hash_id는 절대 고정하지 말 것: 회사별로 달라질 수 있음. full_audit.py가 보기 버튼 클릭으로 매번 동적 추출
- [완료] 폴더는 스킵: 사용자가 수기로 태그 기재, 이미 끝난 폴더
- U8IgUOsKzpgjK와 Qv8p2lwYXm1Bj는 완전히 다른 미라판 프로그램: hash_id 서로 호환 안 됨
- 같은 유형의 파일이 복수이면 ZIP 압축 후 업로드 (full_audit.py가 자동 처리)
- 제출하기 버튼: button.confirm_submit_open 클릭 후 button.basic_info_save_btn 클릭
