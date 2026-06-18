# 러닝메이트 iOS 앱스토어 배포 순서

작성일: 2026-06-17
대상: `https://run.myrunningmate.com/` 도메인 연결 이후 Apple App Store 첫 배포

## 현재 프로젝트 상태

| 항목 | 상태 |
| --- | --- |
| iOS shell | `ios/` Capacitor 프로젝트 존재 |
| 앱 이름 | `러닝메이트` |
| 확정 Bundle ID | `com.myrunningmate.run` |
| 현재 앱 버전 | `1.0`, build `1` |
| iOS 최소 버전 | 15.0 |
| 앱 실행 방식 | `webDir` 내부 번들, 시작 라우트 `/access` |
| API 운영 Origin | `https://run.myrunningmate.com` |
| 앱 아이콘/스플래시 | `ios/App/App/Assets.xcassets/`에 포함 |
| HealthKit | entitlement와 사용 목적 문구 포함 |
| iOS 개인정보 목적 문구 | HealthKit, 카메라, 사진 보관함, 마이크, 위치 문구 포함 |
| 공개 법적 페이지 | `/privacy`, `/terms`, `/account/delete` 구현 이력 있음 |
| Apple Developer 유료 계정 | 보유 확인 |
| 외부 Mac/iPhone 접속 | 정상 확인 |

## Bundle ID 확정 기준

Bundle ID는 앱스토어에 보이는 이름이 아니라 Apple이 앱을 구분하는 내부 고유 식별자다. Xcode 앱, Apple Developer App ID, App Store Connect 앱 레코드가 모두 같은 Bundle ID를 써야 서명, TestFlight, 앱 업데이트가 이어진다.

러닝메이트는 운영 도메인 `run.myrunningmate.com`을 기준으로 `com.myrunningmate.run`을 확정안으로 사용한다.

| 후보 | 판단 |
| --- | --- |
| `net.seasonai.run.matomabo` | 기존 개발용 값이다. 앱스토어 공개 브랜드와 도메인이 맞지 않아 첫 배포 전 변경하는 편이 낫다. |
| `com.myrunningmate.run` | 운영 도메인을 reverse-DNS 형식으로 뒤집은 값이다. 브랜드와 도메인이 맞고 향후 앱 업데이트에도 쓰기 좋다. |

확정은 아래 세 곳이 모두 같은 값일 때 완료된다.

1. `capacitor.config.json`의 `appId`
2. Xcode target의 `PRODUCT_BUNDLE_IDENTIFIER`
3. Apple Developer > Identifiers에 등록한 Explicit App ID

Apple Developer에서 `com.myrunningmate.run`이 이미 사용 중이라고 나오면 `com.myrunningmate.runningmate`처럼 같은 도메인 기반의 다른 값을 정하고, 위 세 곳을 같은 값으로 다시 맞춘다.

## Apple Developer Capabilities

첫 앱스토어 배포에서 Apple Developer > Identifiers > `com.myrunningmate.run`에 켤 capability는 HealthKit만 둔다.

| Capability | 지금 설정 | 이유 |
| --- | --- | --- |
| HealthKit | 켬 | 네이티브 `RunningMateHealthKitPlugin`이 Apple Watch/HealthKit 러닝 기록을 읽는다. |
| Associated Domains | 끔 | Universal Links, webcredentials, passkeys를 아직 구현하지 않았다. |
| Push Notifications | 끔 | APNs 토큰 등록/네이티브 푸시 수신 구현이 없다. 웹 Notification API만으로는 켜지 않는다. |
| Sign in with Apple | 끔 | 현재 Google/Naver 소셜 버튼을 숨긴 상태이고 이메일 로그인 중심이다. 제3자 소셜 로그인을 다시 켜면 함께 검토한다. |
| In-App Purchase | 끔 | 유료 구독/인앱결제 상품을 아직 구현하지 않았다. |
| Background Modes | 끔 | 백그라운드 위치 추적, 오디오, HealthKit background delivery를 구현하지 않았다. |
| App Groups/iCloud/CloudKit/Apple Pay | 끔 | 현재 앱 구조에서 쓰지 않는다. |

Capability는 기능을 실제로 구현했을 때만 켠다. 켜기만 하고 앱에서 쓰지 않으면 심사 질문과 설정 리스크가 늘어난다.

Capability와 별도로 `Info.plist` 개인정보 목적 문구는 필요하다. 현재 앱은 파일 업로드와 위치 기반 날씨를 쓰므로 아래 문구를 포함한다.

