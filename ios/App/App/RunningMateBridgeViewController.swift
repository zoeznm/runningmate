import Capacitor

class RunningMateBridgeViewController: CAPBridgeViewController {
    override func capacitorDidLoad() {
        super.capacitorDidLoad()
        bridge?.registerPluginInstance(RunningMateHealthKitPlugin())
    }
}
