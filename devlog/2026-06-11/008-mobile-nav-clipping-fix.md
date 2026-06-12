# 모바일 하단 메뉴바 잘림 보정

## 사용자 원본 요청

메뉴바를 하단으로 좀 내리니까 저렇게 하단에 좀 잘리는 현상이 발생해 수정해줘 메뉴바를 z-index를 써서 항상 위에 있게 하면 고쳐지려나?

## 처리 내용

- 모바일 하단 메뉴바가 음수 `bottom` offset으로 내려갈 때 라벨 하단이 viewport 밖으로 잘리지 않도록 offset 값을 하단 padding에 반영했다.
- 메뉴바 `z-index`를 높여 화면 콘텐츠보다 항상 위에 렌더링되도록 했다.
- 메뉴바에 `translateZ(0)`을 적용해 모바일 브라우저 합성 레이어에서 안정적으로 표시되도록 했다.
- PWA 캐시 버전을 `runningmate-pwa-v24`로 갱신했다.

## 변경 파일

- `src/app/page.dashboard/view.scss`
- `config/pwa/sw.js`
- `devlog.md`
- `devlog/2026-06-11/008-mobile-nav-clipping-fix.md`

## 검증 결과

- `git diff --check` 통과
- `wiz_project_build(clean=false)` 성공

## 남은 리스크

- 실제 iOS Safari/PWA 하단 안전 영역은 기기별로 달라, 첨부 스크린샷과 같은 실기기에서 최종 육안 확인이 필요하다.
