# 이름 변경 배포 아카이브 복사 및 검증

- **ID**: 022
- **날짜**: 2026-06-11
- **유형**: 배포 산출물

## 작업 요약

정상 생성된 `/tmp/runningmate-deploy.tar.gz`를 `/opt/app/project/main/runningmate-deploy-35m.tar.gz` 이름으로 복사했다.
복사본 크기, gzip 무결성, SHA256 checksum을 확인했다.

## 원문 요청사항

```text
/tmp/runningmate-deploy.tar.gz 말고, 이름을 바꿔서 프로젝트 루트에 복사해줘.

cp /tmp/runningmate-deploy.tar.gz /opt/app/project/main/runningmate-deploy-35m.tar.gz
ls -lh /opt/app/project/main/runningmate-deploy-35m.tar.gz
gzip -t /opt/app/project/main/runningmate-deploy-35m.tar.gz
sha256sum /opt/app/project/main/runningmate-deploy-35m.tar.gz

그리고 /opt/app/project/main/runningmate-deploy-35m.tar.gz 를 다운로드 파일로 제공해줘.
```

## 변경 파일 목록

- `runningmate-deploy-35m.tar.gz`
  - `/tmp/runningmate-deploy.tar.gz`를 이름을 바꿔 프로젝트 루트에 복사.
- `devlog.md`
  - 2026-06-11 ID 022 요약 행 추가.
- `devlog/2026-06-11/022-deploy-archive-renamed-project-copy.md`
  - 작업 상세 devlog 추가.

## 확인한 내용

- 복사본 크기: `35M`
- `gzip -t /opt/app/project/main/runningmate-deploy-35m.tar.gz` 통과.
- SHA256: `5153421ffe2214199888f53aacabf9f2c876945f27e2049f1baa28dc3a041c20`

## 검증 결과

```text
-rw-r--r-- 1 root root 35M Jun 11 16:32 /opt/app/project/main/runningmate-deploy-35m.tar.gz
5153421ffe2214199888f53aacabf9f2c876945f27e2049f1baa28dc3a041c20  /opt/app/project/main/runningmate-deploy-35m.tar.gz
```
