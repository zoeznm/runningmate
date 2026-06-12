# 설정 화면 약관/개인정보/계정삭제 진입 및 공개 페이지 앱형 톤 보정

- 날짜: 2026-06-12
- 작업 ID: 021
- 리뷰 ID: eloeddldgkttnnzmkewgysjnazydbtwj

## 사용자 원문

"/privacy, /terms, /account/delete 이거를 설정 페이지에 녹여줘 설정페이지에서 들어갈 수 있게 대신에 들어가는게 앱이랑 디자인이 자연스러워야돼. 갑자기 웹 디자인으로 변경되면 안되고 자연스럽게 나와야돼. 버튼 같은거 누르면 해당 페이지로 넘어가도록"

## 변경 요약

대시보드 설정 화면에 개인정보처리방침, 이용약관, 계정 삭제 페이지로 이동하는 설정 행을 추가했다. 공개 문서/계정 삭제 페이지에는 앱식 뒤로가기와 좁은 앱 화면 톤을 적용해 설정에서 이동해도 화면 전환이 자연스럽게 보이도록 보정했다.

## 변경 파일

- `src/app/page.dashboard/view.pug`
  - 설정 > 정보에 개인정보처리방침과 이용약관 진입 행을 추가했다.
  - 설정 > 데이터의 계정 삭제 행이 `/account/delete`로 이동하도록 바꿨다.
- `src/app/page.dashboard/view.ts`
  - 설정 행에서 공개 페이지로 이동하는 `openLegalPage()`를 추가했다.
  - 기존 전체 데이터 삭제 진입 함수가 계정 삭제 페이지 이동을 사용하도록 정리했다.
- `src/app/page.privacy/view.ts`
  - 설정 화면으로 자연스럽게 돌아갈 수 있는 뒤로가기 동작을 추가했다.
- `src/app/page.privacy/view.pug`
  - 앱형 뒤로가기 버튼을 헤더에 추가했다.
- `src/app/page.privacy/view.scss`
  - 공개 문서 화면을 앱 내부 화면 톤과 폭에 맞게 보정했다.
- `src/app/page.terms/view.ts`
  - 설정 화면으로 자연스럽게 돌아갈 수 있는 뒤로가기 동작을 추가했다.
- `src/app/page.terms/view.pug`
  - 앱형 뒤로가기 버튼을 헤더에 추가했다.
- `src/app/page.terms/view.scss`
  - 공개 문서 화면을 앱 내부 화면 톤과 폭에 맞게 보정했다.
- `src/app/page.account.delete/view.ts`
  - 설정 화면으로 자연스럽게 돌아갈 수 있는 뒤로가기 동작을 추가했다.
- `src/app/page.account.delete/view.pug`
  - 앱형 뒤로가기 버튼을 헤더에 추가했다.
- `src/app/page.account.delete/view.scss`
  - 계정 삭제 화면을 앱 내부 화면 톤과 폭에 맞게 보정했다.
- `devlog.md`
  - 작업 요약 행을 추가했다.
- `devlog/2026-06-12/021-settings-legal-entry-app-tone.md`
  - 작업 상세 로그를 추가했다.

## 확인 결과

- 설정 화면의 기존 `settings-list-row` 패턴을 재사용해 새 진입 행을 추가했다.
- 공개 페이지는 기존 URL을 유지하면서 뒤로가기 버튼과 앱형 톤을 적용했다.

## 검증

- `wiz_project_build(clean=false)` 성공.
