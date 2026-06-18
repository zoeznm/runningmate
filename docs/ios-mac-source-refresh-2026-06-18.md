# iOS Mac 프로젝트 소스 최신화 절차

작성일: 2026-06-18
대상 경로: `/Users/kimbomi/Desktop/app/project/main`

## 왜 필요한가

Mac에서 아래 명령이 아무것도 출력하지 않으면 Mac 로컬 프로젝트가 최신 소스가 아니다.

```bash
cd /Users/kimbomi/Desktop/app/project/main
grep -n "descriptor.serverURL = nil" ios/App/App/RunningMateBridgeViewController.swift
```

`npm run ios:sync`, Xcode `Clean Build Folder`, iPhone 앱 삭제는 Mac 로컬의 Swift 소스 파일을 최신화하지 않는다. 예전 Swift 파일이 남아 있으면 같은 예전 코드로 계속 다시 빌드된다.

## 최신화 기준

최신 `ios/App/App/RunningMateBridgeViewController.swift`에는 아래 코드가 있어야 한다.

```swift
override func instanceDescriptor() -> InstanceDescriptor {
    let descriptor = super.instanceDescriptor()

    descriptor.serverURL = nil
    descriptor.appStartPath = nil
    descriptor.allowedNavigationHostnames = []

    if let bundledApp = Bundle.main.url(forResource: "public", withExtension: nil) {
        descriptor.appLocation = bundledApp
    }

    return descriptor
}
```

## 순서

1. Mac의 `/Users/kimbomi/Desktop/app/project/main` 프로젝트 소스 자체를 최신 상태로 반영한다.

Git 저장소로 관리 중이면 먼저 아래 명령을 실행한다.

```bash
cd /Users/kimbomi/Desktop/app/project/main
git status
git fetch origin
git pull --ff-only origin main
```

`git pull`이 `Already up to date`인데도 아래 `grep` 결과가 없으면, 현재 iOS 수정이 아직 원격 GitHub에 올라가지 않은 상태다. 이 경우 Git 명령만으로는 Mac 프로젝트가 최신화되지 않는다.

2. 다시 아래 명령으로 최신 Swift 코드가 들어왔는지 확인한다.

```bash
cd /Users/kimbomi/Desktop/app/project/main
grep -n "descriptor.serverURL = nil" ios/App/App/RunningMateBridgeViewController.swift
```

3. 출력이 나오면 그 다음에 iOS 동기화와 재설치를 진행한다.

```bash
npm install
rm -f ios/App/App/capacitor.config.json
npm run ios:sync
npm run ios:verify-config
npm run ios:open
```

4. Xcode에서 `Product > Clean Build Folder`를 실행한다.
5. iPhone에서 기존 앱을 삭제한다.
6. Xcode에서 다시 Run한다.

## 정상 기준

- Xcode 콘솔에 `Loading app at https://run.myrunningmate.com/dashboard...`가 나오면 안 된다.
- Xcode에서 `RunningMateBridgeViewController.swift`를 열었을 때 `descriptor.serverURL = nil`이 보여야 한다.
- 앱 아이콘도 최신 `AppIcon.appiconset`으로 바뀌어야 한다.
