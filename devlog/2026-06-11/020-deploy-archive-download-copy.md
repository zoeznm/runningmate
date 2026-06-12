# 배포 아카이브 다운로드 복사본 생성

- **ID**: 020
- **날짜**: 2026-06-11
- **유형**: 배포 산출물

## 작업 요약

`/tmp/runningmate-deploy.tar.gz`를 원자적으로 다시 생성하고 gzip 무결성을 확인했다.
다운로드 시 0바이트로 보이는 문제를 우회하기 위해 동일한 파일을 프로젝트 루트와 `/mnt/data`에도 복사하고 checksum 파일을 함께 생성했다.

## 원문 요청사항

```text
또 다운로드해서 보면 0바이트야
```

## 변경 파일 목록

- `runningmate-deploy.tar.gz`
  - `/tmp/runningmate-deploy.tar.gz`와 동일한 다운로드용 복사본.
- `runningmate-deploy.sha256`
  - 프로젝트 루트 복사본의 SHA256 checksum.
- `devlog.md`
  - 2026-06-11 ID 020 요약 행 추가.
- `devlog/2026-06-11/020-deploy-archive-download-copy.md`
  - 작업 상세 devlog 추가.

## 확인한 내용

- `/tmp/runningmate-deploy.tar.gz`, `/opt/app/project/main/runningmate-deploy.tar.gz`, `/mnt/data/runningmate-deploy.tar.gz`가 모두 35M로 생성됨을 확인했다.
- 세 파일 모두 `gzip -t`를 통과했다.
- 세 파일의 SHA256 checksum이 모두 동일함을 확인했다.
- tar 목록 상위 30개 항목이 `/opt/app` 기준 상대경로 구조로 표시됨을 확인했다.

## 검증 결과

```text
5153421ffe2214199888f53aacabf9f2c876945f27e2049f1baa28dc3a041c20
```
