# ClamAV 설치 및 기록 업로드 악성 파일 스캔 복구

## 사용자 원본 요청

정상 수정은 ClamAV 설치 또는 RUNNINGMATE_AV_SCANNER 지정입니다. 이걸 해주면 안돼?

## 처리 내용

- 서버 런타임에 `clamav`, `clamav-freshclam` 패키지를 설치했다.
- `freshclam`으로 ClamAV 시그니처 DB를 갱신했다.
- 앱의 업로드 보안 검사 로직이 기본 탐색하는 `clamscan` 실행 파일을 사용할 수 있게 했다.
- 별도 `RUNNINGMATE_AV_SCANNER` 지정 없이도 기본 스캐너 경로가 동작하도록 복구했다.

## 변경 파일

- `devlog.md`
- `devlog/2026-06-11/004-clamav-upload-scan-runtime.md`

## 검증 결과

- `clamscan --version` 확인: `ClamAV 1.4.4/28027`
- `freshclam --version` 확인: `ClamAV 1.4.4/28027`
- `/var/lib/clamav`에 `main.cvd`, `daily.cvd`, `bytecode.cvd` 생성 확인
- `/etc/hosts` 클린 파일 스캔 결과 `OK` 확인
- EICAR 표준 테스트 파일 스캔 결과 `Eicar-Test-Signature FOUND` 확인

## 남은 리스크

- 현재 복구는 서버 런타임 패키지 설치 기반이라 컨테이너나 서버가 재생성되면 이미지/프로비저닝에도 ClamAV 설치 절차를 반영해야 한다.
- `freshclam` 실행 중 `NotifyClamd` 설정 경고가 출력될 수 있으나, 현재 앱 경로는 데몬이 아닌 `clamscan` 직접 실행을 사용한다.