| Info.plist key | 이유 |
| --- | --- |
| `NSHealthShareUsageDescription` | HealthKit 러닝 기록 읽기 |
| `NSCameraUsageDescription` | 러닝 기록 사진/영상 촬영 업로드 |
| `NSPhotoLibraryUsageDescription` | 사진 보관함의 러닝 캡처, 사진, 영상 선택 업로드 |
| `NSMicrophoneUsageDescription` | 기기에서 영상을 촬영할 때 오디오가 포함될 수 있음 |
| `NSLocationWhenInUseUsageDescription` | 러닝 기록 날짜의 날씨와 지역 정보 표시 |

## 배포 전 결정해야 할 것

1. Apple Developer에서 `com.myrunningmate.run` Explicit App ID를 등록한다.
   - HealthKit capability를 켠다.
   - Xcode Signing Team에서 같은 Bundle ID가 잡히는지 확인한다.
2. 심사용 테스트 계정을 만든다.
   - 이메일/비밀번호 로그인 가능
   - 샘플 러닝 기록 1개 이상
   - 계정 삭제 경로 확인 가능
3. 앱스토어 공개 정보 초안을 준비한다.
   - 앱 이름: 러닝메이트
   - 카테고리: Health & Fitness 권장
   - 지원 URL: `https://run.myrunningmate.com/`
   - 개인정보처리방침 URL: `https://run.myrunningmate.com/privacy`
   - 계정 삭제 안내 URL: `https://run.myrunningmate.com/account/delete`

## 지금부터 바로 할 일

Apple Developer 계정, Bundle ID, HealthKit capability, 운영 도메인 확인까지 끝났다면 다음 순서로 진행한다.

1. Mac에 최신 프로젝트를 가져온다.
2. Mac 터미널에서 iOS 프로젝트를 동기화한다.

```bash
cd /path/to/runningmate/project/main
npm install
npm run ios:sync
npm run ios:open
```

3. Xcode에서 Signing & Capabilities를 확인한다.
   - Team: 보유 중인 Apple Developer Team
   - Bundle Identifier: `com.myrunningmate.run`
   - Capability: HealthKit만 켜져 있어야 함
   - Version: `1.0`
   - Build: `1`
4. iPhone 실기기에 먼저 Run한다.
   - 앱 첫 화면이 원격 Safari가 아니라 앱 내부 `/access` 로그인 화면으로 열리는지 확인
   - 로그인, 기록 업로드, 사진/영상 선택, 위치 기반 날씨, HealthKit 권한 팝업 확인
   - `/privacy`, `/terms`, `/account/delete` 진입 확인
5. App Store Connect에서 앱 레코드를 만든다.
   - Platform: iOS
   - Name: 러닝메이트
   - Bundle ID: `com.myrunningmate.run`
   - SKU: `runningmate-ios`
   - Primary Language: Korean
6. Xcode에서 Product > Archive를 실행한다.
7. Organizer에서 Distribute App > App Store Connect > Upload를 선택해 빌드를 올린다.
8. App Store Connect에서 빌드 처리 완료를 기다린다.
9. TestFlight Internal Testing 그룹을 만들고 본인 계정에 먼저 배포한다.
10. iPhone TestFlight 빌드에서 핵심 기능을 다시 테스트한다.
11. 앱스토어 메타데이터를 채운다.
    - 스크린샷
    - 설명, 키워드, 카테고리
    - Support URL
    - Privacy Policy URL
    - App Privacy 답변
    - Age Rating
    - 심사용 테스트 계정
12. App Review Notes를 작성하고 Submit for Review를 누른다.

심사 제출 전 Review Notes 예시:

```text
테스트 계정:
이메일:
비밀번호:

주요 확인 경로:
- 러닝 기록 업로드/수동 입력
- HealthKit 러닝 기록 불러오기
- 개인정보처리방침: https://run.myrunningmate.com/privacy
- 이용약관: https://run.myrunningmate.com/terms
- 계정 삭제: https://run.myrunningmate.com/account/delete

HealthKit 사용 목적:
사용자가 허용한 Apple Watch/HealthKit 러닝 완료 기록, 거리, 시간, 심박수, 칼로리, 걸음 수를 러닝메이트 기록으로 불러오기 위해 사용합니다.
```

## 남은 순서

### 1. 운영 도메인 최종 점검

서버에서 아래 응답을 먼저 확인한다.

```bash
curl -I https://run.myrunningmate.com/dashboard
curl -I https://run.myrunningmate.com/privacy
curl -I https://run.myrunningmate.com/terms
curl -I https://run.myrunningmate.com/account/delete
curl -I https://run.myrunningmate.com/sw.js
curl https://run.myrunningmate.com/healthz
```

`/api/`, `/auth/`, `/healthz`, `/sw.js`, `/manifest.json`은 SPA `index.html` fallback이 아니라 실제 API/정적 파일로 응답해야 한다.

2026-06-17 현재 이 서버에서 확인한 상태:

