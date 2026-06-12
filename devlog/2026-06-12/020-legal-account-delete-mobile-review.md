# 앱스토어 심사용 공개 약관/개인정보/계정삭제 페이지 및 모바일 업로드 안내 보강

- 날짜: 2026-06-12
- 작업 ID: 020
- 리뷰 ID: eloeddldgkttnnzmkewgysjnazydbtwj

## 사용자 원문

"작업 진행해줘"

## 변경 요약

앱스토어 심사에 필요한 공개 개인정보처리방침, 이용약관, 계정 삭제 페이지를 추가하고, 개인정보 문서에 Runningmate가 처리하는 데이터 범주를 명시했다. 모바일 업로드와 권한 안내 문구도 보강했다.

## 변경 파일

- `src/app/page.privacy/app.json`
  - `/privacy` 공개 페이지를 추가했다.
- `src/app/page.privacy/view.ts`
  - `/api/agreements`에서 현재 개인정보처리방침을 불러오도록 구현했다.
- `src/app/page.privacy/view.pug`
  - 공개 개인정보처리방침 문서 화면을 추가했다.
- `src/app/page.privacy/view.scss`
  - 문서 화면의 데스크톱/모바일 스타일을 추가했다.
- `src/app/page.terms/app.json`
  - `/terms` 공개 페이지를 추가했다.
- `src/app/page.terms/view.ts`
  - `/api/agreements`에서 현재 이용약관을 불러오도록 구현했다.
- `src/app/page.terms/view.pug`
  - 공개 이용약관 문서 화면을 추가했다.
- `src/app/page.terms/view.scss`
  - 문서 화면의 데스크톱/모바일 스타일을 추가했다.
- `src/app/page.account.delete/app.json`
  - `/account/delete` 공개 페이지를 추가했다.
- `src/app/page.account.delete/view.ts`
  - 로그인 상태 확인, 삭제 확인 입력, `/api/auth/account` DELETE 호출 흐름을 추가했다.
- `src/app/page.account.delete/view.pug`
  - 계정 삭제 안내, 삭제 데이터 목록, 최종 삭제 폼을 추가했다.
- `src/app/page.account.delete/view.scss`
  - 계정 삭제 화면의 데스크톱/모바일 스타일을 추가했다.
- `src/angular/app/app.component.ts`
  - `/privacy`, `/terms`, `/account/delete`를 공개 경로로 처리해 로그인 리다이렉트와 재동의 모달을 건너뛰도록 했다.
- `src/model/struct/agreement.py`
  - 개인정보처리방침을 v1.3, 2026-06-12 시행으로 갱신하고 회원 정보, 러닝 기록, 체중 기록, 사진/영상, AI 대화 기록, 사용량 기록, 기기/로그인 정보를 명시했다.
- `src/app/page.dashboard/view.ts`
  - 기록 캡처 업로드와 추가 사진/영상 선택의 안내 문구를 구분했다.
- `src/app/page.dashboard/view.pug`
  - 모바일 사진/파일 선택 권한 안내와 위치 권한 설정 변경 안내를 추가했다.
- `src/app/page.dashboard/view.scss`
  - 모바일 업로드 권한 안내 박스 스타일을 추가했다.
- `devlog.md`
  - 작업 요약 행을 추가했다.
- `devlog/2026-06-12/020-legal-account-delete-mobile-review.md`
  - 작업 상세 로그를 추가했다.

## 확인 결과

- `wiz_source_list_apps(appType=page)`로 `/privacy`, `/terms`, `/account/delete` 페이지가 등록된 것을 확인했다.
- 기존 `/api/auth/account` 삭제 API와 마이페이지 삭제 흐름을 확인하고, 새 삭제 페이지에서 같은 API를 사용하도록 했다.
- 기존 `/api/agreements` 공개 GET과 약관/개인정보 모델을 확인하고, 공개 문서 페이지가 같은 정책 데이터를 표시하도록 했다.

## 검증

- `wiz_project_build(clean=false)` 성공.
- `python -m py_compile /opt/app/project/main/src/model/struct/agreement.py` 성공.
