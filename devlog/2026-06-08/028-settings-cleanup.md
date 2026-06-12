# 028. 설정 화면 알림/연동/생체인증/상단 테마 토글 제거

## 사용자 원본 요청

```text
설정에서 
1. 월 목표 설정 아래에 전체 알림 러닝 리마인더, 목표 진행 주간 리포트, 휴식 후 복귀 이런거 없애줘 
2. 휴식 추천도 없애줘 
3. 연동 부분 없애줘 (애플워치, Apple Music) 
4. 앱 잠금(생체인증) 도 없애줘 
5. 표시에 테마 다크, 라이트, 시스템 이렇게 있으니까 앱 상단에 별, 해 아이콘 싹 없애줘 

작업 진행해줘
```

## 변경 파일

- `src/app/page.dashboard/view.pug`
- `src/app/page.dashboard/view.scss`
- `config/pwa/sw.js`
- `src/angular/angular.build.options.json`
- `src/angular/angular.json`
- `src/angular/index.pug`
- `src/assets/notification-settings.css`
- `src/assets/notification-settings.js`
- `src/angular/static/notification-settings.css`
- `src/angular/static/notification-settings.js`
- `src/route/notification-settings-css/`
- `src/route/notification-settings-js/`
- `bundle/www/main.js`
- `bundle/www/index.html`
- `bundle/www/notification-settings.css`
- `bundle/www/notification-settings.js`
- `devlog.md`
- `devlog/2026-06-08/027-settings-order-goal-navigation-catchup.md`
- `devlog/2026-06-08/028-settings-cleanup.md`

## 변경 내용

- 설정의 목표 & 알림 섹션에서 월 목표 설정 아래의 알림/리마인더 상세 UI와 휴식 추천 행을 제거했다.
- 설정의 연동 섹션과 애플워치(HealthKit), Apple Music 연결 행을 제거했다.
- 개인정보 섹션의 앱 잠금(생체인증) 행을 제거했다.
- 앱 상단의 별/해 테마 전환 버튼과 관련 CSS를 제거했다.
- 더 이상 쓰지 않는 `notification-settings` 정적 파일, 라우트, 번들 파일 참조를 제거했다.
- 서비스워커 사전 캐시 목록과 Angular asset glob에서 `notification-settings` 항목을 제거하고 캐시 버전을 갱신했다.

## 확인 결과

- `rg`로 설정 템플릿, SCSS, `index.pug`, 번들에서 제거 대상 문자열이 남지 않은 것을 확인했다.
- `node --check bundle/www/main.js` 성공.
- `node build/wizbuild.js src/app/page.dashboard/view` 성공 후 생성된 임시 `view.html` 제거 확인.
- 로컬 `http://127.0.0.1:3000/index.html`에서 `notification-settings` 참조가 없음을 확인했다.
- 로컬 `http://127.0.0.1:3000/main.js`의 대시보드 템플릿에서 상단 테마 버튼, 알림/휴식 추천, 연동, 생체인증 행이 모두 absent임을 확인했다.
- `src`, `config`, 현재 번들에서 런타임 `notification-settings` 참조가 제거된 것을 확인했다.
