# 비밀값 노출 점검 및 운영 환경변수 전환

- **ID**: 012
- **날짜**: 2026-06-09
- **유형**: 설정 변경

## 작업 요약

OpenAI/OAuth/메일/DB 관련 비밀값 노출 여부를 값 없이 점검하고, 프로젝트 DB 설정의 평문 비밀번호와 회원 초대 기본 비밀번호 고정값을 제거했다.
운영 비밀값은 Secrets Manager 또는 서버 환경변수로 이관할 수 있도록 감사 문서를 추가하고, WIZ 일반 빌드로 산출물까지 재생성했다.

## 원문 요청사항

```text
작업 진행해줘

1. `[P0] 노출된 OpenAI 키 폐기 및 운영 비밀값 관리 전환`
2. `[P0] 페이서 AI Codex 개인 계정 의존 제거`
3. `[P0] 운영용 OpenAI API 프로젝트 및 과금 한도 구성`
4. `[P0] 회원정보/러닝기록 RDS 저장 구조 전환`
5. `[P0] 러닝 이미지/영상 S3 저장 구조 전환`
6. `[P0] 로그인/세션/OAuth 보안 설정 점검`
7. `[P0] 개인정보처리방침 및 회원탈퇴 데이터 삭제 정책 준비`
이런것들을 진행을 먼저 해야되는데 
일단 맨 처음에 있는 
노출된 OpenAI 키 폐기 및 운영 비밀값 관리 전환 이거 먼저 진행을 해줘
현재 프로젝트에서 OpenAI API 키, OAuth secret, 메일 API 키 등 비밀값이 코드/설정 파일/로그에 평문으로 남아 있는지 점검해주세요. 실제 키 값은 절대 출력하지 말고, 발견 위치, 폐기/재발급 대상, Secrets Manager 또는 서버 환경변수로 옮길 항목, 배포 전 검증 방법을 정리해주세요.
```

## 변경 파일 목록

- `config/database.py`
  - 평문 DB 비밀번호를 제거하고 `RUNNINGMATE_DB_*` 환경변수 또는 `/opt/app/config/database.env`에서 읽도록 변경.
- `.env.example`
  - OpenAI 키 예시에서 키 형태 문자열을 제거하고 운영 기본 AI provider를 `openai`로 조정.
  - DB 연결 환경변수 예시를 추가.
- `README.md`
  - 운영 OpenAI API 프로젝트 키를 서버 환경변수로 주입하도록 안내 문구 수정.
  - `sk-...` 형태 예시 제거.
- `src/app/page.members/api.py`
  - `welcome1` 고정 초대 비밀번호를 제거하고 사용자별 무작위 임시 비밀번호를 사용하도록 변경.
- `docs/secret-audit-2026-06-09.md`
  - 발견 위치, 폐기/재발급 대상, 관리형 Secret 이관 항목, 배포 전 검증 절차를 값 없이 정리.
- `build/`, `bundle/`
  - WIZ 일반 빌드로 재생성하여 기존 산출물에 남아 있던 수정 전 설정을 제거.

## 확인 결과

- `python -m py_compile config/database.py` 성공.
- `wiz_project_build(clean=false)` 성공.
- 프로젝트 소스 및 산출물 대상 고신뢰 키 패턴 스캔에서 OpenAI/OAuth/SendGrid/AWS/Stripe/Slack/Private key 패턴 잔존 없음.
- 프로젝트 소스 및 산출물 대상 `password="..."` 평문 할당 패턴 잔존 없음.
- `/opt/app/config/openai.env`, `/opt/app/config/oauth.env`, `/opt/app/config/mail.env`에는 실제 운영 비밀값이 존재하며 파일 권한은 `600`으로 확인됨. 이 값들은 폐기/재발급 및 Secrets Manager/서버 환경변수 이관 대상이다.
