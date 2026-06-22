import Capacitor
import CoreLocation
import CoreMotion
import Foundation
import HealthKit
import WatchConnectivity

@objc(RunningMateHealthKitPlugin)
class RunningMateHealthKitPlugin: CAPPlugin, CAPBridgedPlugin, CLLocationManagerDelegate, WCSessionDelegate {
    let identifier = "RunningMateHealthKitPlugin"
    let jsName = "RunningMateHealthKit"
    let pluginMethods: [CAPPluginMethod] = [
        CAPPluginMethod(name: "isAvailable", returnType: CAPPluginReturnPromise),
        CAPPluginMethod(name: "requestAuthorization", returnType: CAPPluginReturnPromise),
        CAPPluginMethod(name: "getRunningWorkouts", returnType: CAPPluginReturnPromise),
        CAPPluginMethod(name: "startLiveRun", returnType: CAPPluginReturnPromise),
        CAPPluginMethod(name: "pauseLiveRun", returnType: CAPPluginReturnPromise),
        CAPPluginMethod(name: "resumeLiveRun", returnType: CAPPluginReturnPromise),
        CAPPluginMethod(name: "stopLiveRun", returnType: CAPPluginReturnPromise),
        CAPPluginMethod(name: "getLiveRunSnapshot", returnType: CAPPluginReturnPromise)
    ]

    private let healthStore = HKHealthStore()
    private let pedometer = CMPedometer()
    private var locationManager: CLLocationManager?
    private var liveRunSession: LiveRunSession?
    private var pendingLocationAuthorization: ((Bool) -> Void)?
    private var liveRunTimer: Timer?
    private var liveHeartRateTimer: Timer?
    private var watchConnectivityConfigured = false

    override func load() {
        super.load()
        configureWatchConnectivity()
    }

    @objc func isAvailable(_ call: CAPPluginCall) {
        call.resolve(["available": HKHealthStore.isHealthDataAvailable()])
    }

    @objc func requestAuthorization(_ call: CAPPluginCall) {
        requestHealthKitAccess { success, error in
            DispatchQueue.main.async {
                if let error = error {
                    call.reject("설정 > 건강 접근 권한을 허용해줘", "permission_denied", error)
                    return
                }

                call.resolve([
                    "available": HKHealthStore.isHealthDataAvailable(),
                    "granted": success
                ])
            }
        }
    }

    @objc func getRunningWorkouts(_ call: CAPPluginCall) {
        guard HKHealthStore.isHealthDataAvailable() else {
            call.reject("HealthKit is not available on this device.", "unavailable")
            return
        }

        requestHealthKitAccess { [weak self] _, error in
            guard let self = self else { return }
            if let error = error {
                DispatchQueue.main.async {
                    call.reject("설정 > 건강 접근 권한을 허용해줘", "permission_denied", error)
                }
                return
            }

            self.queryRunningWorkouts(days: call.getInt("days", 7), limit: call.getInt("limit", 20)) { result in
                DispatchQueue.main.async {
                    switch result {
                    case .success(let workouts):
                        RunningMateWidgetStore.syncRecentRuns(from: workouts)
                        call.resolve(["workouts": workouts])
                    case .failure(let error):
                        call.reject("애플워치 기록을 불러오지 못했어.", "healthkit_query_failed", error)
                    }
                }
            }
        }
    }

    @objc func startLiveRun(_ call: CAPPluginCall) {
        if let session = liveRunSession, session.status != .stopped {
            call.resolve(liveRunPayload(for: session))
            return
        }

        requestLocationAccess { [weak self] granted in
            guard let self = self else { return }

            DispatchQueue.main.async {
                guard granted else {
                    call.reject("러닝 거리 측정을 위해 위치 권한을 허용해줘.", "location_permission_denied")
                    return
                }

                let runType = call.getString("runType", "jogging")
                let weightKg = call.getDouble("weightKg") ?? 60.0
                let session = LiveRunSession(runType: runType, weightKg: max(30.0, min(weightKg, 220.0)))
                self.liveRunSession = session
                self.requestHealthKitAccess { [weak self, weak session] _, _ in
                    DispatchQueue.main.async {
                        guard let self = self, let session = session, self.liveRunSession === session else { return }
                        self.queryLiveHeartRateSamples(includeRecentFallback: true)
                    }
                }
                self.configureWatchConnectivity()
                self.startWatchWorkoutApp(runType: runType, runId: session.id, weightKg: session.weightKg, startedAt: session.startDate)
                self.sendWatchRunCommand("start", extra: [
                    "runType": runType,
                    "runId": session.id,
                    "weightKg": session.weightKg,
                    "startedAt": self.isoString(session.startDate)
                ])
                self.configureLocationTracking()
                self.startLocationUpdates()
                self.startPedometerUpdates(from: session.activeSegmentStart)
                self.startLiveRunTimers()
                let payload = self.liveRunPayload(for: session, reason: "started")
                self.startLiveActivity(with: payload)
                self.notifyListeners("liveRunUpdate", data: payload)
                call.resolve(payload)
            }
        }
    }

