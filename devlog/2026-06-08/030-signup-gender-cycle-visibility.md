# 030. 회원가입 성별 선택 및 남성 사용자 생리주기 기능 숨김

## 사용자 원본 요청

```text
생리주기 같은 경우에는 남자 사용자한테는 필요가 없잖아 그래서 이거를 어떻게 하면 좋을까? 회원가입을 할 때 남자/ 여자 선택할 수 있게 하면 어때? 그래서 여자면 생리주기 기능이 개인정보 섹션에 있는거고 남자라면 아예 저 기능자체가 없는거지
```

## 변경 파일

- `src/app/page.access/view.pug`
- `src/app/page.access/view.ts`
- `src/app/page.access/api.py`
- `src/app/page.dashboard/view.pug`
- `src/app/page.dashboard/view.ts`
- `src/model/db/user.py`
- `src/model/struct.py`
- `src/model/struct/user.py`
- `src/model/auth.py`
- `src/model/struct/agreement.py`
- `src/route/api.auth.register/controller.py`
- `src/route/api.profile/controller.py`
- `bundle/www/main.js`
- `bundle/www/main.js.map`
- `devlog.md`
- `devlog/2026-06-08/030-signup-gender-cycle-visibility.md`

## 변경 내용

- 회원가입 1단계에 여자/남자 성별 선택을 추가하고 미선택 시 다음 단계와 가입을 막았다.
- `user.gender` 컬럼과 기존 DB 보강 로직을 추가했다.
- 회원가입 API, 프로필 API, auth 공개 사용자 payload에 `gender`를 포함했다.
- 남성 사용자(`gender === "male"`)에게 달력 주기 연동, 주기 기록, 분석 주기 패턴, 개인정보 생리주기 설정을 숨기고 로컬 주기 설정도 꺼지도록 처리했다.
- 개인정보 수집 기본 문구에 성별 수집 항목을 추가했다.

## 확인 결과

- `wiz_project_build(projectName="main", clean=false)` 성공.
- `node build/wizbuild.js src/app/page.access/view && node build/wizbuild.js src/app/page.dashboard/view` 성공.
- `python -m py_compile`로 변경 Python 파일 구문 확인 성공.
- `node --check bundle/www/main.js` 성공.
- 로컬 `http://127.0.0.1:3000/main.js`에서 성별 선택 UI, `selectSignupGender`, `shouldShowCycleFeature`, 생리주기 설정 조건 반영 확인.
- 생성된 임시 `view.html` 파일이 남지 않은 것을 확인.
