# 기능별 로컬 커밋 생성 및 개인 레포 push 인증 실패 기록

## 사용자 요청

- 리뷰 ID: `eaftzjpafzoupkplisxwpehouzuquirq`
- 제목: 개인서버를 리뷰옵스에 등록
- 원문 요청: "기능별로 커밋하고 푸시하고 반복해줘"

## 작업 요약

누적 변경을 기능 단위로 나눠 로컬 커밋을 생성했다. 각 기능 커밋 후 `git push origin main`을 시도했지만, 새 개인 GitHub remote가 HTTPS 사용자 인증을 요구해 push는 실패했다.

## 생성한 커밋

| 커밋 | 메시지 | 성격 |
| --- | --- | --- |
| `8748d84` | `chore: add operations docs and scripts` | 운영 문서, devlog 상세 파일, 배포/헬스체크/보안 스크립트 |
| `bc5f966` | `feat: add runningmate API and auth backend` | 인증, API 라우트, 데이터 모델, 세션/요청 유틸 |
| `8146e6f` | `feat: build runningmate web app experience` | Angular/WIZ 화면, 대시보드, 접근 화면, 공통 UI 컴포넌트 |
| `b084cfd` | `feat: add iOS shell and brand assets` | Capacitor iOS wrapper와 브랜드 아이콘 |

## 변경 파일

- `devlog.md`
  - 2026-06-12 ID 003 작업 요약 행을 추가했다.
- `devlog/2026-06-12/003-functional-commits-push-attempt.md`
  - 기능별 커밋과 push 실패 결과를 기록했다.

## 확인한 내용

- `origin`은 `https://github.com/zoeznm/runningmate.git`로 설정되어 있다.
- 기능별 커밋 4개를 로컬 `main` 브랜치에 생성했다.
- 배포 압축본(`runningmate-deploy*.tar.gz`, split part, checksum, reassemble 안내)은 커밋하지 않고 untracked로 남겼다.
- 실제 secret 패턴 검색에서는 placeholder 문서 예시만 확인했고, 커밋 대상에서 실제 키 패턴은 발견하지 못했다.
- iOS `public` 빌드 산출물은 `ios/.gitignore`에 의해 커밋 대상에서 제외됐다.

## 검증 결과

- staged source 커밋들은 `git diff --cached --check`를 통과했다.
- 과거 devlog 원문에는 trailing whitespace가 있어 첫 문서 커밋의 `git diff --check`는 실패했지만, 사용자 원문 보존 성격이라 수정하지 않았다.
- `git push origin main`은 매번 `fatal: could not read Username for 'https://github.com': No such device or address`로 실패했다.