| 확인 | 결과 |
| --- | --- |
| `http://127.0.0.1:3000/healthz` | 200 JSON |
| `http://127.0.0.1:3000/dashboard` | 200 HTML |
| `https://run.myrunningmate.com/healthz`를 `127.0.0.1`로 강제 해석 | 200 JSON |
| `https://run.myrunningmate.com/sw.js`를 `127.0.0.1`로 강제 해석 | 200 JavaScript |
| `https://run.myrunningmate.com/api/auth/login`를 `127.0.0.1`로 강제 해석 | 200 JSON 인증 실패 응답 |
| 이 서버에서 공인 DNS `49.165.96.213`로 직접 접속 | timeout |
| 외부 브라우징 경로의 `https://run.myrunningmate.com/` | 앱 로딩 HTML 확인 |
| 사용자 외부 Mac/iPhone 접속 | 정상 확인 |

공인 DNS 직접 접속 timeout은 서버 내부에서 자기 공인 IP로 되돌아가는 hairpin NAT 문제로 본다. 외부 Mac/iPhone 접속은 정상 확인됐으므로 제출 전에는 같은 외부 환경에서 `/privacy`, `/terms`, `/account/delete`, `/healthz`, `/sw.js`까지 한 번 더 확인한다.

### 2. Mac 개발 환경 준비

Mac에서 진행한다. 이 Linux 서버만으로는 App Store용 `.ipa` 생성과 업로드를 끝낼 수 없다.

1. Xcode 설치 및 Apple Account 로그인
2. 보유 중인 Apple Developer 유료 계정으로 Xcode Signing Team 선택
3. 이 저장소를 Mac으로 가져오기
4. 프로젝트 루트에서 의존성 설치와 iOS 동기화

```bash
cd /path/to/runningmate/project/main
npm install
npm run ios:sync
npm run ios:open
```

Capacitor iOS 앱은 Xcode에서 일반 네이티브 앱처럼 빌드/배포한다.

### 3. Apple Developer에서 App ID 등록

Apple Developer > Certificates, Identifiers & Profiles에서 Explicit App ID를 등록한다.

| 값 | 입력 기준 |
| --- | --- |
| Description | RunningMate 또는 러닝메이트 |
| Bundle ID | `com.myrunningmate.run` |
| Capabilities | HealthKit 활성화 |

Xcode Signing & Capabilities에서도 같은 Team과 Bundle ID가 잡혀야 한다.

### 4. Xcode에서 실기기 테스트

1. `ios/App/App.xcodeproj` 또는 Xcode가 여는 App 프로젝트를 연다.
2. Signing Team 지정
3. Bundle Identifier 확인
4. Version `1.0`, Build `1` 확인
5. iPhone 실기기에서 실행
6. 아래 흐름을 확인
   - 앱 첫 진입이 앱 내부 `/access` 로그인 화면으로 열리는지
   - 로그인/회원가입
   - 기록 업로드
   - HealthKit 권한 팝업과 데이터 읽기
   - 개인정보/약관/계정 삭제 페이지
   - 네트워크 끊김 또는 서버 오류 시 흰 화면으로 멈추지 않는지

### 5. App Store Connect 앱 레코드 생성

App Store Connect > Apps > New App에서 앱 레코드를 만든다.

| 항목 | 입력 기준 |
| --- | --- |
| Platform | iOS |
| Name | 러닝메이트 |
| Primary Language | Korean |
| Bundle ID | Apple Developer에 등록한 Bundle ID |
| SKU | `runningmate-ios` 같은 내부 식별자 |
| User Access | 필요 시 Full Access |

앱 레코드를 만들기 전에 Business 영역의 최신 계약 동의가 끝나 있어야 한다.

### 6. Archive와 빌드 업로드

Xcode에서 진행한다.

1. 대상 기기를 `Any iOS Device` 또는 실제 기기로 선택
2. Product > Archive
3. Organizer에서 Archive 선택
4. Distribute App
5. App Store Connect 업로드
6. App Store Connect에서 빌드 처리 완료 이메일 대기

업로드된 빌드는 Bundle ID, version, build number 조합으로 앱 레코드에 연결된다.

### 7. TestFlight 내부 테스트

App Store 심사 전에 TestFlight에서 내부 테스트를 먼저 한다.

1. 내부 테스터 추가
2. 빌드 배포
3. iPhone에서 설치
4. 로그인, 업로드, HealthKit, 계정 삭제 진입, 개인정보/약관 링크 확인
5. 문제가 있으면 build number를 `2`, `3`처럼 올려 다시 Archive/업로드

### 8. 앱스토어 메타데이터 입력

App Store Connect에서 아래를 채운다.

