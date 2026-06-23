import Foundation
import HealthKit
import SwiftUI
import WatchConnectivity

final class RunMateWatchWorkoutManager: NSObject, ObservableObject {
    static let shared = RunMateWatchWorkoutManager()

    @Published var statusText = "iPhone에서 러닝을 시작해줘"
    @Published var heartRateText = "-- bpm"
    @Published var distanceText = "0.00 km"
    @Published var paceText = "-- /km"
    @Published var canPause = false
    @Published var canResume = false
    @Published var canStop = false

    private let healthStore = HKHealthStore()
    private var workoutSession: HKWorkoutSession?
    private var workoutBuilder: HKLiveWorkoutBuilder?
    private var startedAt: Date?
    private var runId: String?
    private var metricsTimer: Timer?
    private var lastMetricsSentAt: Date = .distantPast
    private var lastHeartRateTimestamp: TimeInterval = 0

    private var latestHeartRate: Double?
    private var heartRateSum: Double = 0
    private var heartRateCount: Double = 0
    private var distanceMeters: Double = 0
    private var activeEnergyKcal: Double = 0
    private var stepCount: Double = 0

    override private init() {
        super.init()
        activateConnectivity()
    }

    func start(runId: String?, runType: String, configuration: HKWorkoutConfiguration? = nil) {
        if workoutSession != nil {
            if let runId = runId, !runId.isEmpty {
                self.runId = runId
            }
            sendMetrics(force: true)
            return
        }

        guard HKHealthStore.isHealthDataAvailable() else {
            sendError("Apple Watch에서 건강 데이터를 사용할 수 없어.")
            return
        }

        requestHealthKitAccess { [weak self] success in
            DispatchQueue.main.async {
                guard let self = self else { return }
                guard success else {
                    self.statusText = "건강 접근 권한이 필요해"
                    self.sendError("Apple Watch 건강 접근 권한을 허용해줘.")
                    return
                }
                self.startWorkoutSession(runId: runId, runType: runType, configuration: configuration)
            }
        }
    }

    func pause() {
        workoutSession?.pause()
        statusText = "일시정지"
        canPause = false
        canResume = workoutSession != nil
        sendMetrics(force: true)
    }

    func resume() {
        workoutSession?.resume()
        statusText = "러닝 중"
        canPause = workoutSession != nil
        canResume = false
        sendMetrics(force: true)
    }

    func stop() {
        guard let builder = workoutBuilder else {
            cleanupWorkout()
            return
        }

        metricsTimer?.invalidate()
        metricsTimer = nil
        workoutSession?.end()
        sendMetrics(force: true)

        let endedAt = Date()
        builder.endCollection(withEnd: endedAt) { [weak self] _, _ in
            builder.finishWorkout { _, _ in
                DispatchQueue.main.async {
                    self?.cleanupWorkout()
                }
            }
        }
    }

    private func startWorkoutSession(runId: String?, runType: String, configuration: HKWorkoutConfiguration? = nil) {
        let configuration = configuration ?? workoutConfiguration(for: runType)

        do {
            let session = try HKWorkoutSession(healthStore: healthStore, configuration: configuration)
            let builder = session.associatedWorkoutBuilder()
            builder.dataSource = HKLiveWorkoutDataSource(healthStore: healthStore, workoutConfiguration: configuration)
            session.delegate = self
            builder.delegate = self

            self.workoutSession = session
            self.workoutBuilder = builder
            self.startedAt = Date()
            self.runId = runId
            self.latestHeartRate = nil
            self.heartRateSum = 0
            self.heartRateCount = 0
            self.distanceMeters = 0
            self.activeEnergyKcal = 0
            self.stepCount = 0
            self.statusText = "러닝 중"
            self.canPause = true
            self.canResume = false
            self.canStop = true

            let startDate = startedAt ?? Date()
            session.startActivity(with: startDate)
            builder.beginCollection(withStart: startDate) { [weak self] _, error in
                DispatchQueue.main.async {
                    if let error = error {
                        self?.statusText = "측정 시작 실패"
                        self?.sendError(error.localizedDescription)
                        return
                    }
                    self?.startMetricsTimer()
                    self?.sendMetrics(force: true)
                }
            }
        } catch {
            statusText = "측정 시작 실패"
            sendError(error.localizedDescription)
        }
    }

    private func workoutConfiguration(for runType: String) -> HKWorkoutConfiguration {
        let configuration = HKWorkoutConfiguration()
        configuration.activityType = .running
        configuration.locationType = runType == "treadmill" ? .indoor : .outdoor
        return configuration
    }

