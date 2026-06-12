# 로그인 성공 응답 날짜 직렬화 보강

## 사용자 요청

- 리뷰 ID: `xyacypgnxkenansvzctubfxprpwtjhgw`
- 제목: 로그인 자동 무한 로딩
- 요청: 로그인 시 계속 `응답을 읽지 못했어. 다시 시도해줘` 오류가 뜨며 로그인이 안 된다고 다시 요청했다.

## 원인

- 실제 리뷰 도메인에서 잘못된 계정으로 `/api/auth/login`을 호출했을 때 실패 응답은 JSON으로 반환되는 것을 확인했다.
- 따라서 계속 발생하는 parse 오류는 로그인 성공 응답 생성 중 서버가 JSON 직렬화에 실패하는 경로가 더 유력했다.
- 코드상 `auth.public_user()`가 DB `DateTimeField`인 `created_at`/`created` 값을 그대로 반환할 수 있어, 성공 로그인 응답의 `tokens.user.created_at` 직렬화가 깨질 수 있었다.

## 변경 파일

- `src/model/auth.py`
  - 공개 사용자 응답의 `created_at`을 `_public_datetime()`으로 문자열 정규화하도록 수정했다.
- `src/route/api.auth.login/controller.py`
  - 로그인 성공 응답도 `_send_response(200, ...)` 경로로 통일했다.
  - JSON 생성 시 `default=auth._json_default`를 사용해 남은 날짜형 값도 안전하게 문자열화하도록 했다.

## 확인한 내용

- `wiz_project_build(projectName="main", clean=false)` 성공
  - `EsBuild complete`
  - `Project 'main' build completed`
- 리뷰 도메인 확인
  - `POST https://matomabo.run.seasonai.net/api/auth/login`에 잘못된 계정으로 호출 시 `content-type: application/json`
  - 응답 body: `{"code": 401, "data": {"success": false, "message": "아이디 또는 비밀번호가 올바르지 않습니다."}}`
- 코드 확인
  - `auth.public_user()`의 `created_at` 문자열화 확인
  - 로그인 성공 응답 `_send_response(200, ...)` 적용 확인

## 남은 확인/배포 메모

- 실제 계정의 성공 로그인은 비밀번호가 없어 직접 검증하지 못했다.
- 배포/재시작 후 실제 모바일에서 성공 로그인 시 parse 오류가 사라지는지 확인해야 한다.
