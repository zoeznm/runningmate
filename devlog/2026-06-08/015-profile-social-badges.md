# 015. 프로필 팔로잉/팔로워 목록 및 프로필별 뱃지 노출

## 사용자 원본 요청

프로필 화면에서 팔로잉 누르면 팔로잉 목록 보여주고 팔로워 버튼 누르면 팔로워 목록 보여주고 그리고 각 프로필마다 무슨 뱃지 모았는지도 보여주면 좋겠어

## 변경 파일

- `src/app/page.dashboard/view.ts`
- `src/app/page.dashboard/view.pug`
- `src/app/page.dashboard/view.scss`
- `src/model/runningmate.py`
- `src/route/api.follows.following/controller.py`
- `src/route/api.follows.followers/controller.py`
- `src/route/api.follows.detail/controller.py`
- `src/route/api.users.search/controller.py`

## 변경 내용

- 내 프로필의 팔로잉/팔로워 숫자를 누르면 프로필 화면 안에서 해당 목록이 열리도록 추가했다.
- 목록의 각 프로필에 관계 상태, 팔로우 버튼, 획득 뱃지 요약과 뱃지 칩을 표시했다.
- 친구 프로필 상세 카드에도 획득 뱃지 섹션을 추가했다.
- 팔로우/검색 API 응답에 공개 프로필의 획득 뱃지 요약을 포함하도록 보강했다.

## 확인 결과

- `wiz_project_build(projectName="main", clean=false)` 성공.
- `python -m py_compile project/main/src/model/runningmate.py project/main/src/route/api.follows.following/controller.py project/main/src/route/api.follows.followers/controller.py project/main/src/route/api.follows.detail/controller.py project/main/src/route/api.users.search/controller.py` 성공.
