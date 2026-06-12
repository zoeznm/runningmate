# 배포 압축 산출물 Git 제외 및 관리 기준 문서화

## 사용자 요청

- 리뷰 ID: `eaftzjpafzoupkplisxwpehouzuquirq`
- 제목: 개인서버를 리뷰옵스에 등록
- 원문 요청: "`runningmate-deploy*.tar.gz` 등 배포 압축 산출물 7개는 의도적으로 untracked 상태입니다. 이런것들은 어떻게 관리해?"

## 작업 요약

배포 압축본, 분할본, 체크섬, 재조립 안내 파일을 Git 커밋 대상에서 제외하도록 `.gitignore`에 규칙을 추가했다. 산출물은 GitHub Release 또는 외부 artifact 저장소에 올리고, Git에는 소스와 배포 스크립트/문서만 남기는 관리 기준을 문서화했다.

## 변경 파일

- `.gitignore`
  - `runningmate-deploy*.tar.gz`, split part, checksum, reassemble 안내 파일 ignore 규칙 추가.
- `docs/deployment-artifact-management-2026-06-12.md`
  - 배포 압축 산출물 관리 기준, 권장 release 흐름, 로컬 보관 정책을 문서화.
- `devlog.md`
  - 2026-06-12 ID 005 작업 요약 행 추가.
- `devlog/2026-06-12/005-deployment-artifact-management.md`
  - 작업 상세 devlog 추가.

## 확인한 내용

- 현재 root에 배포 압축본/분할본/체크섬/재조립 안내 파일 7개가 있었다.
- 해당 파일들은 소스가 아니라 배포 산출물이므로 Git 커밋 대신 release asset으로 관리하는 것이 적절하다.
- ignore 규칙 추가 후 해당 산출물들이 `git status`에 나타나지 않는 것을 확인했다.

## 검증 결과

- `git diff --cached --check` 통과.
- 변경 커밋 생성 후 `git push origin main` 성공.
