import Foundation
import Capacitor
import UIKit

class RunningMateBridgeViewController: CAPBridgeViewController {
    private var appBackgroundOverride: UIColor? = UIColor(red: 7.0 / 255.0, green: 17.0 / 255.0, blue: 15.0 / 255.0, alpha: 1.0)
    private var appBackgroundPrefersDarkStatusBarText: Bool = false
    private var appBackgroundColor: UIColor {
        if let appBackgroundOverride = appBackgroundOverride {
            return appBackgroundOverride
        }

        return UIColor { traits in
            if traits.userInterfaceStyle == .light {
                return UIColor(red: 247.0 / 255.0, green: 247.0 / 255.0, blue: 249.0 / 255.0, alpha: 1.0)
            }
            return UIColor(red: 18.0 / 255.0, green: 18.0 / 255.0, blue: 28.0 / 255.0, alpha: 1.0)
        }
    }

    override func instanceDescriptor() -> InstanceDescriptor {
        let descriptor = super.instanceDescriptor()

        // Always use the bundled Capacitor assets for production iOS builds.
        descriptor.serverURL = nil
        descriptor.appStartPath = nil
        descriptor.allowedNavigationHostnames = []

        if let bundledApp = Bundle.main.url(forResource: "public", withExtension: nil) {
            descriptor.appLocation = bundledApp
        }

        return descriptor
    }

    override func viewDidLoad() {
        super.viewDidLoad()

        applyAppBackground()
        setNeedsStatusBarAppearanceUpdate()
    }

    override func viewWillAppear(_ animated: Bool) {
        super.viewWillAppear(animated)
        applyAppBackground()
    }

    override func viewDidAppear(_ animated: Bool) {
        super.viewDidAppear(animated)
        applyAppBackground()
    }

    override func viewDidLayoutSubviews() {
        super.viewDidLayoutSubviews()
        applyAppBackground()
    }

    override func traitCollectionDidChange(_ previousTraitCollection: UITraitCollection?) {
        super.traitCollectionDidChange(previousTraitCollection)
        if appBackgroundOverride == nil {
            appBackgroundPrefersDarkStatusBarText = traitCollection.userInterfaceStyle == .light
            setNeedsStatusBarAppearanceUpdate()
        }
        applyAppBackground()
    }

    private func applyAppBackground() {
        view.window?.backgroundColor = appBackgroundColor
        view.backgroundColor = appBackgroundColor
        webView?.isOpaque = false
        webView?.backgroundColor = appBackgroundColor
        webView?.scrollView.backgroundColor = appBackgroundColor
        webView?.scrollView.subviews.forEach { $0.backgroundColor = .clear }
    }

    func setAppBackgroundColor(_ hexString: String) {
        if let color = UIColor(runningMateHexString: hexString) {
            appBackgroundOverride = color
            appBackgroundPrefersDarkStatusBarText = color.runningMatePrefersDarkStatusBarText
        } else {
            appBackgroundOverride = nil
            appBackgroundPrefersDarkStatusBarText = traitCollection.userInterfaceStyle == .light
        }
        applyAppBackground()
        view.setNeedsLayout()
        view.layoutIfNeeded()
        webView?.setNeedsLayout()
        webView?.layoutIfNeeded()
        setNeedsStatusBarAppearanceUpdate()
    }

    override var preferredStatusBarStyle: UIStatusBarStyle {
        appBackgroundPrefersDarkStatusBarText ? .darkContent : .lightContent
    }

    override func capacitorDidLoad() {
        super.capacitorDidLoad()
        bridge?.registerPluginInstance(RunningMateHealthKitPlugin())
        bridge?.registerPluginInstance(RunningMateAuthPlugin())
    }

    func handleOAuthRedirect(_ url: URL) -> Bool {
        guard let scheme = url.scheme?.lowercased(),
              ["runmate", "com.myrunningmate.run"].contains(scheme),
              url.host?.lowercased() == "oauth" else {
            return false
        }

        let source = URLComponents(url: url, resolvingAgainstBaseURL: false)
        let query = source?.percentEncodedQuery ?? ""
        let accessPath = query.isEmpty ? "/access" : "/access?\(query)"
        let escapedPath = accessPath
            .replacingOccurrences(of: "\\", with: "\\\\")
            .replacingOccurrences(of: "'", with: "\\'")

        DispatchQueue.main.async { [weak self] in
            guard let self = self else { return }
            self.setAppBackgroundColor("#07110f")
            self.webView?.evaluateJavaScript("window.location.replace('\(escapedPath)')") { [weak self] _, error in
                guard let self = self, error != nil else { return }

                var target = URLComponents()
                target.scheme = "capacitor"
                target.host = "localhost"
                target.path = "/access"
                target.percentEncodedQuery = source?.percentEncodedQuery

                if let targetURL = target.url {
                    self.webView?.load(URLRequest(url: targetURL))
                }
            }
        }
        return true
    }
}

private extension UIColor {
    convenience init?(runningMateHexString hexString: String) {
        let normalized = hexString.trimmingCharacters(in: .whitespacesAndNewlines)
            .trimmingCharacters(in: CharacterSet(charactersIn: "#"))

        guard normalized.count == 6,
              let value = UInt32(normalized, radix: 16) else {
            return nil
        }

        let red = CGFloat((value & 0xFF0000) >> 16) / 255.0
        let green = CGFloat((value & 0x00FF00) >> 8) / 255.0
        let blue = CGFloat(value & 0x0000FF) / 255.0
        self.init(red: red, green: green, blue: blue, alpha: 1.0)
    }

    var runningMatePrefersDarkStatusBarText: Bool {
        var red: CGFloat = 0
        var green: CGFloat = 0
        var blue: CGFloat = 0
        var alpha: CGFloat = 0

        guard getRed(&red, green: &green, blue: &blue, alpha: &alpha) else {
            return false
        }

        let luminance = (0.2126 * red) + (0.7152 * green) + (0.0722 * blue)
        return luminance > 0.72
    }
}
