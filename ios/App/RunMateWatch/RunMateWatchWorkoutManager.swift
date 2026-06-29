import Foundation
import CoreLocation
import HealthKit
import SwiftUI
import WatchConnectivity

final class RunMateWatchWorkoutManager: NSObject, ObservableObject, CLLocationManagerDelegate {
    static let shared = RunMateWatchWorkoutManager()

    @Published var statusText = "워치에서 러닝 시작 가능"
    @Published var connectionText = "워치 단독 저장 가능"
    @Published var heartRateText = "-- bpm"
    @Published var distanceText = "0.00 km"
    @Published var paceText = "-- /km"
    @Published var elapsedText = "00:00"
    @Published var cadenceText = "-- spm"
    @Published var caloriesText = "0 kcal"
    @Published var canPause = false
    @Published var canResume = false
    @Published var canStop = false
    @Published var isWorkoutActive = false

    private let healthStore = HKHealthStore()
    private var workoutSession: HKWorkoutSession?
    private var workoutBuilder: HKLiveWorkoutBuilder?
    private var startedAt: Date?
    private var runId: String?
    private var metricsTimer: Timer?
    private var lastMetricsSentAt: Date = .distantPast
    private var lastHeartRateTimestamp: TimeInterval = 0
    private var workoutState: HKWorkoutSessionState = .notStarted
    private var isStoppingWorkout = false
    private var isStandaloneRun = false
    private var currentRunType = "jogging"
    private var pausedAt: Date?
    private var pausedDuration: TimeInterval = 0
    private var locationManager: CLLocationManager?

    private var latestHeartRate: Double?
    private var heartRateSum: Double = 0
    private var heartRateCount: Double = 0
    private var distanceMeters: Double = 0
    private var routeDistanceMeters: Double = 0
    private var elevationGainMeters: Double = 0
    private var activeEnergyKcal: Double = 0
    private var stepCount: Double = 0
    private var routeLocations: [CLLocation] = []
    private var lastRouteLocation: CLLocation?
    private var lastAltitude: Double?

    override private init() {
        super.init()
        activateConnectivity()
    }

    func start(runId: String?, runType: String, configuration: HKWorkoutConfiguration? = nil, standalone: Bool = false) {
        if workoutSession != nil {
            if let runId = runId, !runId.isEmpty {
                self.runId = runId
                self.isStandaloneRun = false
            }
            sendMetrics(force: true)
            return
        }

        guard HKHealthStore.isHealthDataAvailable() else {
            statusText = "건강 데이터 사용 불가"
            sendError("Apple Watch에서 건강 데이터를 사용할 수 없어.")
            return
        }

        statusText = "건강 권한 확인 중"
        requestHealthKitAccess { [weak self] success in
            DispatchQueue.main.async {
                guard let self = self else { return }
                guard success else {
                    self.statusText = "건강 접근 권한이 필요해"
                    self.sendError("Apple Watch 건강 접근 권한을 허용해줘.")
                    return
                }
                self.startWorkoutSession(runId: runId, runType: runType, configuration: configuration, standalone: standalone)
            }
        }
    }

    func startFromWatch() {
        start(runId: "watch-\(UUID().uuidString)", runType: "jogging", standalone: true)
    }

    func pause() {
        guard let session = workoutSession else {
            cleanupWorkout()
            return
        }

        guard workoutState == .running else {
            syncWorkoutControls(for: workoutState)
            sendMetrics(force: true)
            return
        }

        workoutState = .paused
        pausedAt = Date()
        syncWorkoutControls(for: .paused)
        session.pause()
        sendMetrics(force: true)
    }

    func resume() {
        guard let session = workoutSession else {
            cleanupWorkout()
            return
        }

        guard workoutState == .paused else {
            syncWorkoutControls(for: workoutState)
            sendMetrics(force: true)
            return
        }

        if let pausedAt = pausedAt {
            pausedDuration += max(0, Date().timeIntervalSince(pausedAt))
        }
        pausedAt = nil
        workoutState = .running
        syncWorkoutControls(for: .running)
        session.resume()
        sendMetrics(force: true)
    }

