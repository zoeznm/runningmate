# 친구 이름/랭킹 배지, 친구코드 추가, 프로필 목록 위치, 자동 로그인 확인 화면 개선

## 사용자 원본 요청

1. 지금 다른 사용자 이름은 김**이런식으로 보이게 해뒀는데 친구 이름은 다 보이게 해주고 전체 랭킹보는 곳에서 친구가 있으면  런메이트 라는 이름을 붙여줘  
2. 내 프로필 들어가서 팔로잉 팔로워 클릭하면 그 목록 보여주는 페이지로 넘어가는데 지금 그 페이지가 너무 상단에 있어서 뒤로가기 버튼을 누를 수가 없어 이 부분 수정해줘 다른 페이지들이랑시작값 위치 똑같이 해줘  
3. 그리고 생각해보니까 친구를 추가할 수 있는 버튼이 없던데 그 친구코드 같은거 자기 자신껄로 고유코드 나오게 해서 그거 공유하면 친구가 될 수 있게 하면 좋을 거 같은데 커뮤니티 탭 메뉴에 그 기능을 만들고 싶은데 어디에 추가를 해야될지 모르겠어 플로팅 AI 처럼 플로팅 친구추가 버튼 같은 걸 둬야하나? 고민이네  
4. 이게 가끔씩 들어올 때 로그인이 풀려서 다시 로그인하라고 하다가 자동 로그인돼서 들어오는 경우가 있거든? 근데 그런게 아예 없으면 좋겠어 자동 로그인 선택하고 로그인한 사용자는 그런 로그인이 살짝 풀리는 일도 없으면 좋겠어  

일단 이정도로 수정해줘

## 처리 내용

- 전체 랭킹 응답에 팔로잉/팔로워/상호 관계 필드를 추가하고, 팔로잉 사용자는 이름 마스킹을 적용하지 않도록 했다.
- 전체 랭킹 화면에서 친구 관계인 항목 옆에 `런메이트` 배지가 보이도록 했다.
- 커뮤니티 > 친구 탭 상단에 내 친구코드 표시, 복사/공유, 코드 입력 추가 카드를 추가했다.
- `/api/friends/code` route를 추가해 내 코드 조회와 코드 기반 팔로우를 처리하도록 했다.
- 프로필 팔로잉/팔로워 목록 overlay에 일반 대시보드 화면과 같은 상단 여백 및 모바일 safe-area 보정을 적용했다.
- access 화면에서 자동 로그인 세션 확인이 끝나기 전에는 로그인 폼을 보여주지 않고 `자동 로그인 확인 중` 상태를 먼저 보여주도록 했다.
- PWA 캐시 버전을 `runningmate-pwa-v30`으로 갱신했다.

## 변경 파일

- `src/app/page.dashboard/view.ts`
- `src/app/page.dashboard/view.pug`
- `src/app/page.dashboard/view.scss`
- `src/app/page.access/view.ts`
- `src/app/page.access/view.pug`
- `src/app/page.access/view.scss`
- `src/model/runningmate.py`
- `src/route/api.ranking.weekly/controller.py`
- `src/route/api.friends.code/app.json`
- `src/route/api.friends.code/controller.py`
- `config/pwa/sw.js`
- `devlog.md`
- `devlog/2026-06-11/016-friend-code-ranking-profile-auth-polish.md`

## 검증 결과

- `wiz_project_build(clean=false)` 성공
- `python -m py_compile src/route/api.friends.code/controller.py src/route/api.ranking.weekly/controller.py src/model/runningmate.py` 통과
- `git diff --check` 통과
- 번들에 `runningmate-pwa-v30`, `/api/friends/code`, `session-check-card` 반영 확인
- WIZ worker 재시작 후 `/api/friends/code`가 JSON 인증 응답을 반환하는 것 확인
- `/dashboard`, `/access` 응답 200 확인

## 남은 리스크

- 친구코드는 사용자 ID 기반 단축 코드라 기존 계정에는 즉시 생성되지만, 실사용 친구 추가는 로그인된 계정으로 직접 확인이 필요하다.
- PWA 서비스워커 캐시 교체 전에는 이전 화면이 잠시 남을 수 있다.