| 항목 | 기준 |
| --- | --- |
| Screenshots | iPhone 스크린샷 1~10장, 필요한 디스플레이 크기별 업로드 |
| Description | 러닝 기록, 캘린더, 목표, AI 페이서, 커뮤니티 중심으로 작성 |
| Keywords | 러닝, 달리기, 기록, 페이스, 운동 등 |
| Support URL | `https://run.myrunningmate.com/` 또는 support 안내 페이지 |
| Privacy Policy URL | `https://run.myrunningmate.com/privacy` |
| App Privacy | 이메일, 러닝/피트니스, 건강, 사진/영상, 사용자 콘텐츠, 사용량/진단 로그 등 실제 수집 항목 기준으로 답변 |
| Age Rating | 건강/커뮤니티/사용자 생성 콘텐츠 기준으로 정확히 답변 |

HealthKit 데이터는 광고 타겟팅이나 추적 목적으로 쓰지 않는다고 심사 메모에 명확히 적는다.

### 9. 심사 제출

심사 제출 전 App Review Notes에 아래 내용을 적는다.

```text
테스트 계정:
이메일:
비밀번호:

주요 기능:
- 러닝 기록 업로드/수동 입력
- 러닝 캘린더와 목표 관리
- HealthKit 러닝 데이터 읽기
- 개인정보처리방침: https://run.myrunningmate.com/privacy
- 계정 삭제: 앱 설정 또는 https://run.myrunningmate.com/account/delete

HealthKit 사용 목적:
사용자가 허용한 러닝 완료 기록, 거리, 시간, 심박수, 칼로리, 걸음 수를 러닝메이트 기록으로 불러오기 위해 사용합니다.
```

제출 후 반려가 오면 Resolution Center의 문구를 기준으로 고친 뒤 build number를 올려 다시 제출한다.

## 심사 리스크

| 리스크 | 대응 |
| --- | --- |
| 단순 웹사이트 래퍼로 보일 가능성 | HealthKit, 모바일 업로드, 앱형 계정/삭제 흐름처럼 iOS 앱에서 제공하는 실제 기능을 심사 메모와 스크린샷에 드러낸다. |
| 계정 생성 앱의 계정 삭제 요구 | `/account/delete`와 앱 설정 진입이 실제로 동작하는지 TestFlight에서 확인한다. |
| 개인정보/건강 데이터 고지 누락 | Privacy Policy와 App Privacy 답변에 러닝, 건강, 사진/영상, AI 대화, 로그 수집을 실제 처리 기준으로 맞춘다. |
| 불필요한 capability 활성화 | 첫 배포는 HealthKit만 켠다. Push, Associated Domains, Sign in with Apple, IAP는 구현 전까지 끄고 둔다. |
| 개인정보 목적 문구 누락 | 사진/영상 업로드와 위치 기반 날씨 때문에 `Info.plist`의 카메라, 사진, 마이크, 위치 문구를 유지한다. |
| 운영 도메인 API fallback 오류 | `/api/`, `/auth/`, `/healthz`, `/sw.js`가 HTML fallback이 아닌지 제출 전 재점검한다. |
| 서버 내부 공인 도메인 timeout | 외부 Mac/iPhone 접속은 정상 확인됐으므로 hairpin NAT 이슈로 보고, 제출 전 외부 환경에서 주요 경로만 재검증한다. |
| Bundle ID 등록 실패 | `com.myrunningmate.run`이 Apple Developer에서 이미 사용 중이면 `com.myrunningmate.runningmate` 같은 대체값으로 코드와 Apple 설정을 모두 같이 바꾼다. |

## 공식 참고

- Apple Developer Program 가입: https://developer.apple.com/programs/enroll/
- App ID 등록: https://developer.apple.com/help/account/identifiers/register-an-app-id/
- Capability 추가: https://developer.apple.com/documentation/xcode/adding-capabilities-to-your-app
- iOS 지원 capability: https://developer.apple.com/help/account/reference/supported-capabilities-ios/
- App Store Connect 앱 레코드 생성: https://developer.apple.com/help/app-store-connect/create-an-app-record/add-a-new-app/
- Xcode 배포/Archive: https://developer.apple.com/documentation/xcode/distributing-your-app-for-beta-testing-and-releases
- 빌드 업로드: https://developer.apple.com/help/app-store-connect/manage-builds/upload-builds/
- TestFlight 내부 테스터: https://developer.apple.com/help/app-store-connect/test-a-beta-version/add-internal-testers/
- 심사 제출: https://developer.apple.com/help/app-store-connect/manage-submissions-to-app-review/submit-an-app/
- App Review Guidelines: https://developer.apple.com/app-store/review/guidelines/
- 계정 삭제 요구사항: https://developer.apple.com/support/offering-account-deletion-in-your-app/
- App Privacy 정보: https://developer.apple.com/app-store/app-privacy-details/
- 스크린샷 사양: https://developer.apple.com/help/app-store-connect/reference/app-information/screenshot-specifications/
- Capacitor iOS 배포: https://capacitorjs.com/docs/ios/deploying-to-app-store