    @objc func pauseLiveRun(_ call: CAPPluginCall) {
        guard let session = liveRunSession, session.status == .running else {
            call.reject("진행 중인 러닝이 없어.", "no_active_run")
            return
        }

        session.pause()
        sendWatchRunCommand("pause", extra: ["runId": session.id])
        stopLocationUpdates()
        pedometer.stopUpdates()
        emitLiveRunUpdate(reason: "paused")
        call.resolve(liveRunPayload(for: session))
    }

    @objc func resumeLiveRun(_ call: CAPPluginCall) {
        guard let session = liveRunSession, session.status == .paused else {
            call.reject("일시정지된 러닝이 없어.", "no_paused_run")
            return
        }

        requestLocationAccess { [weak self] granted in
            guard let self = self else { return }

            DispatchQueue.main.async {
                guard granted else {
                    call.reject("러닝 거리 측정을 위해 위치 권한을 허용해줘.", "location_permission_denied")
                    return
                }

                session.resume()
                self.sendWatchRunCommand("resume", extra: ["runId": session.id])
                self.configureLocationTracking()
                self.startLocationUpdates()
                self.startPedometerUpdates(from: session.activeSegmentStart)
                self.startLiveRunTimers()
                self.emitLiveRunUpdate(reason: "resumed")
                call.resolve(self.liveRunPayload(for: session))
            }
        }
    }

    @objc func stopLiveRun(_ call: CAPPluginCall) {
        guard let session = liveRunSession else {
            call.reject("종료할 러닝이 없어.", "no_active_run")
            return
        }

        session.stop()
        sendWatchRunCommand("stop", extra: ["runId": session.id])
        stopLiveRunSensors()
        let payload = liveRunPayload(for: session, ended: true)
        RunningMateWidgetStore.recordCompletedRun(
            id: session.id,
            startDate: session.startDate,
            endDate: session.endDate ?? Date(),
            distanceKm: numericValue(payload["distance_km"]) ?? 0,
            durationSeconds: session.elapsedSeconds
        )
        endLiveActivity(with: payload)
        notifyListeners("liveRunEnded", data: payload)
        liveRunSession = nil
        call.resolve(payload)
    }

    @objc func getLiveRunSnapshot(_ call: CAPPluginCall) {
        guard let session = liveRunSession else {
            call.resolve(["active": false])
            return
        }

        call.resolve(liveRunPayload(for: session))
    }

    private func requestLocationAccess(completion: @escaping (Bool) -> Void) {
        DispatchQueue.main.async {
            let manager = self.liveLocationManager()
            let status = manager.authorizationStatus
            switch status {
            case .authorizedAlways, .authorizedWhenInUse:
                completion(true)
            case .notDetermined:
                self.pendingLocationAuthorization = completion
                manager.requestWhenInUseAuthorization()
            case .denied, .restricted:
                completion(false)
            @unknown default:
                completion(false)
            }
        }
    }

    private func liveLocationManager() -> CLLocationManager {
        if let locationManager = locationManager {
            return locationManager
        }

        let manager = CLLocationManager()
        manager.delegate = self
        locationManager = manager
        return manager
    }

    private func configureLocationTracking() {
        let manager = liveLocationManager()
        manager.desiredAccuracy = kCLLocationAccuracyBestForNavigation
        manager.distanceFilter = kCLDistanceFilterNone
        manager.activityType = .fitness
        manager.pausesLocationUpdatesAutomatically = false
        if Bundle.main.object(forInfoDictionaryKey: "UIBackgroundModes") != nil {
            manager.allowsBackgroundLocationUpdates = true
            manager.showsBackgroundLocationIndicator = true
        }
    }

    private func startLocationUpdates() {
        let manager = liveLocationManager()
        manager.startUpdatingLocation()
        manager.requestLocation()
    }

    private func stopLocationUpdates() {
        locationManager?.stopUpdatingLocation()
    }

    private func startPedometerUpdates(from startDate: Date) {
        guard CMPedometer.isStepCountingAvailable(), let session = liveRunSession else {
            return
        }

        pedometer.stopUpdates()
        pedometer.startUpdates(from: startDate) { [weak self, weak session] data, _ in
            guard let self = self, let session = session, let data = data else { return }

            DispatchQueue.main.async {
                guard self.liveRunSession === session, session.status == .running else { return }

                session.updateStepMetrics(
                    segmentSteps: data.numberOfSteps.doubleValue,
                    currentCadenceStepsPerSecond: data.currentCadence?.doubleValue,
                    at: Date()
                )
                self.emitLiveRunUpdate(reason: "pedometer")
            }
        }
    }

