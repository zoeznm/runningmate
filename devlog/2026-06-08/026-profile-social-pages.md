# 026. 프로필 팔로우 목록/타 사용자 프로필 전체화면 전환

## 사용자 원본 요청

팔로잉을 누르면 팔로잉 목록이 저렇게 나오고 있는데 그냥 다른 페이지처럼 보여줘 저런식으로 보여주면 여러명일 때 보기가 힘들잖아 인스타그램처럼 그렇게 다른 페이지로 넘어가서 나오게 해주면 좋겠어 팔로잉 뿐만 아니라 팔로워도 똑같이 그렇게 보여줘 그리고 목록에 저렇게 누군가 다른 사용자가 있으면 그 다른 사용자 누르면 그 사용자의 프로필도 같이 보여줘 그 사람의 프로필도 저렇게 피드, 팔로잉, 팔로워 목록 나오고 언팔로우 버튼도 같이 보여주고 이러면 좋겠어 다른 사용자의 프로필도 인스타그램처럼 다른 페이지로 나오게 해주면 좋겠어

## 변경 파일

- `src/app/page.dashboard/view.ts`
- `src/app/page.dashboard/view.pug`
- `src/app/page.dashboard/view.scss`
- `src/route/api.follows.detail/controller.py`

## 변경 내용

- 내 프로필의 팔로잉/팔로워 목록을 인라인 카드가 아닌 전체화면 목록 페이지로 분리했다.
- 목록의 사용자 항목을 누르면 해당 사용자의 전체화면 프로필 페이지로 이동하도록 추가했다.
- 다른 사용자 프로필에 피드, 팔로잉/팔로워 카운터, 뱃지, 팔로우/언팔로우 버튼을 표시했다.
- 다른 사용자 프로필 안에서도 팔로잉/팔로워 목록을 전체화면 목록으로 볼 수 있게 했다.
- `/api/follows/<user_id>` GET 응답에 프로필, 팔로잉/팔로워 목록, 사진/영상 피드를 포함하도록 확장했다.

## 확인 결과

- `wiz_project_build(projectName="main", clean=false)` 성공.
- `python -m py_compile project/main/src/route/api.follows.detail/controller.py` 성공.
