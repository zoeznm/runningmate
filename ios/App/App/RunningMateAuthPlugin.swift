import Capacitor
import Foundation
import UIKit

@objc(RunningMateAuthPlugin)
class RunningMateAuthPlugin: CAPPlugin, CAPBridgedPlugin {
    let identifier = "RunningMateAuthPlugin"
    let jsName = "RunningMateAuth"
    let pluginMethods: [CAPPluginMethod] = [
        CAPPluginMethod(name: "openExternalAuth", returnType: CAPPluginReturnPromise),
        CAPPluginMethod(name: "setSafeAreaBackground", returnType: CAPPluginReturnPromise)
    ]

    @objc func openExternalAuth(_ call: CAPPluginCall) {
        guard let rawURL = call.getString("url"),
              let url = URL(string: rawURL),
              let scheme = url.scheme?.lowercased(),
              ["https", "http"].contains(scheme) else {
            call.reject("잘못된 인증 URL입니다.", "invalid_url")
            return
        }

        DispatchQueue.main.async {
            UIApplication.shared.open(url, options: [:]) { success in
                if success {
                    call.resolve(["opened": true])
                } else {
                    call.reject("인증 화면을 열지 못했습니다.", "open_failed")
                }
            }
        }
    }

    @objc func setSafeAreaBackground(_ call: CAPPluginCall) {
        let color = call.getString("color") ?? ""
        DispatchQueue.main.async {
            if let controller = self.bridge?.viewController as? RunningMateBridgeViewController {
                controller.setAppBackgroundColor(color)
            }
            call.resolve()
        }
    }
}
