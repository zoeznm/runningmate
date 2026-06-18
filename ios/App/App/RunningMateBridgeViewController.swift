import Foundation
import Capacitor
import UIKit

class RunningMateBridgeViewController: CAPBridgeViewController {
    private let appBackgroundColor = UIColor(red: 18.0 / 255.0, green: 18.0 / 255.0, blue: 28.0 / 255.0, alpha: 1.0)

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

        view.backgroundColor = appBackgroundColor
        webView?.isOpaque = false
        webView?.backgroundColor = appBackgroundColor
        webView?.scrollView.backgroundColor = appBackgroundColor
        setNeedsStatusBarAppearanceUpdate()
    }

    override var preferredStatusBarStyle: UIStatusBarStyle {
        .lightContent
    }

    override func capacitorDidLoad() {
        super.capacitorDidLoad()
        bridge?.registerPluginInstance(RunningMateHealthKitPlugin())
    }
}
