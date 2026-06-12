# 001. P2 코드 보안 작업 및 개인 서버 준비 템플릿 추가

- 날짜: 2026-06-10
- 요청: "그러면 일단 너가 할 수 잇는 작업 순서대로 작업 진행해줘"
- 리뷰 ID: `eplsrldlzbjzpstdfzvzaprwbkaozrlo`

## 변경 파일

- `src/model/security.py`
- `src/model/oauth.py`
- `src/controller/admin.py`
- `src/app/page.members/app.json`
- `src/app/page.members/api.py`
- `src/route/api.ai-config/controller.py`
- `src/route/api.auth.login/controller.py`
- `src/route/api.auth.logout/controller.py`
- `src/route/api.auth.password/controller.py`
- `src/route/api.auth.account/controller.py`
- `src/route/api.run-images/controller.py`
- `src/route/api.run-media/controller.py`
- `src/route/api.runs.media/controller.py`
- `src/route/api.parse-image/controller.py`
- `docs/private-server-p2-security-plan-2026-06-10.md`
- `ops/nginx-runningmate.conf.example`
- `scripts/setup-private-server-firewall.sh`
- `scripts/encrypt-runningmate-backup.sh`
- `devlog.md`
- `devlog/2026-06-10/001-p2-code-security-and-private-server-templates.md`

## 변경 내용

- 공통 보안 모델에 민감정보 마스킹, 안전 로그 출력, JSONL 감사 로그 저장 기능을 추가했다.
- 이메일, 토큰, API 키, 비밀번호, 일기/민감 본문 계열 값을 로그/감사 로그에서 마스킹하도록 했다.
- OAuth 로그와 비밀번호 재설정 메일 로그가 공통 마스킹 유틸을 사용하도록 변경했다.
- `user.role == "admin"` 기준 관리자 판별과 `require_admin()` guard를 추가했다.
- `/members` 페이지를 `admin` 컨트롤러로 전환하고, 회원 목록/초대/삭제 API에 관리자 guard와 감사 로그를 추가했다.
- AI 설정 POST 관리자 작업에 감사 로그를 추가했다.
- 로그인, 로그아웃, 비밀번호 변경, 계정 삭제, 파일 접근 거부, 파일 업로드, 이미지 업로드 이벤트 감사 로그를 추가했다.
- 개인 서버 P2 보안 계획 문서를 추가했다.
- Nginx TLS 리버스 프록시 예시 설정을 추가했다.
- UFW 방화벽 dry-run 스크립트를 추가했다.
- 백업 산출물 암호화 스크립트를 추가했다.

## 확인 결과

- `python3 -m py_compile`로 변경 Python 파일 문법 검사를 통과했다.
- `bash -n scripts/setup-private-server-firewall.sh` 성공.
- `bash -n scripts/encrypt-runningmate-backup.sh` 성공.
- `git diff --check` 성공.
- `wiz_project_build(clean=false)` 성공.
- `Security.mask_sensitive()` 단위 확인 성공.
- Python 3.12 pyc 검증 산출물은 정리했다.