    private func requestHealthKitAccess(completion: @escaping (Bool) -> Void) {
        let sampleTypes = healthSampleTypes()
        let readTypes = Set<HKObjectType>(sampleTypes.map { $0 as HKObjectType })
        healthStore.requestAuthorization(toShare: sampleTypes, read: readTypes) { success, _ in
            completion(success)
        }
    }

    private func healthSampleTypes() -> Set<HKSampleType> {
        var types: Set<HKSampleType> = [HKObjectType.workoutType()]
        [
            HKQuantityTypeIdentifier.heartRate,
            HKQuantityTypeIdentifier.activeEnergyBurned,
            HKQuantityTypeIdentifier.distanceWalkingRunning,
            HKQuantityTypeIdentifier.stepCount
        ].forEach { identifier in
            if let quantityType = HKObjectType.quantityType(forIdentifier: identifier) {
                types.insert(quantityType)
            }
        }
        return types
    }

    private func startMetricsTimer() {
        metricsTimer?.invalidate()
        metricsTimer = Timer.scheduledTimer(withTimeInterval: 1.0, repeats: true) { [weak self] _ in
            self?.sendMetrics(force: false)
        }
        if let metricsTimer = metricsTimer {
            RunLoop.main.add(metricsTimer, forMode: .common)
        }
    }

    private func updateStatistics(for quantityType: HKQuantityType) {
        guard let statistics = workoutBuilder?.statistics(for: quantityType) else { return }

        switch quantityType.identifier {
        case HKQuantityTypeIdentifier.heartRate.rawValue:
            let unit = HKUnit.count().unitDivided(by: .minute())
            if let quantity = statistics.mostRecentQuantity() {
                let value = quantity.doubleValue(for: unit)
                if value.isFinite && value > 0 {
                    let timestamp = Date().timeIntervalSince1970
                    latestHeartRate = value
                    if timestamp > lastHeartRateTimestamp {
                        lastHeartRateTimestamp = timestamp
                        heartRateSum += value
                        heartRateCount += 1
                    }
                    heartRateText = "\(Int(round(value))) bpm"
                }
            }
        case HKQuantityTypeIdentifier.distanceWalkingRunning.rawValue:
            if let quantity = statistics.sumQuantity() {
                distanceMeters = max(0, quantity.doubleValue(for: .meter()))
                distanceText = String(format: "%.2f km", distanceMeters / 1000.0)
            }
        case HKQuantityTypeIdentifier.activeEnergyBurned.rawValue:
            if let quantity = statistics.sumQuantity() {
                activeEnergyKcal = max(0, quantity.doubleValue(for: .kilocalorie()))
            }
        case HKQuantityTypeIdentifier.stepCount.rawValue:
            if let quantity = statistics.sumQuantity() {
                stepCount = max(0, quantity.doubleValue(for: .count()))
            }
        default:
            break
        }

        paceText = formattedPace()
    }

    private func sendMetrics(force: Bool) {
        guard workoutSession != nil,
              WCSession.isSupported(),
              WCSession.default.activationState == .activated else { return }

        let now = Date()
        if !force && now.timeIntervalSince(lastMetricsSentAt) < 0.75 {
            return
        }
        lastMetricsSentAt = now

        var payload: [String: Any] = [
            "type": "liveRunMetrics",
            "runId": runId ?? "",
            "timestamp": now.timeIntervalSince1970,
            "distance_m": distanceMeters,
            "active_energy_kcal": activeEnergyKcal,
            "calories": activeEnergyKcal,
            "step_count": stepCount,
            "elapsed_seconds": elapsedSeconds(),
            "status": currentStatus()
        ]
        if let latestHeartRate = latestHeartRate {
            payload["heart_rate"] = latestHeartRate
        }
        if heartRateCount > 0 {
            payload["avg_heart_rate"] = heartRateSum / heartRateCount
        }
        if stepCount > 0, elapsedSeconds() > 0 {
            payload["cadence"] = stepCount / max(elapsedSeconds() / 60.0, 0.1)
        }
        if let paceSeconds = paceSecondsPerKm() {
            payload["pace_seconds_per_km"] = paceSeconds
        }

        if WCSession.default.isReachable {
            WCSession.default.sendMessage(payload, replyHandler: nil, errorHandler: nil)
        } else {
            try? WCSession.default.updateApplicationContext(payload)
        }
    }

    private func sendError(_ message: String) {
        guard WCSession.isSupported(), WCSession.default.activationState == .activated else { return }
        let payload: [String: Any] = [
            "type": "liveRunError",
            "message": message,
            "timestamp": Date().timeIntervalSince1970
        ]
        if WCSession.default.isReachable {
            WCSession.default.sendMessage(payload, replyHandler: nil, errorHandler: nil)
        } else {
            try? WCSession.default.updateApplicationContext(payload)
        }
    }

