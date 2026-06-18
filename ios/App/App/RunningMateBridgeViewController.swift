import Foundation
import Capacitor

class RunningMateBridgeViewController: CAPBridgeViewController {
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

    override func capacitorDidLoad() {
        super.capacitorDidLoad()
        bridge?.registerPluginInstance(RunningMateHealthKitPlugin())
    }
}