    func stop() {
        guard let builder = workoutBuilder else {
            cleanupWorkout()
            return
        }
        guard !isStoppingWorkout else {
            sendMetrics(force: true)
            return
        }

        let endedAt = Date()
        if workoutState == .paused, let pausedAt = pausedAt {
            pausedDuration += max(0, endedAt.timeIntervalSince(pausedAt))
        }
        pausedAt = nil
        isStoppingWorkout = true
        workoutState = .ended
        metricsTimer?.invalidate()
        metricsTimer = nil
        if workoutSession?.state != .ended {
            workoutSession?.end()
        }
        syncWorkoutControls(for: .ended)
        sendMetrics(force: true)
        stopRouteTracking()

        builder.endCollection(withEnd: endedAt) { [weak self] _, _ in
            builder.finishWorkout { workout, _ in
                DispatchQueue.main.async {
                    self?.finishStoppedWorkout(workout: workout, endedAt: endedAt)
                }
            }
        }
    }

    private func startWorkoutSession(runId: String?, runType: String, configuration: HKWorkoutConfiguration? = nil, standalone: Bool = false) {
        let configuration = configuration ?? workoutConfiguration(for: runType)
        let normalizedRunId = (runId?.isEmpty == false) ? runId : "watch-\(UUID().uuidString)"

        do {
            let session = try HKWorkoutSession(healthStore: healthStore, configuration: configuration)
            let builder = session.associatedWorkoutBuilder()
            builder.dataSource = HKLiveWorkoutDataSource(healthStore: healthStore, workoutConfiguration: configuration)
            session.delegate = self
            builder.delegate = self

            self.workoutSession = session
            self.workoutBuilder = builder
            self.startedAt = Date()
            self.runId = normalizedRunId
            self.currentRunType = runType
            self.isStandaloneRun = standalone || runId?.isEmpty != false
            self.workoutState = .notStarted
            self.isStoppingWorkout = false
            self.pausedAt = nil
            self.pausedDuration = 0
            self.latestHeartRate = nil
            self.heartRateSum = 0
            self.heartRateCount = 0
            self.lastHeartRateTimestamp = 0
            self.distanceMeters = 0
            self.routeDistanceMeters = 0
            self.elevationGainMeters = 0
            self.activeEnergyKcal = 0
            self.stepCount = 0
            self.routeLocations = []
            self.lastRouteLocation = nil
            self.lastAltitude = nil
            self.elapsedText = "00:00"
            self.cadenceText = "-- spm"
            self.caloriesText = "0 kcal"
            self.syncWorkoutControls(for: .running)
            self.isWorkoutActive = true
            self.startRouteTrackingIfNeeded(for: configuration)

            let startDate = startedAt ?? Date()
            self.workoutState = .running
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
        metricsTimer = Timer.scheduledTimer(withTimeInterval: 0.5, repeats: true) { [weak self] _ in
            self?.updateDisplayMetrics()
            self?.sendMetrics(force: false)
        }
        if let metricsTimer = metricsTimer {
            RunLoop.main.add(metricsTimer, forMode: .common)
        }
    }

    private func updateStatistics(for quantityType: HKQuantityType) {
        guard let statistics = workoutBuilder?.statistics(for: quantityType) else { return }
        guard workoutState == .running else {
            updateDisplayMetrics()
            return
        }

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
                distanceText = String(format: "%.2f km", max(distanceMeters, routeDistanceMeters) / 1000.0)
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

        updateDisplayMetrics()
        paceText = formattedPace()
    }

    private func updateDisplayMetrics() {
        elapsedText = formattedElapsed()
        cadenceText = formattedCadence()
        caloriesText = "\(Int(round(activeEnergyKcal))) kcal"
    }

    private func finishStoppedWorkout(workout: HKWorkout?, endedAt: Date) {
        if isStandaloneRun {
            sendStandaloneRunCompleted(workout: workout, endedAt: endedAt)
        }
        cleanupWorkout()
    }

    private func startRouteTrackingIfNeeded(for configuration: HKWorkoutConfiguration) {
        guard configuration.locationType != .indoor else { return }

        let manager = currentLocationManager()
        manager.desiredAccuracy = kCLLocationAccuracyBestForNavigation
        manager.distanceFilter = kCLDistanceFilterNone
        manager.activityType = .fitness

        switch manager.authorizationStatus {
        case .authorizedAlways, .authorizedWhenInUse:
            manager.startUpdatingLocation()
            manager.requestLocation()
        case .notDetermined:
            manager.requestWhenInUseAuthorization()
        case .denied, .restricted:
            break
        @unknown default:
            break
        }
    }

    private func currentLocationManager() -> CLLocationManager {
        if let locationManager = locationManager {
            return locationManager
        }

        let manager = CLLocationManager()
        manager.delegate = self
        locationManager = manager
        return manager
    }

    private func stopRouteTracking() {
        locationManager?.stopUpdatingLocation()
    }

    private func sendStandaloneRunCompleted(workout: HKWorkout?, endedAt: Date) {
        guard WCSession.isSupported() else { return }

        let payload = standaloneRunPayload(workout: workout, endedAt: endedAt)
        let session = WCSession.default
        if session.activationState != .activated {
            session.activate()
        }
        session.transferUserInfo(payload)
        if session.isReachable {
            session.sendMessage(payload, replyHandler: nil, errorHandler: nil)
        }
        connectionText = "iPhone 열면 기록 동기화"
    }

    private func standaloneRunPayload(workout: HKWorkout?, endedAt: Date) -> [String: Any] {
        let startDate = startedAt ?? workout?.startDate ?? Date()
        let measuredDurationSeconds = elapsedSeconds(at: endedAt)
        let durationSeconds = measuredDurationSeconds > 0 ? measuredDurationSeconds : max(0, workout?.duration ?? endedAt.timeIntervalSince(startDate))
        let workoutDistanceMeters = workout?.totalDistance?.doubleValue(for: .meter()) ?? 0
        let distance = max(distanceMeters, routeDistanceMeters, workoutDistanceMeters)
        let distanceKm = distance / 1000.0
        let workoutCalories = workout?.totalEnergyBurned?.doubleValue(for: .kilocalorie()) ?? 0
        let estimatedCalories = estimatedCalories(distanceKm: distanceKm, elapsedSeconds: durationSeconds, weightKg: 60)
        let calories = max(activeEnergyKcal, workoutCalories, estimatedCalories)
        let avgHeartRate = heartRateCount > 0 ? heartRateSum / heartRateCount : latestHeartRate
        let cadence = stepCount > 0 && durationSeconds > 0 ? stepCount / max(durationSeconds / 60.0, 0.1) : nil
        let pace = distanceKm > 0.003 && durationSeconds > 0 ? durationSeconds / distanceKm : nil
        let routePoints = sampledRouteLocations(routeLocations).map { location in
            [
                "lat": rounded(location.coordinate.latitude, places: 6),
                "lng": rounded(location.coordinate.longitude, places: 6)
            ]
        }

        var payload: [String: Any] = [
            "type": "watchStandaloneRunEnded",
            "id": runId ?? workout?.uuid.uuidString ?? "watch-\(UUID().uuidString)",
            "source": "apple_watch_standalone",
            "run_type": currentRunType,
            "date": dateKey(startDate),
            "started_at": isoString(startDate),
            "ended_at": isoString(endedAt),
            "distance_km": rounded(distanceKm, places: 3),
            "duration": durationText(durationSeconds),
            "duration_seconds": Int(round(durationSeconds)),
            "calories": Int(round(calories)),
            "step_count": Int(round(stepCount)),
            "elevation_gain_m": Int(round(elevationGainMeters)),
            "metrics_source": "apple_watch_standalone",
            "heart_rate_available": avgHeartRate != nil,
            "active": false,
            "status": "stopped"
        ]

        if let latestHeartRate = latestHeartRate {
            payload["heart_rate"] = Int(round(latestHeartRate))
        }
        if let avgHeartRate = avgHeartRate {
            payload["avg_heart_rate"] = Int(round(avgHeartRate))
        }
        if let cadence = cadence, cadence.isFinite {
            payload["cadence"] = Int(round(cadence))
        }
        if let pace = pace, pace.isFinite {
            payload["avg_pace"] = formattedPace(secondsPerKm: pace)
            payload["pace_seconds_per_km"] = pace
        }
        if let first = routePoints.first {
            payload["start_location"] = first
        }
        if let last = routePoints.last {
            payload["end_location"] = last
        }
        if !routePoints.isEmpty {
            payload["route_points"] = routePoints
        }

        return payload
    }

    private func sampledRouteLocations(_ locations: [CLLocation], limit: Int = 80) -> [CLLocation] {
        guard locations.count > limit else { return locations }
        let step = max(1, Int(ceil(Double(locations.count) / Double(limit))))
        var sampled = locations.enumerated().compactMap { index, location in
            index % step == 0 ? location : nil
        }
        if let last = locations.last,
           sampled.last?.timestamp != last.timestamp {
            sampled.append(last)
        }
        return sampled
    }

    private func sendMetrics(force: Bool) {
        guard workoutSession != nil,
              WCSession.isSupported(),
              WCSession.default.activationState == .activated else { return }

        let now = Date()
        if !force && now.timeIntervalSince(lastMetricsSentAt) < 0.35 {
            return
        }
        lastMetricsSentAt = now

        var payload: [String: Any] = [
            "type": "liveRunMetrics",
            "runId": runId ?? "",
            "timestamp": now.timeIntervalSince1970,
            "distance_m": max(distanceMeters, routeDistanceMeters),
            "active_energy_kcal": activeEnergyKcal,
            "calories": activeEnergyKcal,
            "step_count": stepCount,
            "elevation_gain_m": elevationGainMeters,
            "elapsed_seconds": elapsedSeconds(),
            "status": currentStatus()
        ]
        if isStandaloneRun {
            payload["source"] = "apple_watch_standalone"
        }
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

    private func elapsedSeconds(at date: Date) -> TimeInterval {
        guard let startedAt = startedAt else { return 0 }
        let currentPause = workoutState == .paused ? max(0, date.timeIntervalSince(pausedAt ?? date)) : 0
        return max(0, date.timeIntervalSince(startedAt) - pausedDuration - currentPause)
    }

    private func elapsedSeconds() -> TimeInterval {
        elapsedSeconds(at: Date())
    }

    private func paceSecondsPerKm() -> Double? {
        let distanceKm = max(distanceMeters, routeDistanceMeters) / 1000.0
        guard distanceKm > 0.003 else { return nil }
        let pace = elapsedSeconds() / distanceKm
        return pace.isFinite && pace > 0 ? pace : nil
    }

    private func formattedPace() -> String {
        guard let pace = paceSecondsPerKm() else { return "-- /km" }
        return "\(formattedPace(secondsPerKm: pace)) /km"
    }

    private func formattedCadence() -> String {
        guard stepCount > 0, elapsedSeconds() > 0 else { return "-- spm" }
        let cadence = stepCount / max(elapsedSeconds() / 60.0, 0.1)
        guard cadence.isFinite && cadence > 0 else { return "-- spm" }
        return "\(Int(round(cadence))) spm"
    }

    private func estimatedCalories(distanceKm: Double, elapsedSeconds: TimeInterval, weightKg: Double) -> Double {
        if distanceKm > 0.05 {
            return max(0, distanceKm * weightKg * 1.036)
        }
        let minutes = max(0, elapsedSeconds / 60.0)
        return max(0, 8.3 * 3.5 * weightKg / 200.0 * minutes)
    }

    private func formattedPace(secondsPerKm: Double) -> String {
        guard secondsPerKm.isFinite && secondsPerKm > 0 else { return "-" }
        let total = Int(round(secondsPerKm))
        return String(format: "%d'%02d\"", total / 60, total % 60)
    }

    private func durationText(_ seconds: TimeInterval) -> String {
        let total = Int(round(max(0, seconds)))
        return String(format: "%02d:%02d:%02d", total / 3600, (total % 3600) / 60, total % 60)
    }

    private func dateKey(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.timeZone = TimeZone.current
        formatter.dateFormat = "yyyy-MM-dd"
        return formatter.string(from: date)
    }

    private func isoString(_ date: Date) -> String {
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        return formatter.string(from: date)
    }

    private func rounded(_ value: Double, places: Int) -> Double {
        let power = pow(10.0, Double(places))
        return (value * power).rounded() / power
    }

    private func formattedElapsed() -> String {
        let total = Int(round(elapsedSeconds()))
        if total >= 3600 {
            return String(format: "%d:%02d:%02d", total / 3600, (total % 3600) / 60, total % 60)
        }
        return String(format: "%02d:%02d", total / 60, total % 60)
    }

    private func currentStatus() -> String {
        switch workoutState {
        case .paused:
            return "paused"
        case .running:
            return "running"
        case .ended:
            return "stopped"
        default:
            return workoutSession == nil ? "stopped" : "running"
        }
    }

    private func syncWorkoutControls(for state: HKWorkoutSessionState) {
        workoutState = state
        switch state {
        case .running:
            statusText = isStandaloneRun ? "워치 단독 러닝 중" : "러닝 중"
            canPause = true
            canResume = false
            canStop = false
        case .paused:
            statusText = "일시정지"
            canPause = false
            canResume = true
            canStop = true
        case .ended:
            statusText = "러닝 완료"
            canPause = false
            canResume = false
            canStop = false
        default:
            canPause = false
            canResume = false
            canStop = workoutSession != nil
        }
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
        routeDistanceMeters = 0
        elevationGainMeters = 0
        activeEnergyKcal = 0
        stepCount = 0
        routeLocations = []
        lastRouteLocation = nil
        lastAltitude = nil
        workoutState = .notStarted
        isStoppingWorkout = false
        pausedAt = nil
        pausedDuration = 0
        isStandaloneRun = false
        currentRunType = "jogging"
        heartRateText = "-- bpm"
        distanceText = "0.00 km"
        paceText = "-- /km"
        elapsedText = "00:00"
        cadenceText = "-- spm"
        caloriesText = "0 kcal"
        statusText = "워치에서 러닝 시작 가능"
        canPause = false
        canResume = false
        canStop = false
        isWorkoutActive = false
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
                self.start(runId: receivedRunId, runType: runType, standalone: false)
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

extension RunMateWatchWorkoutManager {
    func locationManagerDidChangeAuthorization(_ manager: CLLocationManager) {
        guard workoutSession != nil,
              workoutState == .running,
              manager.authorizationStatus == .authorizedAlways || manager.authorizationStatus == .authorizedWhenInUse else {
            return
        }
        manager.startUpdatingLocation()
        manager.requestLocation()
    }

    func locationManager(_ manager: CLLocationManager, didUpdateLocations locations: [CLLocation]) {
        guard workoutSession != nil, workoutState == .running else { return }

        for location in locations {
            guard location.horizontalAccuracy >= 0,
                  location.horizontalAccuracy <= 60,
                  location.coordinate.latitude.isFinite,
                  location.coordinate.longitude.isFinite else {
                continue
            }

            if let startedAt = startedAt, location.timestamp < startedAt {
                continue
            }

            if let lastRouteLocation = lastRouteLocation {
                let delta = location.distance(from: lastRouteLocation)
                let timeDelta = location.timestamp.timeIntervalSince(lastRouteLocation.timestamp)
                if delta >= 1.5 && delta <= 220 && timeDelta >= 0 {
                    routeDistanceMeters += delta
                }
            }

            routeLocations.append(location)
            lastRouteLocation = location
            if routeDistanceMeters > distanceMeters {
                distanceText = String(format: "%.2f km", routeDistanceMeters / 1000.0)
                paceText = formattedPace()
            }

            if location.verticalAccuracy >= 0 && location.verticalAccuracy <= 35 {
                if let lastAltitude = lastAltitude {
                    let altitudeDelta = location.altitude - lastAltitude
                    if altitudeDelta > 1.5 {
                        elevationGainMeters += altitudeDelta
                    }
                }
                lastAltitude = location.altitude
            }
        }
    }

    func locationManager(_ manager: CLLocationManager, didFailWithError error: Error) {
        guard isStandaloneRun else { return }
        connectionText = "GPS 대기 중"
    }
}

extension RunMateWatchWorkoutManager: HKWorkoutSessionDelegate {
    func workoutSession(_ workoutSession: HKWorkoutSession, didChangeTo toState: HKWorkoutSessionState, from fromState: HKWorkoutSessionState, date: Date) {
        DispatchQueue.main.async {
            self.syncWorkoutControls(for: toState)
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
                self.connectionText = "iPhone 연결 오류"
            }
            return
        }
        DispatchQueue.main.async {
            self.connectionText = activationState == .activated ? "iPhone 연결됨" : "iPhone 연결 대기"
            self.sendMetrics(force: true)
        }
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
