# 051. 로컬 업로드 파일 서명 URL 및 권한 확인 적용

- 날짜: 2026-06-09
- 요청: "로컬 업로드 파일 접근 URL을 인증/권한 기반 또는 짧은 만료 서명 URL로 전환"
- 리뷰 ID: `eplsrldlzbjzpstdfzvzaprwbkaozrlo`

## 변경 파일

- `src/model/security.py`
- `src/model/runningmate.py`
- `src/route/api.run-images/controller.py`
- `src/route/api.run-media/controller.py`
- `src/route/api.runs/controller.py`
- `src/route/api.runs.detail/controller.py`
- `src/route/api.runs.media/controller.py`
- `src/route/api.feed/controller.py`
- `src/route/api.follows.detail/controller.py`
- `devlog.md`
- `devlog/2026-06-09/051-local-upload-signed-access.md`

## 변경 내용

- 로컬 업로드 URL에 `exp`, `sig` 쿼리를 붙이는 HMAC 서명 URL을 추가했다.
- 기본 만료 시간은 `RUNNINGMATE_UPLOAD_URL_TTL_SECONDS` 환경변수로 조정 가능하며 기본값은 600초다.
- 파일 서빙 라우트가 서명 검증을 먼저 수행하고, 서명이 없거나 만료된 경우 로그인 사용자 권한을 확인하도록 했다.
- 권한이 없으면 파일 존재 여부를 노출하지 않도록 404로 응답한다.
- `/api/run-images`, `/api/run-media` 응답 캐시를 `public`에서 `private`로 변경하고 `nosniff` 헤더를 추가했다.
- 러닝 목록/상세/미디어/피드/프로필 미디어 API 응답에는 서명 URL을 내려주되, DB/JSON 저장값은 기존 원본 로컬 경로를 유지하도록 했다.
- 파일 삭제/계정 삭제 정리 로직이 서명 URL을 받아도 원본 경로로 정규화할 수 있게 보강했다.

## 확인 결과

- `python3 -m py_compile`로 변경 Python 파일 문법 검사를 통과했다.
- `git diff --check` 성공.
- `wiz_project_build(clean=false)` 성공.
- `Security.sign_upload_url()`과 `Security.verify_upload_url_signature()`의 서명 생성/검증 단위 확인 성공.
- Python 3.12 pyc 검증 산출물은 정리했다.
