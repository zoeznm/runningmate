# 개인 서버 미디어 저장소·인증 보안·탈퇴 정책 P0 정리

## 사용자 요청

러닝 이미지/영상 개인 서버 파일 저장 및 백업 구조 전환, 로그인/세션/OAuth 보안 설정 점검, 개인정보처리방침 및 회원탈퇴 데이터 삭제 정책 준비를 순서대로 진행하고 작업 내용을 알려달라는 요청.

## 변경 파일

- `.env.example`: 개인 서버 미디어/백업 경로, 세션 쿠키, OAuth 운영 env 예시 추가
- `src/model/security.py`: 인증 응답 보안 헤더, OAuth host/TTL 설정 helper 추가
- `src/model/oauth.py`: OAuth env 로드 범위 축소, redirect host 검증, state TTL/상수 시간 비교, 로그 마스킹 보강
- `src/model/struct/user.py`: 계정 삭제 시 소셜 로그인 연결과 비밀번호 재설정 토큰 삭제 추가
- `src/model/struct/agreement.py`: 개인정보처리방침 v1.2로 갱신, 개인 서버 저장/백업/탈퇴 삭제 범위 반영
- `src/model/runningmate.py`: 러닝 미디어 파일 기본 경로를 `/srv/runningmate/media` 기준으로 변경
- `src/route/api.parse-image/controller.py`: 러닝 캡처 이미지 저장 기본 경로 변경
- `src/route/api.run-images/controller.py`, `src/route/api.run-media/controller.py`: 파일 제공 기본 경로 변경
- `src/route/api.auth.*`: 인증/세션/OAuth 관련 API에 no-store 보안 헤더 적용
- `src/app/page.mypage/view.pug`: 계정 삭제 안내 문구를 실제 삭제/익명화 범위와 맞춤
- `scripts/backup-runningmate-private-server.sh`: 개인 서버 데이터/미디어/선택 DB 백업 스크립트 추가
- `docs/private-server-p0-ops-2026-06-09.md`: 세 P0 작업 운영 기준 문서 추가
- `docs/private-server-storage-plan-2026-06-09.md`: 미디어 기본 경로 문서 갱신
- `devlog.md`, `devlog/2026-06-09/037-private-server-media-auth-privacy-p0.md`: 작업 기록 추가

## 확인 결과

- 변경된 Python 파일 `py_compile` 성공
- `bash -n scripts/backup-runningmate-private-server.sh` 성공
- `wiz_project_build(projectName="main", clean=false)` 성공
- WIZ 런타임 재시작 성공
- `http://127.0.0.1:3000/access` 200 확인
- `http://127.0.0.1:3000/api/auth/me` 200 확인
- `/api/auth/me` 응답에서 `Cache-Control: no-store`, `Pragma: no-cache`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: same-origin` 확인
- 변경 범위에서 OpenAI, Google, SendGrid 형식의 실제 키 패턴 미검출

## 남은 리스크

- 실제 이미지/영상 업로드와 백업 복구는 운영 디렉토리 권한 및 실제 사용자 세션으로 추가 검증이 필요하다.
- HTTPS 운영 환경에서 브라우저 쿠키의 `Secure`, `HttpOnly`, `SameSite=Lax` 실제 발급 확인이 필요하다.
- 회원탈퇴 삭제는 테스트 계정으로 DB row, JSON 미러, 파일 삭제 결과를 배포 전 한 번 더 대조해야 한다.
