# Git 원격 저장소 개인 레포 URL 변경

## 사용자 요청

- 리뷰 ID: `eaftzjpafzoupkplisxwpehouzuquirq`
- 제목: 개인서버를 리뷰옵스에 등록
- 원문 요청: "내 개인 레포로 변경하고 싶은데 https://github.com/zoeznm/runningmate.git 이거야 https"

## 작업 요약

WIZ 프로젝트 `main`의 git `origin` 원격 URL을 기존 `https://github.com/season-framework/wiz-sample-project`에서 사용자가 지정한 개인 레포 `https://github.com/zoeznm/runningmate.git`로 변경했다.

## 변경 파일

- `.git/config`
  - `remote.origin.url`을 `https://github.com/zoeznm/runningmate.git`로 변경했다.
- `devlog.md`
  - 2026-06-12 ID 002 작업 요약 행을 추가했다.
- `devlog/2026-06-12/002-git-origin-private-repo.md`
  - 작업 상세 devlog를 추가했다.

## 확인한 내용

- WIZ 워크스페이스 현재 프로젝트가 `main`임을 확인했다.
- 기존 remote는 `origin https://github.com/season-framework/wiz-sample-project`였다.
- 변경 후 remote는 fetch/push 모두 `origin https://github.com/zoeznm/runningmate.git`로 설정됐다.
- 현재 브랜치는 `main`이고 upstream 설정은 `origin` + `refs/heads/main`이다.
- 새 remote에 대한 `git ls-remote --heads origin main`은 현재 환경에서 GitHub 사용자 인증을 요구해 실패했다.

## 검증 결과

- `git config --get remote.origin.url`로 새 URL 반영을 확인했다.
- `git remote -v`로 fetch/push URL이 모두 새 개인 레포를 가리키는 것을 확인했다.
- GitHub 인증 정보가 없어 fetch/push 권한은 확인하지 못했다.