    private func startLiveRunTimers() {
        guard liveRunTimer == nil else { return }

        liveRunTimer = Timer.scheduledTimer(withTimeInterval: 1.0, repeats: true) { [weak self] _ in
            self?.queryLivePedometerSnapshot()
            self?.emitLiveRunUpdate(reason: "tick")
        }
        if let liveRunTimer = liveRunTimer {
            RunLoop.main.add(liveRunTimer, forMode: .common)
        }

        liveHeartRateTimer?.invalidate()
        liveHeartRateTimer = Timer.scheduledTimer(withTimeInterval: 2.0, repeats: true) { [weak self] _ in
            self?.queryLiveHeartRateSamples(includeRecentFallback: true)
        }
        if let liveHeartRateTimer = liveHeartRateTimer {
            RunLoop.main.add(liveHeartRateTimer, forMode: .common)
        }
        queryLiveHeartRateSamples(includeRecentFallback: true)
    }

    private func stopLiveRunSensors() {
        stopLocationUpdates()
        pedometer.stopUpdates()
        liveRunTimer?.invalidate()
        liveRunTimer = nil
        liveHeartRateTimer?.invalidate()
        liveHeartRateTimer = nil
    }

    private func queryLivePedometerSnapshot() {
        guard CMPedometer.isStepCountingAvailable(),
              let session = liveRunSession,
              session.status == .running else {
            return
        }

        pedometer.queryPedometerData(from: session.activeSegmentStart, to: Date()) { [weak self, weak session] data, _ in
            guard let self = self, let session = session, let data = data else { return }

            DispatchQueue.main.async {
                guard self.liveRunSession === session, session.status == .running else { return }

                session.updateStepMetrics(
                    segmentSteps: data.numberOfSteps.doubleValue,
                    currentCadenceStepsPerSecond: data.currentCadence?.doubleValue,
                    at: Date()
                )
                self.emitLiveRunUpdate(reason: "pedometer_snapshot")
            }
        }
    }

    private func emitLiveRunUpdate(reason: String) {
        guard let session = liveRunSession else { return }
        let payload = liveRunPayload(for: session, reason: reason)
        updateLiveActivity(with: payload, force: reason != "tick")
        notifyListeners("liveRunUpdate", data: payload)
    }

