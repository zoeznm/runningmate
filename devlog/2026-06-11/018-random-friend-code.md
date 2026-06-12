# 친구코드 랜덤 저장 방식 전환 및 공유 버튼 문구 정리

## 사용자 원본 요청

복사랑 공유랑 뭔 차이야? 그리고 내 코드가 RM-DUDGHK933 이면 안될 거 같은데  
내 아이디잖아  
그렇게 만들지 말고 사용자마다 랜덤한 코드로 해줘야지

## 처리 내용

- `복사` 버튼 문구를 `코드 복사`, `공유` 버튼 문구를 `공유하기`로 바꿔 기능 차이를 조금 더 분명하게 했다.
- 사용자 테이블에 `friend_code` 컬럼을 추가하고, 기존 테이블에는 자동 보강되도록 마이그레이션 로직을 추가했다.
- 친구코드는 사용자 ID/아이디/이메일에서 만들지 않고, `RM-` 접두어와 랜덤 문자열로 생성해 DB에 저장하도록 했다.
- 친구코드 입력은 저장된 랜덤 코드로만 사용자 매칭되게 바꿔 username/email을 코드처럼 취급하지 않도록 했다.
- PWA 캐시 버전을 `runningmate-pwa-v32`로 갱신했다.

## 변경 파일

- `src/model/db/user.py`
- `src/model/struct.py`
- `src/model/struct/user.py`
- `src/route/api.friends.code/controller.py`
- `src/app/page.dashboard/view.pug`
- `config/pwa/sw.js`
- `devlog.md`
- `devlog/2026-06-11/018-random-friend-code.md`

## 검증 결과

- `python -m py_compile` 통과
- `git diff --check` 통과
- `wiz_project_build(clean=false)` 성공
- `/api/friends/code` 비로그인 요청이 JSON 인증 응답을 반환하는 것 확인
- 실제 DB의 `user.friend_code` 컬럼 및 `user_friend_code_unique` 인덱스 존재 확인

## 남은 리스크

- 기존 사용자에게는 친구코드 조회 시점에 랜덤 코드가 최초 생성되므로, 로그인된 실제 계정으로 한 번 조회 확인이 필요하다.
