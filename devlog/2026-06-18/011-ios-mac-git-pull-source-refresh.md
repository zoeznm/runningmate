# Mac 프로젝트 Git 최신화 명령 및 한계 문서화

- 날짜: 2026-06-18
- 작업 ID: 011
- 리뷰 ID: cffcsljsecovmosrwdemlskhtgambebz

## 사용자 원문

"먼저 Mac의 /Users/kimbomi/Desktop/app/project/main 프로젝트를 최신 코드로 갱신해야 합니다. 이걸 어떻게 하더라? 명령어 뭐야?"

## 확인

- 현재 저장소 원격은 `https://github.com/zoeznm/runningmate.git`이다.
- 현재 브랜치는 `main`이다.
- Git으로 Mac 프로젝트를 최신화하려면 `git fetch origin`, `git pull --ff-only origin main`을 사용한다.

## 주의

- `git pull`은 원격 GitHub에 올라간 변경만 가져온다.
- 현재 ReviewOps 작업 변경이 아직 원격에 push되지 않았다면, Mac에서 `git pull`을 해도 `descriptor.serverURL = nil`이 생기지 않을 수 있다.

## 반영

- `docs/ios-mac-source-refresh-2026-06-18.md`에 Git 최신화 명령과 `Already up to date`인데도 grep 결과가 없을 때의 의미를 추가했다.
