import Capacitor
import Foundation
import AuthenticationServices
import UIKit

@objc(RunningMateAuthPlugin)
class RunningMateAuthPlugin: CAPPlugin, CAPBridgedPlugin, ASWebAuthenticationPresentationContextProviding {
    let identifier = "RunningMateAuthPlugin"
    let jsName = "RunningMateAuth"
    let pluginMethods: [CAPPluginMethod] = [
        CAPPluginMethod(name: "openExternalAuth", returnType: CAPPluginReturnPromise),
        CAPPluginMethod(name: "setSafeAreaBackground", returnType: CAPPluginReturnPromise)
    ]

    private var authSession: ASWebAuthenticationSession?

    @objc func openExternalAuth(_ call: CAPPluginCall) {
        guard let rawURL = call.getString("url"),
              let url = URL(string: rawURL),
              let scheme = url.scheme?.lowercased(),
              ["https", "http"].contains(scheme) else {
            call.reject("잘못된 인증 URL입니다.", "invalid_url")
            return
        }

        if #available(iOS 12.0, *) {
            let session = ASWebAuthenticationSession(url: url, callbackURLScheme: "runmate") { [weak self] callbackURL, _ in
                DispatchQueue.main.async {
                    self?.authSession = nil
                    guard let callbackURL = callbackURL else {
                        return
                    }
                    if let controller = self?.bridge?.viewController as? RunningMateBridgeViewController {
                        _ = controller.handleOAuthRedirect(callbackURL)
                    }
                }
            }

            if #available(iOS 13.0, *) {
                session.presentationContextProvider = self
                session.prefersEphemeralWebBrowserSession = false
            }

            authSession = session
            if session.start() {
                call.resolve(["opened": true, "mode": "authentication_session"])
            } else {
                authSession = nil
                call.reject("인증 화면을 열지 못했습니다.", "open_failed")
            }
            return
        }

        DispatchQueue.main.async {
            UIApplication.shared.open(url, options: [:]) { success in
                if success {
                    call.resolve(["opened": true, "mode": "external_browser"])
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

    @available(iOS 12.0, *)
    func presentationAnchor(for session: ASWebAuthenticationSession) -> ASPresentationAnchor {
        if let window = bridge?.viewController?.view.window {
            return window
        }

        if #available(iOS 13.0, *) {
            for scene in UIApplication.shared.connectedScenes {
                guard let windowScene = scene as? UIWindowScene else { continue }
                for window in windowScene.windows where window.isKeyWindow {
                    return window
                }
            }
        }

        return ASPresentationAnchor()
    }
}
