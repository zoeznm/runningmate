# 배포 압축 산출물 관리 기준

작성일: 2026-06-12
대상: 러닝메이트 개인 서버 배포 산출물

## 원칙

`runningmate-deploy*.tar.gz` 같은 배포 압축본은 Git 커밋에 넣지 않는다. Git에는 소스, 설정 예시, 배포 스크립트, 검증 문서만 남기고, 압축 산출물은 release asset 또는 별도 artifact 저장소에서 관리한다.

## 이유

- 압축본은 소스에서 다시 만들 수 있는 산출물이다.
- Git repo 크기를 빠르게 키운다.
- 같은 파일이 이름만 바뀌어 반복 커밋되면 clone, fetch, diff가 모두 느려진다.
- 체크섬과 분할 파일도 압축본과 같은 생명주기를 가지므로 Git이 아니라 release asset에 같이 둔다.

## 현재 파일 분류

| 파일 패턴 | 관리 위치 | 비고 |
| --- | --- | --- |
| `runningmate-deploy*.tar.gz` | GitHub Release 또는 외부 artifact 저장소 | 배포 압축본 |
| `runningmate-deploy*.tar.gz.part-*` | GitHub Release 또는 외부 artifact 저장소 | 다운로드 제한 대응 분할본 |
| `runningmate-deploy*.sha256` | 압축본과 같은 release asset | 무결성 검증용 |
| `runningmate-deploy*.parts.sha256` | 분할본과 같은 release asset | 분할본 검증용 |
| `runningmate-deploy*.reassemble.txt` | 분할본과 같은 release asset | 재조립 안내 |

## 권장 흐름

1. 소스 변경을 기능별로 커밋한다.
2. 배포 기준 commit에 tag를 붙인다.
3. 해당 commit에서 배포 압축본을 만든다.
4. `sha256sum`을 생성한다.
5. GitHub Release에 tag, 압축본, 체크섬, 재조립 안내 파일을 함께 올린다.
6. 개인 서버에서는 release asset을 내려받아 체크섬을 검증한 뒤 배포한다.

예시:

```bash
cd /opt/app/project/main
git tag -a deploy-2026-06-12-1 -m "runningmate deploy 2026-06-12"
git push origin deploy-2026-06-12-1

sha256sum runningmate-deploy.tar.gz > runningmate-deploy.sha256
sha256sum -c runningmate-deploy.sha256
```

GitHub CLI가 없으면 GitHub 웹 UI의 Releases 화면에서 tag를 선택하고 파일을 업로드한다.

## 로컬 보관 정책

- 작업 중인 서버에는 최신 1개와 직전 1개만 남긴다.
- 오래된 압축본은 외부 release/storage에 올라간 뒤 삭제한다.
- 운영 secret, DB dump, 사용자 업로드 데이터는 앱 배포 압축본에 섞지 않는다.
- 백업 파일은 `scripts/backup-runningmate-private-server.sh`와 별도 백업 정책으로 관리한다.

## Git ignore

배포 산출물은 `.gitignore`에서 제외한다. 실수로 stage하지 않기 위해 root에 생성되는 `runningmate-deploy*` 압축본, 분할본, 체크섬, 재조립 안내 파일을 모두 ignore한다.
