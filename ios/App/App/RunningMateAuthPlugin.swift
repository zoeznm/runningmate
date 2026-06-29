import Capacitor
import Foundation
import AuthenticationServices
import Security
import UIKit

@objc(RunningMateAuthPlugin)
class RunningMateAuthPlugin: CAPPlugin, CAPBridgedPlugin, ASWebAuthenticationPresentationContextProviding {
    let identifier = "RunningMateAuthPlugin"
    let jsName = "RunningMateAuth"
    let pluginMethods: [CAPPluginMethod] = [
        CAPPluginMethod(name: "openExternalAuth", returnType: CAPPluginReturnPromise),
        CAPPluginMethod(name: "saveAuthTokens", returnType: CAPPluginReturnPromise),
        CAPPluginMethod(name: "loadAuthTokens", returnType: CAPPluginReturnPromise),
        CAPPluginMethod(name: "clearAuthTokens", returnType: CAPPluginReturnPromise),
        CAPPluginMethod(name: "setSafeAreaBackground", returnType: CAPPluginReturnPromise)
    ]

    private var authSession: ASWebAuthenticationSession?
    private let keychainService = "com.myrunningmate.run.auth"
    private let keychainAccount = "runningmate.auth.tokens"

    @objc func openExternalAuth(_ call: CAPPluginCall) {
        guard let rawURL = call.getString("url"),
              let url = URL(string: rawURL),
              let scheme = url.scheme?.lowercased(),
              ["https", "http"].contains(scheme) else {
            call.reject("잘못된 인증 URL입니다.", "invalid_url")
            return
        }

        if #available(iOS 12.0, *) {
            let session = ASWebAuthenticationSession(url: url, callbackURLScheme: "runmate") { [weak self] callbackURL, error in
                DispatchQueue.main.async {
                    self?.authSession = nil

                    if let callbackURL = callbackURL {
                        if let controller = self?.bridge?.viewController as? RunningMateBridgeViewController {
                            _ = controller.handleOAuthRedirect(callbackURL)
                        }
                        call.resolve([
                            "opened": true,
                            "mode": "authentication_session",
                            "callbackUrl": callbackURL.absoluteString
                        ])
                        return
                    }

                    if let authError = error as? ASWebAuthenticationSessionError,
                       authError.code == .canceledLogin {
                        call.reject("소셜 로그인이 취소되었습니다.", "auth_cancelled")
                        return
                    }

                    call.reject("소셜 인증 응답을 받지 못했습니다.", "auth_failed")
                }
            }

            if #available(iOS 13.0, *) {
                session.presentationContextProvider = self
                session.prefersEphemeralWebBrowserSession = false
            }

            authSession = session
            if session.start() {
                return
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

    @objc func saveAuthTokens(_ call: CAPPluginCall) {
        guard let accessToken = call.getString("accessToken"), !accessToken.isEmpty,
              let refreshToken = call.getString("refreshToken"), !refreshToken.isEmpty else {
            call.reject("저장할 로그인 토큰이 없습니다.", "missing_tokens")
            return
        }

        let autoLogin = call.getBool("autoLogin") ?? false
        if !autoLogin {
            clearStoredAuthTokens()
            call.resolve(["saved": false])
            return
        }

        let payload: [String: Any] = [
            "accessToken": accessToken,
            "refreshToken": refreshToken,
            "autoLogin": true,
            "savedAt": Date().timeIntervalSince1970
        ]

        do {
            try saveStoredAuthTokens(payload)
            call.resolve(["saved": true])
        } catch {
            call.reject("자동 로그인 정보를 저장하지 못했습니다.", "keychain_save_failed", error)
        }
    }

    @objc func loadAuthTokens(_ call: CAPPluginCall) {
        guard let payload = loadStoredAuthTokens(),
              let accessToken = payload["accessToken"] as? String, !accessToken.isEmpty,
              let refreshToken = payload["refreshToken"] as? String, !refreshToken.isEmpty else {
            call.resolve(["hasTokens": false])
            return
        }

        call.resolve([
            "hasTokens": true,
            "accessToken": accessToken,
            "refreshToken": refreshToken,
            "autoLogin": (payload["autoLogin"] as? Bool) ?? true
        ])
    }

    @objc func clearAuthTokens(_ call: CAPPluginCall) {
        clearStoredAuthTokens()
        call.resolve(["cleared": true])
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

    private func keychainIdentityQuery() -> [String: Any] {
        return [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: keychainService,
            kSecAttrAccount as String: keychainAccount
        ]
    }

    private func saveStoredAuthTokens(_ payload: [String: Any]) throws {
        let data = try JSONSerialization.data(withJSONObject: payload, options: [])
        clearStoredAuthTokens()

        var query = keychainIdentityQuery()
        query[kSecAttrAccessible as String] = kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly
        query[kSecValueData as String] = data

        let status = SecItemAdd(query as CFDictionary, nil)
        guard status == errSecSuccess else {
            throw NSError(domain: "RunningMateAuthPlugin", code: Int(status), userInfo: [
                NSLocalizedDescriptionKey: "Keychain save failed with status \(status)"
            ])
        }
    }

    private func loadStoredAuthTokens() -> [String: Any]? {
        var query = keychainIdentityQuery()
        query[kSecReturnData as String] = true
        query[kSecMatchLimit as String] = kSecMatchLimitOne

        var result: CFTypeRef?
        let status = SecItemCopyMatching(query as CFDictionary, &result)
        guard status == errSecSuccess, let data = result as? Data else {
            return nil
        }

        return (try? JSONSerialization.jsonObject(with: data, options: [])) as? [String: Any]
    }

    private func clearStoredAuthTokens() {
        SecItemDelete(keychainIdentityQuery() as CFDictionary)
    }
}
