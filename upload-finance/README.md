# upload-finance

사후관리 피투자기업 자료를 Google Drive에서 찾아 미라판에 자동 업로드하는 스킬입니다.
재무제표뿐 아니라 주주명부, 등기부등본, 4대보험, 기타자료까지 파일명으로 유형을 자동 분류합니다.

## 설치

```
/plugin install upload-finance@mirapartners
```

## 사용법

Claude Code에서 입력:
```
/upload-finance
```

실행하면 Claude가 필요한 정보를 물어보고, 확인 후 자동으로 업로드를 진행합니다.

## 파일 유형 자동 분류

| 파일명 키워드 | 미라판 input | 설명 |
|------------|------------|------|
| 재무, 손익, BS, IS, balance, income, 표준재무 | finance_file | 재무제표 |
| 주주 | shareholder_file | 주주명부 |
| 등기 | certify_file | 등기부등본 |
| 보험, 4대, 사대 | insurance_file | 4대보험 |
| 그 외 | etc_file | 기타자료 |

같은 유형의 파일이 여러 개이면 자동으로 ZIP 압축 후 업로드합니다.

## 동작 흐름

1. **사전 확인**: Drive 폴더 ID, 미라판 프로그램 코드, 대상 회사 목록 기준 확인
2. **설정 점검**: full_audit.py 파라미터가 답변과 일치하는지 확인 및 수정
3. **드라이런**: python full_audit.py --dry-run 실행 후 대기중 회사 목록 미리 확인
4. **본실행**: 사용자 동의 후 python full_audit.py 실행
5. **결과 보고**: full_audit_result.json 읽어서 완료/실패 요약

## 주요 주의사항

- hash_id는 고정하지 않음: 매번 보기 버튼 클릭으로 동적 추출
- [완료] Drive 폴더는 스킵 (사용자가 수기로 태그)
- 미라판 두 URL(U8IgUOsKzpgjK / Qv8p2lwYXm1Bj)은 완전히 다른 프로그램 - 혼용 금지

## 의존 스크립트

| 파일 | 역할 |
|------|------|
| full_audit.py | 전수조사 + 업로드 메인 스크립트 |
| modules/browser.py | Selenium 드라이버 생성 |
| modules/login.py | 미라판 로그인 |
| modules/drive_scanner.py | Google Drive 파일 스캔 |
| modules/uploader.py | 파일 다운로드 + 업로드 |
| modules/file_matcher.py | 회사명 fuzzy 매칭 |
