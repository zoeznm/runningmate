# README를 러닝메이트 프로젝트 기준으로 재구성

## 사용자 요청

- 리뷰 ID: `eaftzjpafzoupkplisxwpehouzuquirq`
- 제목: 개인서버를 리뷰옵스에 등록
- 원문 요청: "근데 지금 리드미 보면 WIZ Sample Project 라고 뜨는데 리드미를 다시 이 프로젝트를 기반으로 재구성해줘야될 거 같애"

## 작업 요약

샘플 프로젝트 중심이던 README를 러닝메이트 실제 서비스 기준으로 재작성했다. 기능, 기술 스택, 프로젝트 구조, 실행/빌드, 환경변수, API, 개인 서버 배포, 배포 산출물 관리, iOS shell, 운영 문서, Git 작업 원칙을 정리했다.

## 변경 파일

- `README.md`
  - `WIZ Sample Project` 설명과 샘플 계정/게시판 중심 설명을 제거했다.
  - 러닝메이트 기능과 운영 기준을 프로젝트 문서 허브 형태로 재구성했다.
- `devlog.md`
  - 2026-06-12 ID 006 작업 요약 행을 추가했다.
- `devlog/2026-06-12/006-readme-runningmate-rewrite.md`
  - 작업 상세 devlog를 추가했다.

## 확인한 내용

- WIZ 프로젝트 `main`의 app/route/package 구성을 확인했다.
- `.env.example`, `package.json`, `src/angular/package.json`, 배포 산출물 관리 문서를 확인해 README에 반영했다.
- README에서 샘플 프로젝트 제목과 샘플 계정 중심 설명을 제거했다.

## 검증 결과

- 문서 변경만 수행했으므로 WIZ/Angular 빌드는 실행하지 않았다.
- `git diff --cached --check` 통과.
- 변경 커밋 생성 후 `git push origin main` 성공.
