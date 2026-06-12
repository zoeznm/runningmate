# 다운로드 제한 대응 배포 아카이브 분할

- **ID**: 023
- **날짜**: 2026-06-11
- **유형**: 배포 산출물

## 작업 요약

다운로드 제한 20MB를 피하기 위해 `runningmate-deploy-35m.tar.gz`를 18MB 단위 part 파일로 분할했다.
분할 파일을 다시 합친 결과가 원본 archive와 동일한 SHA256을 갖고, gzip 무결성 검사를 통과함을 확인했다.

## 원문 요청사항

```text
{"code": 404, "data": {"message": "파일은 최대 20.0 MB까지 다운로드할 수 있습니다."}}
```

## 변경 파일 목록

- `runningmate-deploy-35m.tar.gz.part-aa`
  - 18MB 이하 다운로드용 분할 파일 1.
- `runningmate-deploy-35m.tar.gz.part-ab`
  - 18MB 이하 다운로드용 분할 파일 2.
- `runningmate-deploy-35m.parts.sha256`
  - part 파일별 SHA256 checksum 목록.
- `runningmate-deploy-35m.reassemble.txt`
  - part 파일 재조립 안내.
- `devlog.md`
  - 2026-06-11 ID 023 요약 행 추가.
- `devlog/2026-06-11/023-deploy-archive-split-for-download-limit.md`
  - 작업 상세 devlog 추가.

## 확인한 내용

- `part-aa`: `18874368 bytes` (`18M`)
- `part-ab`: `17126939 bytes` (`17M`)
- 두 파일 모두 20MB 제한보다 작다.
- `/tmp/runningmate-deploy-reassembled.tar.gz`로 재조립 후 `gzip -t` 통과.
- 재조립 파일 SHA256이 원본과 동일하다.

## 검증 결과

```text
5153421ffe2214199888f53aacabf9f2c876945f27e2049f1baa28dc3a041c20  /opt/app/project/main/runningmate-deploy-35m.tar.gz
5153421ffe2214199888f53aacabf9f2c876945f27e2049f1baa28dc3a041c20  /tmp/runningmate-deploy-reassembled.tar.gz
```
