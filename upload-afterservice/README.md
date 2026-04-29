# upload-afterservice

사후관리 피투자기업 자료를 Google Drive에서 찾아 미라판에 자동 업로드하는 스킬입니다.
재무제표뿐 아니라 주주명부, 등기부등본, 4대보험, 기타자료까지 파일명으로 유형을 자동 분류합니다.

## 설치

```
/plugin install upload-afterservice@mirapartners
```

## 사용법

Claude Code에서 입력:
```
/upload-afterservice
```

## 파일 유형 자동 분류

| 파일명 키워드 | 미라판 input | 설명 |
|------------|------------|------|
| 재무, 손익, BS, IS, balance, income, 표준재무 | finance_file | 재무제표 |
| 주주 | shareholder_file | 주주명부 |
| 등기 | certify_file | 등기부등본 |
| 보험, 4대, 사대 | insurance_file | 4대보험 |
| 그 외 | etc_file | 기타자료 |

## 의존 스크립트

| 파일 | 역할 |
|------|------|
| full_audit.py | 전수조사 + 업로드 메인 스크립트 |
| modules/browser.py | Selenium 드라이버 생성 |
| modules/login.py | 미라판 로그인 |
| modules/drive_scanner.py | Google Drive 파일 스캔 |
| modules/uploader.py | 파일 다운로드 + 업로드 |
| modules/file_matcher.py | 회사명 fuzzy 매칭 |