    private func startLiveActivity(with payload: [String: Any]) {
        if #available(iOS 16.1, *) {
            RunningMateLiveActivityController.shared.start(with: payload)
        }
    }

    private func updateLiveActivity(with payload: [String: Any], force: Bool = false) {
        if #available(iOS 16.1, *) {
            RunningMateLiveActivityController.shared.update(with: payload, force: force)
        }
    }

    private func endLiveActivity(with payload: [String: Any]) {
        if #available(iOS 16.1, *) {
            RunningMateLiveActivityController.shared.end(with: payload)
        }
    }

    private func liveRunPayload(for session: LiveRunSession, reason: String = "snapshot", ended: Bool = false) -> [String: Any] {
        let elapsedSeconds = session.elapsedSeconds
        let distanceMeters = max(session.distanceMeters, session.watchDistanceMeters ?? 0)
        let distanceKm = distanceMeters / 1000.0
        let steps = max(session.steps, session.watchSteps ?? 0)
        let cadence = session.cadenceStepsPerMinute ?? (elapsedSeconds > 0 ? steps / (elapsedSeconds / 60.0) : nil)
        let calories = session.watchCalories ?? estimatedCalories(distanceKm: distanceKm, elapsedSeconds: elapsedSeconds, weightKg: session.weightKg)
        let averagePaceSecondsPerKm = distanceMeters >= 1.0 && elapsedSeconds > 0 ? elapsedSeconds / max(distanceKm, 0.001) : nil
        let currentPaceSecondsPerKm = session.instantPaceSecondsPerKm ?? averagePaceSecondsPerKm
        let watchConnected = session.hasRecentWatchMetrics || watchSessionIsReachable()
        var payload: [String: Any] = [
            "active": !ended && session.status != .stopped,
            "id": session.id,
            "status": ended ? "stopped" : session.status.rawValue,
            "reason": reason,
            "run_type": session.runType,
            "started_at": isoString(session.startDate),
            "distance_km": rounded(distanceKm, places: 3),
            "duration": durationText(elapsedSeconds),
            "duration_seconds": Int(round(elapsedSeconds)),
            "current_pace": currentPaceSecondsPerKm.map { paceText($0) } ?? "-",
            "avg_pace": averagePaceSecondsPerKm.map { paceText($0) } ?? "-",
            "calories": Int(round(calories)),
            "step_count": Int(round(steps)),
            "elevation_gain_m": Int(round(session.elevationGainMeters)),
            "heart_rate_available": session.latestHeartRate != nil,
            "watch_connected": watchConnected,
            "watch_app_installed": watchAppInstalled(),
            "metrics_source": watchConnected ? "apple_watch" : "iphone"
        ]

        if let cadence = cadence, cadence.isFinite {
            payload["cadence"] = Int(round(cadence))
        }
        if let latestHeartRate = session.latestHeartRate {
            payload["heart_rate"] = Int(round(latestHeartRate))
        }
        if session.heartRateSampleCount > 0 {
            payload["avg_heart_rate"] = Int(round(session.heartRateSum / Double(session.heartRateSampleCount)))
        }
        if let startLocation = session.routeLocations.first {
            payload["start_location"] = liveRunLocationPayload(startLocation)
        }
        if let endLocation = session.routeLocations.last {
            payload["end_location"] = liveRunLocationPayload(endLocation)
        }
        if !session.routeLocations.isEmpty {
            payload["route_points"] = sampledRouteLocations(session.routeLocations).map { liveRunLocationPayload($0) }
        }
        if let endDate = session.endDate {
            payload["ended_at"] = isoString(endDate)
        }
        return payload
    }

    private func liveRunLocationPayload(_ location: CLLocation) -> [String: Any] {
        [
            "lat": rounded(location.coordinate.latitude, places: 6),
            "lng": rounded(location.coordinate.longitude, places: 6)
        ]
    }

    private func sampledRouteLocations(_ locations: [CLLocation], limit: Int = 80) -> [CLLocation] {
        guard locations.count > limit else { return locations }
        let step = max(1, Int(ceil(Double(locations.count) / Double(limit))))
        var sampled = locations.enumerated().compactMap { index, location in
            index % step == 0 ? location : nil
        }
        if let last = locations.last {
            if let currentLast = sampled.last {
                if currentLast.timestamp != last.timestamp ||
                    currentLast.coordinate.latitude != last.coordinate.latitude ||
                    currentLast.coordinate.longitude != last.coordinate.longitude {
                    sampled.append(last)
                }
            } else {
                sampled.append(last)
            }
        }
        return sampled
    }

    private func configureWatchConnectivity() {
        guard WCSession.isSupported() else { return }

        let session = WCSession.default
        if !watchConnectivityConfigured || session.delegate == nil {
            session.delegate = self
            watchConnectivityConfigured = true
        }
        if session.activationState == .notActivated {
            session.activate()
        }
    }

    private func sendWatchRunCommand(_ command: String, extra: [String: Any] = [:]) {
        guard WCSession.isSupported() else { return }

        configureWatchConnectivity()
        let watchSession = WCSession.default
        var message: [String: Any] = [
            "type": "liveRunCommand",
            "command": command,
            "timestamp": Date().timeIntervalSince1970
        ]
        extra.forEach { message[$0.key] = $0.value }

        if watchSession.activationState != .activated {
            watchSession.activate()
        }
        if watchSession.isReachable {
            watchSession.sendMessage(message, replyHandler: nil, errorHandler: nil)
            return
        }
        try? watchSession.updateApplicationContext(message)
        watchSession.transferUserInfo(message)
    }

    private func startWatchWorkoutApp(runType: String, runId: String, weightKg: Double, startedAt: Date) {
        guard HKHealthStore.isHealthDataAvailable(), watchAppInstalled() else { return }

        let configuration = HKWorkoutConfiguration()
        configuration.activityType = .running
        configuration.locationType = runType == "treadmill" ? .indoor : .outdoor

        let commandExtra: [String: Any] = [
            "runType": runType,
            "runId": runId,
            "weightKg": weightKg,
            "startedAt": isoString(startedAt)
        ]

        healthStore.startWatchApp(with: configuration) { [weak self] success, error in
            DispatchQueue.main.async {
                guard let self = self,
                      let session = self.liveRunSession,
                      session.id == runId,
                      session.status == .running else {
                    return
                }

                if success {
                    self.sendWatchRunCommand("start", extra: commandExtra)
                } else if let error = error {
                    self.notifyListeners("liveRunError", data: [
                        "message": "Apple Watch에서 RunMate를 열고 건강 권한을 허용해줘.",
                        "detail": error.localizedDescription,
                        "code": "watch_launch_error"
                    ])
                }
            }
        }
    }

    private func handleWatchMessage(_ message: [String: Any]) {
        guard let type = message["type"] as? String else { return }

        switch type {
        case "liveRunMetrics":
            handleWatchRunMetrics(message)
        case "liveRunError":
            let messageText = (message["message"] as? String) ?? "Apple Watch 러닝 데이터를 가져오지 못했어."
            notifyListeners("liveRunError", data: [
                "message": messageText,
                "code": "watch_error"
            ])
        default:
            break
        }
    }

    private func handleWatchRunMetrics(_ message: [String: Any]) {
        DispatchQueue.main.async {
            guard let session = self.liveRunSession else { return }
            if let runId = message["runId"] as? String, !runId.isEmpty, runId != session.id {
                return
            }

            session.latestWatchMetricsAt = Date()
            if let heartRate = self.numericValue(message["heart_rate"] ?? message["heartRate"]), heartRate > 0 {
                let timestamp = self.numericValue(message["timestamp"]) ?? Date().timeIntervalSince1970
                session.latestHeartRate = heartRate
                if timestamp > session.lastWatchHeartRateTimestamp {
                    session.lastWatchHeartRateTimestamp = timestamp
                    session.heartRateSum += heartRate
                    session.heartRateSampleCount += 1
                }
            }
            if let avgHeartRate = self.numericValue(message["avg_heart_rate"] ?? message["avgHeartRate"]), avgHeartRate > 0, session.heartRateSampleCount == 0 {
                session.latestHeartRate = avgHeartRate
                session.heartRateSum = avgHeartRate
                session.heartRateSampleCount = 1
            }
            if let distanceMeters = self.numericValue(message["distance_m"] ?? message["distanceMeters"]), distanceMeters >= 0 {
                session.watchDistanceMeters = max(session.watchDistanceMeters ?? 0, distanceMeters)
            }
            if let calories = self.numericValue(message["calories"] ?? message["active_energy_kcal"] ?? message["activeEnergyKcal"]), calories >= 0 {
                session.watchCalories = max(session.watchCalories ?? 0, calories)
            }
            if let stepCount = self.numericValue(message["step_count"] ?? message["stepCount"]), stepCount >= 0 {
                session.watchSteps = max(session.watchSteps ?? 0, stepCount)
            }
            if let cadence = self.numericValue(message["cadence"]), cadence > 0 {
                session.cadenceStepsPerMinute = cadence
            }
            if let pace = self.numericValue(message["pace_seconds_per_km"] ?? message["paceSecondsPerKm"]), pace > 0 {
                session.instantPaceSecondsPerKm = pace
            }

            self.emitLiveRunUpdate(reason: "apple_watch")
        }
    }

    private func watchAppInstalled() -> Bool {
        guard WCSession.isSupported() else { return false }
        configureWatchConnectivity()
        let session = WCSession.default
        return session.isPaired && session.isWatchAppInstalled
    }

    private func watchSessionIsReachable() -> Bool {
        guard WCSession.isSupported() else { return false }
        configureWatchConnectivity()
        return WCSession.default.isReachable
    }

    private func numericValue(_ value: Any?) -> Double? {
        if let double = value as? Double, double.isFinite {
            return double
        }
        if let int = value as? Int {
            return Double(int)
        }
        if let number = value as? NSNumber {
            let double = number.doubleValue
            return double.isFinite ? double : nil
        }
        if let string = value as? String, let double = Double(string), double.isFinite {
            return double
        }
        return nil
    }

    private func estimatedCalories(distanceKm: Double, elapsedSeconds: TimeInterval, weightKg: Double) -> Double {
        if distanceKm > 0.05 {
            return max(0, distanceKm * weightKg * 1.036)
        }

        let minutes = max(0, elapsedSeconds / 60.0)
        let joggingMet = 8.3
        return max(0, joggingMet * 3.5 * weightKg / 200.0 * minutes)
    }

    private func queryLiveHeartRateSamples(includeRecentFallback: Bool = false) {
        guard let session = liveRunSession,
              session.status == .running,
              HKHealthStore.isHealthDataAvailable(),
              let quantityType = HKObjectType.quantityType(forIdentifier: .heartRate) else {
            return
        }

        let predicate = HKQuery.predicateForSamples(
            withStart: session.startDate,
            end: Date(),
            options: [.strictStartDate]
        )
        let sort = NSSortDescriptor(key: HKSampleSortIdentifierEndDate, ascending: false)
        let query = HKSampleQuery(
            sampleType: quantityType,
            predicate: predicate,
            limit: 12,
            sortDescriptors: [sort]
        ) { [weak self, weak session] _, samples, _ in
            guard let self = self, let session = session else { return }

            let unit = HKUnit.count().unitDivided(by: HKUnit.minute())
            let heartRateSamples = (samples as? [HKQuantitySample]) ?? []
            DispatchQueue.main.async {
                guard self.liveRunSession === session else { return }

                var didAddSample = false
                for sample in heartRateSamples {
                    if session.heartRateSampleIds.contains(sample.uuid) {
                        continue
                    }
                    let value = sample.quantity.doubleValue(for: unit)
                    guard value.isFinite && value > 0 else { continue }
                    session.heartRateSampleIds.insert(sample.uuid)
                    session.latestHeartRate = value
                    session.heartRateSum += value
                    session.heartRateSampleCount += 1
                    didAddSample = true
                }
                if !didAddSample && session.latestHeartRate == nil && includeRecentFallback {
                    self.queryRecentHeartRateFallback(for: session, quantityType: quantityType)
                    return
                }
                self.emitLiveRunUpdate(reason: "heart_rate")
            }
        }
        healthStore.execute(query)
    }

    private func queryRecentHeartRateFallback(for session: LiveRunSession, quantityType: HKQuantityType) {
        let fallbackStart = session.startDate.addingTimeInterval(-10 * 60)
        let predicate = HKQuery.predicateForSamples(
            withStart: fallbackStart,
            end: Date(),
            options: []
        )
        let sort = NSSortDescriptor(key: HKSampleSortIdentifierEndDate, ascending: false)
        let query = HKSampleQuery(
            sampleType: quantityType,
            predicate: predicate,
            limit: 1,
            sortDescriptors: [sort]
        ) { [weak self, weak session] _, samples, _ in
            guard let self = self, let session = session else { return }

            let unit = HKUnit.count().unitDivided(by: HKUnit.minute())
            let sample = (samples as? [HKQuantitySample])?.first
            DispatchQueue.main.async {
                guard self.liveRunSession === session else { return }

                if let sample = sample {
                    let value = sample.quantity.doubleValue(for: unit)
                    if value.isFinite && value > 0 {
                        session.latestHeartRate = value
                        if !session.heartRateSampleIds.contains(sample.uuid) {
                            session.heartRateSampleIds.insert(sample.uuid)
                            session.heartRateSum += value
                            session.heartRateSampleCount += 1
                        }
                    }
                }
                self.emitLiveRunUpdate(reason: "heart_rate")
            }
        }
        healthStore.execute(query)
    }

    func locationManagerDidChangeAuthorization(_ manager: CLLocationManager) {
        guard let pendingLocationAuthorization = pendingLocationAuthorization else { return }

        switch manager.authorizationStatus {
        case .authorizedAlways, .authorizedWhenInUse:
            self.pendingLocationAuthorization = nil
            pendingLocationAuthorization(true)
        case .denied, .restricted:
            self.pendingLocationAuthorization = nil
            pendingLocationAuthorization(false)
        case .notDetermined:
            break
        @unknown default:
            self.pendingLocationAuthorization = nil
            pendingLocationAuthorization(false)
        }
    }

    func locationManager(_ manager: CLLocationManager, didUpdateLocations locations: [CLLocation]) {
        guard let session = liveRunSession, session.status == .running else { return }

        for location in locations {
            guard location.horizontalAccuracy >= 0,
                  location.horizontalAccuracy <= 55,
                  location.timestamp >= session.activeSegmentStart else {
                continue
            }

            if let lastLocation = session.lastLocation {
                let delta = location.distance(from: lastLocation)
                let timeDelta = location.timestamp.timeIntervalSince(lastLocation.timestamp)
                if delta >= 1.5 && delta <= 220 {
                    session.distanceMeters += delta
                }
                session.updateInstantPace(distanceMeters: delta, elapsedSeconds: timeDelta)
            }
            session.appendRouteLocation(location)
            session.lastLocation = location
            if location.speed > 0.6 {
                let instantPace = 1000.0 / location.speed
                session.updateInstantPace(secondsPerKm: instantPace)
            }

            if location.verticalAccuracy >= 0 && location.verticalAccuracy <= 30 {
                if let lastAltitude = session.lastAltitude {
                    let altitudeDelta = location.altitude - lastAltitude
                    if altitudeDelta > 1.5 {
                        session.elevationGainMeters += altitudeDelta
                    }
                }
                session.lastAltitude = location.altitude
            }
        }

        emitLiveRunUpdate(reason: "location")
    }

    func locationManager(_ manager: CLLocationManager, didFailWithError error: Error) {
        notifyListeners("liveRunError", data: [
            "message": "위치 정보를 가져오지 못했어.",
            "code": "location_error"
        ])
    }

    func session(_ session: WCSession, activationDidCompleteWith activationState: WCSessionActivationState, error: Error?) {
        DispatchQueue.main.async {
            if activationState == .activated {
                self.emitLiveRunUpdate(reason: "watch_connected")
            }
        }
    }

    func sessionDidBecomeInactive(_ session: WCSession) {
    }

    func sessionDidDeactivate(_ session: WCSession) {
        session.activate()
    }

    func session(_ session: WCSession, didReceiveMessage message: [String: Any]) {
        handleWatchMessage(message)
    }

    func session(_ session: WCSession, didReceiveApplicationContext applicationContext: [String: Any]) {
        handleWatchMessage(applicationContext)
    }

    func session(_ session: WCSession, didReceiveUserInfo userInfo: [String: Any]) {
        handleWatchMessage(userInfo)
    }

    private func requestHealthKitAccess(completion: @escaping (Bool, Error?) -> Void) {
        guard HKHealthStore.isHealthDataAvailable() else {
            completion(false, nil)
            return
        }

        healthStore.requestAuthorization(toShare: Set<HKSampleType>(), read: readTypes()) { success, error in
            completion(success, error)
        }
    }

    private func readTypes() -> Set<HKObjectType> {
        var types: Set<HKObjectType> = [HKObjectType.workoutType()]
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

    private func queryRunningWorkouts(days: Int, limit: Int, completion: @escaping (Result<[[String: Any]], Error>) -> Void) {
        let endDate = Date()
        let safeDays = max(1, min(days, 30))
        let startDate = Calendar.current.startOfDay(
            for: Calendar.current.date(byAdding: .day, value: -(safeDays - 1), to: endDate) ?? endDate
        )
        let datePredicate = HKQuery.predicateForSamples(withStart: startDate, end: endDate, options: [.strictStartDate])
        let runningPredicate = HKQuery.predicateForWorkouts(with: .running)
        let predicate = NSCompoundPredicate(andPredicateWithSubpredicates: [datePredicate, runningPredicate])
        let sort = NSSortDescriptor(key: HKSampleSortIdentifierStartDate, ascending: false)
        let safeLimit = max(1, min(limit, 50))

        let query = HKSampleQuery(
            sampleType: HKObjectType.workoutType(),
            predicate: predicate,
            limit: safeLimit,
            sortDescriptors: [sort]
        ) { [weak self] _, samples, error in
            guard let self = self else { return }
            if let error = error {
                completion(.failure(error))
                return
            }

            let workouts = (samples as? [HKWorkout]) ?? []
            if workouts.isEmpty {
                completion(.success([]))
                return
            }

            var results = Array(repeating: [String: Any](), count: workouts.count)
            let group = DispatchGroup()
            let resultQueue = DispatchQueue(label: "RunningMateHealthKit.results")

            for (index, workout) in workouts.enumerated() {
                group.enter()
                self.payload(for: workout) { payload in
                    resultQueue.async {
                        results[index] = payload
                        group.leave()
                    }
                }
            }

            group.notify(queue: .main) {
                completion(.success(results))
            }
        }

        healthStore.execute(query)
    }

    private func payload(for workout: HKWorkout, completion: @escaping ([String: Any]) -> Void) {
        averageHeartRate(for: workout) { [weak self] heartRate in
            guard let self = self else { return }
            self.stepCount(for: workout) { steps in
                let distanceKm = self.distanceKilometers(for: workout)
                let durationSeconds = max(0, workout.duration)
                var payload: [String: Any] = [
                    "id": workout.uuid.uuidString,
                    "date": self.dateKey(workout.startDate),
                    "startDate": self.isoString(workout.startDate),
                    "endDate": self.isoString(workout.endDate),
                    "distance_km": self.rounded(distanceKm, places: 2),
                    "duration": self.durationText(durationSeconds),
                    "durationSeconds": Int(round(durationSeconds)),
                    "avg_pace": distanceKm > 0 ? self.paceText(durationSeconds / distanceKm) : "-",
                    "source": workout.sourceRevision.source.name
                ]

                if let calories = workout.totalEnergyBurned?.doubleValue(for: .kilocalorie()) {
                    payload["calories"] = Int(round(calories))
                }

                if let heartRate = heartRate {
                    payload["avg_heart_rate"] = Int(round(heartRate))
                }

                if let steps = steps, durationSeconds > 0 {
                    payload["step_count"] = Int(round(steps))
                    payload["cadence"] = Int(round((steps / (durationSeconds / 60.0)) / 2.0))
                }

                completion(payload)
            }
        }
    }

    private func distanceKilometers(for workout: HKWorkout) -> Double {
        if let distance = workout.totalDistance?.doubleValue(for: .meter()) {
            return distance / 1000.0
        }
        return 0
    }

    private func averageHeartRate(for workout: HKWorkout, completion: @escaping (Double?) -> Void) {
        guard let quantityType = HKObjectType.quantityType(forIdentifier: .heartRate) else {
            completion(nil)
            return
        }

        let predicate = HKQuery.predicateForSamples(
            withStart: workout.startDate,
            end: workout.endDate,
            options: [.strictStartDate, .strictEndDate]
        )
        let query = HKStatisticsQuery(
            quantityType: quantityType,
            quantitySamplePredicate: predicate,
            options: .discreteAverage
        ) { _, statistics, _ in
            let unit = HKUnit.count().unitDivided(by: HKUnit.minute())
            completion(statistics?.averageQuantity()?.doubleValue(for: unit))
        }
        healthStore.execute(query)
    }

    private func stepCount(for workout: HKWorkout, completion: @escaping (Double?) -> Void) {
        guard let quantityType = HKObjectType.quantityType(forIdentifier: .stepCount) else {
            completion(nil)
            return
        }

        let predicate = HKQuery.predicateForSamples(
            withStart: workout.startDate,
            end: workout.endDate,
            options: [.strictStartDate, .strictEndDate]
        )
        let query = HKStatisticsQuery(
            quantityType: quantityType,
            quantitySamplePredicate: predicate,
            options: .cumulativeSum
        ) { _, statistics, _ in
            completion(statistics?.sumQuantity()?.doubleValue(for: .count()))
        }
        healthStore.execute(query)
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

    private func durationText(_ seconds: TimeInterval) -> String {
        let total = Int(round(seconds))
        let hours = total / 3600
        let minutes = (total % 3600) / 60
        let remain = total % 60
        return String(format: "%02d:%02d:%02d", hours, minutes, remain)
    }

    private func paceText(_ secondsPerKm: Double) -> String {
        guard secondsPerKm.isFinite && secondsPerKm > 0 else {
            return "-"
        }

        let total = Int(round(secondsPerKm))
        return String(format: "%d'%02d\"", total / 60, total % 60)
    }

    private func rounded(_ value: Double, places: Int) -> Double {
        let power = pow(10.0, Double(places))
        return (value * power).rounded() / power
    }
}

private final class LiveRunSession {
    enum Status: String {
        case running
        case paused
        case stopped
    }

    let id = UUID().uuidString
    let startDate = Date()
    let runType: String
    let weightKg: Double
    var status: Status = .running
    var activeSegmentStart: Date
    var pausedAt: Date?
    var pausedDuration: TimeInterval = 0
    var endDate: Date?
    var distanceMeters: Double = 0
    var watchDistanceMeters: Double?
    var instantPaceSecondsPerKm: Double?
    var elevationGainMeters: Double = 0
    var steps: Double = 0
    var watchSteps: Double?
    var watchCalories: Double?
    var stepOffset: Double = 0
    var cadenceStepsPerMinute: Double?
    var lastCadenceSampleAt: Date?
    var lastCadenceSampleSteps: Double = 0
    var lastLocation: CLLocation?
    var lastAltitude: Double?
    var routeLocations: [CLLocation] = []
    var latestHeartRate: Double?
    var heartRateSum: Double = 0
    var heartRateSampleCount: Int = 0
    var lastWatchHeartRateTimestamp: TimeInterval = 0
    var latestWatchMetricsAt: Date?
    var heartRateSampleIds = Set<UUID>()

    init(runType: String, weightKg: Double) {
        self.runType = runType
        self.weightKg = weightKg
        self.activeSegmentStart = startDate
    }

    var elapsedSeconds: TimeInterval {
        let end = endDate ?? Date()
        let currentPause = status == .paused ? max(0, end.timeIntervalSince(pausedAt ?? end)) : 0
        return max(0, end.timeIntervalSince(startDate) - pausedDuration - currentPause)
    }

    func pause() {
        guard status == .running else { return }
        status = .paused
        pausedAt = Date()
        stepOffset = steps
    }

    func resume() {
        guard status == .paused else { return }
        let now = Date()
        if let pausedAt = pausedAt {
            pausedDuration += max(0, now.timeIntervalSince(pausedAt))
        }
        status = .running
        self.pausedAt = nil
        activeSegmentStart = now
        lastLocation = nil
        lastAltitude = nil
        instantPaceSecondsPerKm = nil
        cadenceStepsPerMinute = nil
        lastCadenceSampleAt = nil
        lastCadenceSampleSteps = stepOffset
    }

    func updateInstantPace(distanceMeters: Double, elapsedSeconds: TimeInterval) {
        guard distanceMeters >= 1.0,
              elapsedSeconds >= 0.75,
              elapsedSeconds <= 20 else {
            return
        }

        updateInstantPace(secondsPerKm: elapsedSeconds / (distanceMeters / 1000.0))
    }

    func updateInstantPace(secondsPerKm: Double) {
        guard secondsPerKm.isFinite,
              secondsPerKm >= 90,
              secondsPerKm <= 1800 else {
            return
        }

        if let current = instantPaceSecondsPerKm {
            instantPaceSecondsPerKm = current * 0.65 + secondsPerKm * 0.35
        } else {
            instantPaceSecondsPerKm = secondsPerKm
        }
    }

    func updateStepMetrics(segmentSteps: Double, currentCadenceStepsPerSecond: Double?, at date: Date) {
        let normalizedSegmentSteps = max(0, segmentSteps)
        let totalSteps = stepOffset + normalizedSegmentSteps
        steps = max(steps, totalSteps)

        if let currentCadenceStepsPerSecond = currentCadenceStepsPerSecond,
           currentCadenceStepsPerSecond.isFinite,
           currentCadenceStepsPerSecond > 0 {
            cadenceStepsPerMinute = currentCadenceStepsPerSecond * 60.0
        } else if let lastCadenceSampleAt = lastCadenceSampleAt {
            let elapsed = date.timeIntervalSince(lastCadenceSampleAt)
            let stepDelta = steps - lastCadenceSampleSteps
            if elapsed >= 1.0, stepDelta >= 1 {
                cadenceStepsPerMinute = stepDelta / (elapsed / 60.0)
            } else if cadenceStepsPerMinute == nil, elapsedSeconds > 0 {
                cadenceStepsPerMinute = steps / max(elapsedSeconds / 60.0, 0.1)
            }
        } else if elapsedSeconds > 0 {
            cadenceStepsPerMinute = steps / max(elapsedSeconds / 60.0, 0.1)
        }

        if lastCadenceSampleAt == nil || date.timeIntervalSince(lastCadenceSampleAt ?? date) >= 1.0 {
            lastCadenceSampleAt = date
            lastCadenceSampleSteps = steps
        }
    }

    func appendRouteLocation(_ location: CLLocation) {
        if let last = routeLocations.last,
           location.distance(from: last) < 8,
           location.timestamp.timeIntervalSince(last.timestamp) < 8 {
            return
        }
        routeLocations.append(location)
        if routeLocations.count > 240 {
            routeLocations = routeLocations.enumerated()
                .filter { index, _ in index % 2 == 0 || index == routeLocations.count - 1 }
                .map { _, location in location }
        }
    }

    func stop() {
        if status == .paused, let pausedAt = pausedAt {
            pausedDuration += max(0, Date().timeIntervalSince(pausedAt))
        }
        status = .stopped
        endDate = Date()
        stepOffset = steps
        pausedAt = nil
    }

    var hasRecentWatchMetrics: Bool {
        guard let latestWatchMetricsAt = latestWatchMetricsAt else { return false }
        return Date().timeIntervalSince(latestWatchMetricsAt) < 15
    }
}
