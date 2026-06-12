# 027. 설정 화면 순서 및 월 목표 설정 이동 수정 catch-up

## 사용자 원본 요청

```text
작업 진행해줘

월 목표 설정누르면 바로 목표로 안 넘어가 수정해줘
```

## 변경 파일

- `src/app/page.dashboard/view.pug`
- `src/app/page.dashboard/view.ts`
- `bundle/www/main.js`
- `bundle/www/index.html`

## 변경 내용

- 설정 화면 섹션 순서를 프로필, 목표 & 알림, 연동, 표시, 개인정보, 데이터, 정보, 로그아웃 순서로 정리했다.
- 로그아웃 섹션과 로그아웃 처리 함수를 추가해 `/access`로 이동하도록 연결했다.
- 월 목표 설정 행 클릭 시 이벤트 전파를 막고 곧바로 목표 화면으로 이동하도록 `openGoalSettings()`를 보강했다.
- 당시 운영 번들에 동일 변경을 직접 반영했다.

## 확인 결과

- `node --check bundle/www/main.js` 성공.
- `node build/wizbuild.js src/app/page.dashboard/view` 성공.
- 로컬 `http://127.0.0.1:3000/main.js`에서 월 목표 설정 클릭 핸들러와 설정 섹션 순서 반영을 확인했다.