    private func elapsedSeconds() -> TimeInterval {
        guard let startedAt = startedAt else { return 0 }
        return max(0, Date().timeIntervalSince(startedAt))
    }

    private func paceSecondsPerKm() -> Double? {
        let distanceKm = distanceMeters / 1000.0
        guard distanceKm > 0.003 else { return nil }
        let pace = elapsedSeconds() / distanceKm
        return pace.isFinite && pace > 0 ? pace : nil
    }

    private func formattedPace() -> String {
        guard let pace = paceSecondsPerKm() else { return "-- /km" }
        let total = Int(round(pace))
        return String(format: "%d'%02d\" /km", total / 60, total % 60)
    }

    private func currentStatus() -> String {
        if canResume {
            return "paused"
        }
        return workoutSession == nil ? "stopped" : "running"
    }

    private func cleanupWorkout() {
        metricsTimer?.invalidate()
        metricsTimer = nil
        workoutSession = nil
        workoutBuilder = nil
        startedAt = nil
        runId = nil
        latestHeartRate = nil
        heartRateSum = 0
        heartRateCount = 0
        lastHeartRateTimestamp = 0
        distanceMeters = 0
        activeEnergyKcal = 0
        stepCount = 0
        heartRateText = "-- bpm"
        distanceText = "0.00 km"
        paceText = "-- /km"
        statusText = "iPhone에서 러닝을 시작해줘"
        canPause = false
        canResume = false
        canStop = false
    }

    private func activateConnectivity() {
        guard WCSession.isSupported() else { return }
        WCSession.default.delegate = self
        WCSession.default.activate()
    }

    private func handleCompanionMessage(_ message: [String: Any]) {
        guard let type = message["type"] as? String, type == "liveRunCommand" else { return }

        let command = (message["command"] as? String) ?? ""
        let receivedRunId = message["runId"] as? String
        let runType = (message["runType"] as? String) ?? "jogging"

        DispatchQueue.main.async {
            switch command {
            case "start":
                self.start(runId: receivedRunId, runType: runType)
            case "pause":
                self.pause()
            case "resume":
                self.resume()
            case "stop":
                self.stop()
            default:
                break
            }
        }
    }
}

extension RunMateWatchWorkoutManager: HKWorkoutSessionDelegate {
    func workoutSession(_ workoutSession: HKWorkoutSession, didChangeTo toState: HKWorkoutSessionState, from fromState: HKWorkoutSessionState, date: Date) {
        DispatchQueue.main.async {
            switch toState {
            case .running:
                self.statusText = "러닝 중"
                self.canPause = true
                self.canResume = false
                self.canStop = true
            case .paused:
                self.statusText = "일시정지"
                self.canPause = false
                self.canResume = true
                self.canStop = true
            case .ended:
                self.statusText = "러닝 완료"
                self.canPause = false
                self.canResume = false
                self.canStop = false
            default:
                break
            }
            self.sendMetrics(force: true)
        }
    }

    func workoutSession(_ workoutSession: HKWorkoutSession, didFailWithError error: Error) {
        DispatchQueue.main.async {
            self.statusText = "측정 오류"
            self.sendError(error.localizedDescription)
        }
    }
}

extension RunMateWatchWorkoutManager: HKLiveWorkoutBuilderDelegate {
    func workoutBuilder(_ workoutBuilder: HKLiveWorkoutBuilder, didCollectDataOf collectedTypes: Set<HKSampleType>) {
        DispatchQueue.main.async {
            for sampleType in collectedTypes {
                guard let quantityType = sampleType as? HKQuantityType else { continue }
                self.updateStatistics(for: quantityType)
            }
            self.sendMetrics(force: false)
        }
    }

    func workoutBuilderDidCollectEvent(_ workoutBuilder: HKLiveWorkoutBuilder) {
        DispatchQueue.main.async {
            self.sendMetrics(force: true)
        }
    }
}

extension RunMateWatchWorkoutManager: WCSessionDelegate {
    func session(_ session: WCSession, activationDidCompleteWith activationState: WCSessionActivationState, error: Error?) {
        if let error = error {
            DispatchQueue.main.async {
                self.statusText = error.localizedDescription
            }
            return
        }
        sendMetrics(force: true)
    }

    func session(_ session: WCSession, didReceiveMessage message: [String: Any]) {
        handleCompanionMessage(message)
    }

    func session(_ session: WCSession, didReceiveApplicationContext applicationContext: [String: Any]) {
        handleCompanionMessage(applicationContext)
    }

    func session(_ session: WCSession, didReceiveUserInfo userInfo: [String: Any]) {
        handleCompanionMessage(userInfo)
    }
}
