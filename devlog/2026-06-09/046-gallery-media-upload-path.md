# 046. 갤러리 이미지/미디어 업로드 기본 경로 보정

- 날짜: 2026-06-09
- 요청: "지금 보니까 갤러리에 들어가는 이미지들이랑 사진들은 안 보이거든 왜 그러는거야?"

## 원인

- 이미지/미디어 서빙 라우트의 기본 업로드 경로가 `/srv/runningmate/media/...`로 되어 있었다.
- 현재 서버의 실제 영속 파일은 `/opt/app/data/run_images`, `/opt/app/data/run_media`에 있었다.
- 환경변수 `RUNNINGMATE_UPLOAD_DIR`, `RUNNINGMATE_MEDIA_UPLOAD_DIR`가 설정되지 않은 상태라 라우트가 기본 경로를 보고 404를 반환했다.

## 변경 파일

- `src/route/api.run-images/controller.py`
- `src/route/api.run-media/controller.py`
- `src/route/api.parse-image/controller.py`
- `src/model/runningmate.py`

## 변경 내용

- 이미지 업로드/서빙 기본 경로를 `/opt/app/data/run_images`로 변경했다.
- 러닝 미디어 업로드/서빙 기본 경로를 `/opt/app/data/run_media`로 변경했다.
- 환경변수가 설정되어 있으면 기존처럼 환경변수 값을 우선 사용한다.

## 확인 결과

- `wiz_project_build(clean=false)` 성공.
- 앱 재시작 후 `/dashboard` HTTP 200 확인.
- `/api/run-images/45cfb71eec01429f8461d1ee0bc869c3.png` HTTP 200, `image/png` 확인.
- `/api/run-media/3b434662099242b28148ca589f22c042.jpeg` HTTP 200, `image/jpeg` 확인.
