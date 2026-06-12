# 커뮤니티 친구 탭 진입 누락 수정

## 사용자 원본 요청

커뮤니티 > 친구 탭 상단에 내 친구코드 표시, 복사/공유, 코드로 친구 추가 기능을 추가했습니다.  
커뮤니티에 친구 탭이라는게 없는데?

## 처리 내용

- 커뮤니티 서브 메뉴에 `친구` 항목을 추가해 기존 `friends` 화면으로 진입할 수 있도록 했다.
- 친구 탭에 들어가면 기존 친구코드 표시, 복사/공유, 코드 입력 추가 UI가 노출된다.
- 프론트 변경이 기존 PWA 캐시에 묶이지 않도록 서비스워커 캐시 버전을 `runningmate-pwa-v31`로 갱신했다.

## 변경 파일

- `src/app/page.dashboard/view.ts`
- `config/pwa/sw.js`
- `devlog.md`
- `devlog/2026-06-11/017-community-friends-tab-entry.md`

## 검증 결과

- `git diff --check` 통과
- `wiz_project_build(clean=false)` 성공
- 소스에서 커뮤니티 메뉴의 `친구` 항목 및 `runningmate-pwa-v31` 반영 확인

## 남은 리스크

- 설치형 PWA에서는 새 서비스워커가 적용되기 전까지 이전 메뉴가 잠시 보일 수 있다.
