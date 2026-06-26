import Capacitor
import CoreLocation
import CoreMotion
import Foundation
import HealthKit
import MapKit
import UIKit
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
        CAPPluginMethod(name: "discardLiveRun", returnType: CAPPluginReturnPromise),
        CAPPluginMethod(name: "syncWidgetRuns", returnType: CAPPluginReturnPromise),
        CAPPluginMethod(name: "getLiveRunSnapshot", returnType: CAPPluginReturnPromise),
        CAPPluginMethod(name: "getPendingWatchRuns", returnType: CAPPluginReturnPromise),
        CAPPluginMethod(name: "ackPendingWatchRun", returnType: CAPPluginReturnPromise),
        CAPPluginMethod(name: "getCurrentLocation", returnType: CAPPluginReturnPromise),
        CAPPluginMethod(name: "renderRunRouteMap", returnType: CAPPluginReturnPromise)
    ]

    private let pendingWatchRunsKey = "RunningMate.pendingWatchStandaloneRuns"
    private let activeLiveRunSessionKey = "RunningMate.activeLiveRunSession"
    private let healthStore = HKHealthStore()
    private let pedometer = CMPedometer()
    private var locationManager: CLLocationManager?
    private var weatherLocationManager: CLLocationManager?
    private var liveRunSession: LiveRunSession?
    private var pendingLocationAuthorization: ((Bool) -> Void)?
    private var pendingWeatherLocationCall: CAPPluginCall?
    private var liveRunTimer: Timer?
    private var watchConnectivityConfigured = false
    private var lastLiveRunPersistedAt: TimeInterval = 0

    override func load() {
        super.load()
        configureWatchConnectivity()
        observeApplicationLifecycle()
        restorePersistedLiveRunIfNeeded(reason: "plugin_load")
    }

    deinit {
        NotificationCenter.default.removeObserver(self)
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
                        call.resolve(["workouts": workouts])
                    case .failure(let error):
                        call.reject("애플워치 기록을 불러오지 못했어.", "healthkit_query_failed", error)
                    }
                }
            }
        }
    }

    @objc func startLiveRun(_ call: CAPPluginCall) {
        restorePersistedLiveRunIfNeeded(reason: "start_check")
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
                self.persistLiveRunSession(force: true)
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
        restorePersistedLiveRunIfNeeded(reason: "pause_check")
        guard let session = liveRunSession, session.status == .running else {
            call.reject("진행 중인 러닝이 없어.", "no_active_run")
            return
        }

        session.pause()
        persistLiveRunSession(force: true)
        sendWatchRunCommand("pause", extra: ["runId": session.id])
        stopLocationUpdates()
        pedometer.stopUpdates()
        emitLiveRunUpdate(reason: "paused")
        call.resolve(liveRunPayload(for: session))
    }

    @objc func resumeLiveRun(_ call: CAPPluginCall) {
        restorePersistedLiveRunIfNeeded(reason: "resume_check")
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
                self.persistLiveRunSession(force: true)
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
        restorePersistedLiveRunIfNeeded(reason: "stop_check")
        guard let session = liveRunSession else {
            call.reject("종료할 러닝이 없어.", "no_active_run")
            return
        }

        let stoppedAt = Date()
        sendWatchRunCommand("stop", extra: ["runId": session.id])
        stopLiveRunSensors()
        refreshFinalPedometerSnapshot(for: session, endedAt: stoppedAt) { [weak self, weak session] in
            guard let self = self, let session = session, self.liveRunSession === session else {
                call.reject("러닝 종료 중 세션을 찾지 못했어.", "live_run_session_missing")
                return
            }

            session.stop(at: stoppedAt)
            let payload = self.liveRunPayload(for: session, ended: true)
            self.endLiveActivity(with: payload)
            self.notifyListeners("liveRunEnded", data: payload)
            self.liveRunSession = nil
            self.clearPersistedLiveRunSession()
            call.resolve(payload)
        }
    }

    @objc func discardLiveRun(_ call: CAPPluginCall) {
        restorePersistedLiveRunIfNeeded(reason: "discard_check")
        guard let session = liveRunSession else {
            clearPersistedLiveRunSession()
            call.resolve([
                "active": false,
                "status": "stopped",
                "reason": "discarded"
            ])
            return
        }

        session.stop()
        sendWatchRunCommand("stop", extra: ["runId": session.id])
        stopLiveRunSensors()
        let payload = liveRunPayload(for: session, reason: "discarded", ended: true)
        endLiveActivity(with: payload)
        notifyListeners("liveRunUpdate", data: payload)
        liveRunSession = nil
        clearPersistedLiveRunSession()
        call.resolve(payload)
    }

    @objc func syncWidgetRuns(_ call: CAPPluginCall) {
        let runs = (call.getArray("runs", JSObject.self) ?? []).map { object in
            object.reduce(into: [String: Any]()) { result, item in
                result[item.key] = item.value
            }
        }
        let count = RunningMateWidgetStore.replaceCompletedRuns(from: runs)
        call.resolve([
            "synced": true,
            "count": count
        ])
    }

    @objc func getCurrentLocation(_ call: CAPPluginCall) {
        DispatchQueue.main.async {
            guard self.pendingWeatherLocationCall == nil else {
                call.reject("이미 위치를 확인하는 중이야.", "location_in_progress")
                return
            }

            let manager = self.currentWeatherLocationManager()
            switch manager.authorizationStatus {
            case .authorizedAlways, .authorizedWhenInUse:
                self.pendingWeatherLocationCall = call
                manager.requestLocation()
            case .notDetermined:
                self.pendingWeatherLocationCall = call
                manager.requestWhenInUseAuthorization()
            case .denied, .restricted:
                call.reject("위치 권한이 허용되지 않았어.", "location_permission_denied")
            @unknown default:
                call.reject("현재 위치를 확인하지 못했어.", "location_unavailable")
            }
        }
    }

    @objc func getLiveRunSnapshot(_ call: CAPPluginCall) {
        restorePersistedLiveRunIfNeeded(reason: "snapshot_restore")
        guard let session = liveRunSession else {
            call.resolve(["active": false])
            return
        }

        call.resolve(liveRunPayload(for: session))
    }

    @objc func getPendingWatchRuns(_ call: CAPPluginCall) {
        call.resolve([
            "runs": pendingWatchRuns(),
            "count": pendingWatchRuns().count
        ])
    }

    @objc func ackPendingWatchRun(_ call: CAPPluginCall) {
        let ids = pendingWatchRunIds(from: call)
        guard !ids.isEmpty else {
            call.resolve([
                "removed": 0,
                "runs": pendingWatchRuns(),
                "count": pendingWatchRuns().count
            ])
            return
        }

        let before = pendingWatchRuns()
        let next = before.filter { run in
            guard let id = run["id"] as? String else { return true }
            return !ids.contains(id)
        }
        savePendingWatchRuns(next)
        call.resolve([
            "removed": before.count - next.count,
            "runs": next,
            "count": next.count
        ])
    }

    @objc func renderRunRouteMap(_ call: CAPPluginCall) {
        let coordinates = routeCoordinates(from: call)
        guard !coordinates.isEmpty else {
            call.resolve([
                "imageDataUrl": "",
                "hasRoute": false
            ])
            return
        }

        let width = CGFloat(max(260.0, min(call.getDouble("width") ?? 680.0, 1400.0)))
        let height = CGFloat(max(220.0, min(call.getDouble("height") ?? 520.0, 1200.0)))
        let scale = CGFloat(max(1.0, min(call.getDouble("scale") ?? Double(UIScreen.main.scale), 3.0)))
        let distanceKm = call.getDouble("distanceKm") ?? call.getDouble("distance_km") ?? 0
        let explicitLabel = call.getString("locationLabel")?.trimmingCharacters(in: .whitespacesAndNewlines)
        let includeLocationLabel = call.getBool("includeLocationLabel", true)

        let render: (String?) -> Void = { [weak self] locationLabel in
            self?.renderRunRouteSnapshot(
                coordinates: coordinates,
                distanceKm: distanceKm,
                locationLabel: locationLabel,
                width: width,
                height: height,
                scale: scale,
                call: call
            )
        }

        if let explicitLabel = explicitLabel, !explicitLabel.isEmpty {
            render(explicitLabel)
            return
        }

        guard includeLocationLabel, let finalCoordinate = coordinates.last else {
            render(nil)
            return
        }

        let geocoder = CLGeocoder()
        let location = CLLocation(latitude: finalCoordinate.latitude, longitude: finalCoordinate.longitude)
        geocoder.reverseGeocodeLocation(location, preferredLocale: Locale(identifier: "ko_KR")) { placemarks, _ in
            let label = placemarks?.first.map { self.locationLabel(from: $0) }
            render(label)
        }
    }

    private func routeCoordinates(from call: CAPPluginCall) -> [CLLocationCoordinate2D] {
        let rawPoints = call.getArray("routePoints", JSObject.self)
            ?? call.getArray("route_points", JSObject.self)
            ?? []

        return rawPoints.compactMap { point in
            guard let latitude = numericValue(point["lat"] ?? point["latitude"]),
                  let longitude = numericValue(point["lng"] ?? point["lon"] ?? point["longitude"]),
                  latitude >= -90,
                  latitude <= 90,
                  longitude >= -180,
                  longitude <= 180 else {
                return nil
            }

            return CLLocationCoordinate2D(latitude: latitude, longitude: longitude)
        }
    }

    private func renderRunRouteSnapshot(
        coordinates: [CLLocationCoordinate2D],
        distanceKm: Double,
        locationLabel: String?,
        width: CGFloat,
        height: CGFloat,
        scale: CGFloat,
        call: CAPPluginCall
    ) {
        let options = MKMapSnapshotter.Options()
        options.size = CGSize(width: width, height: height)
        options.scale = scale
        options.mapType = .standard
        options.showsBuildings = true
        options.mapRect = paddedMapRect(for: coordinates)

        if #available(iOS 13.0, *) {
            options.traitCollection = UITraitCollection(userInterfaceStyle: .light)
        }

        let snapshotter = MKMapSnapshotter(options: options)
        snapshotter.start(with: DispatchQueue.global(qos: .userInitiated)) { [weak self] snapshot, error in
            guard let self = self, let snapshot = snapshot else {
                DispatchQueue.main.async {
                    call.reject("Apple 지도를 생성하지 못했어.", "map_render_failed", error)
                }
                return
            }

            let image = self.routeMapImage(
                from: snapshot,
                coordinates: coordinates,
                distanceKm: distanceKm,
                locationLabel: locationLabel
            )

            guard let data = image.pngData() else {
                DispatchQueue.main.async {
                    call.reject("지도 이미지를 저장하지 못했어.", "map_image_failed")
                }
                return
            }

            DispatchQueue.main.async {
                call.resolve([
                    "imageDataUrl": "data:image/png;base64,\(data.base64EncodedString())",
                    "width": Int(width),
                    "height": Int(height),
                    "hasRoute": coordinates.count > 1
                ])
            }
        }
    }

    private func paddedMapRect(for coordinates: [CLLocationCoordinate2D]) -> MKMapRect {
        var rect = MKMapRect.null
        for coordinate in coordinates {
            let point = MKMapPoint(coordinate)
            let pointRect = MKMapRect(x: point.x, y: point.y, width: 1, height: 1)
            rect = rect.isNull ? pointRect : rect.union(pointRect)
        }

        guard !rect.isNull else {
            return MKMapRect.world
        }

        let centerCoordinate = MKMapPoint(x: rect.midX, y: rect.midY).coordinate
        let metersPerMapPoint = max(MKMetersPerMapPointAtLatitude(centerCoordinate.latitude), 0.000001)
        let minPaddingMapPoints = 520.0 / metersPerMapPoint
        let horizontalPadding = max(rect.size.width * 0.26, minPaddingMapPoints)
        let verticalPadding = max(rect.size.height * 0.34, minPaddingMapPoints)
        return rect.insetBy(dx: -horizontalPadding, dy: -verticalPadding)
    }

    private func routeMapImage(
        from snapshot: MKMapSnapshotter.Snapshot,
        coordinates: [CLLocationCoordinate2D],
        distanceKm: Double,
        locationLabel: String?
    ) -> UIImage {
        let baseImage = snapshot.image
        let imageSize = baseImage.size
        let points = coordinates.map { snapshot.point(for: $0) }
        let format = UIGraphicsImageRendererFormat.default()
        format.scale = baseImage.scale
        format.opaque = true

        return UIGraphicsImageRenderer(size: imageSize, format: format).image { rendererContext in
            baseImage.draw(at: .zero)

            let context = rendererContext.cgContext
            drawRouteLine(points: points, in: context)
            drawKilometerMarkers(coordinates: coordinates, points: points, distanceKm: distanceKm, imageSize: imageSize)

            if let startPoint = points.first {
                drawRouteEndpoint(at: startPoint, color: UIColor(red: 0.34, green: 0.78, blue: 0.08, alpha: 1), radius: 7)
            }
            if let endPoint = points.last {
                drawRouteEndpoint(at: endPoint, color: UIColor(red: 1, green: 0.08, blue: 0.04, alpha: 1), radius: 11)
            }
            if let locationLabel = locationLabel?.trimmingCharacters(in: .whitespacesAndNewlines), !locationLabel.isEmpty {
                drawLocationLabel(locationLabel, imageSize: imageSize)
            }
        }
    }

    private func drawRouteLine(points: [CGPoint], in context: CGContext) {
        guard points.count > 1 else { return }

        let path = CGMutablePath()
        path.move(to: points[0])
        points.dropFirst().forEach { path.addLine(to: $0) }

        context.saveGState()
        context.setLineCap(.round)
        context.setLineJoin(.round)
        context.setShadow(offset: CGSize(width: 0, height: 3), blur: 8, color: UIColor.black.withAlphaComponent(0.22).cgColor)
        context.setStrokeColor(UIColor.white.withAlphaComponent(0.92).cgColor)
        context.setLineWidth(11)
        context.addPath(path)
        context.strokePath()
        context.restoreGState()

        context.saveGState()
        context.setLineCap(.round)
        context.setLineJoin(.round)
        for index in 1..<points.count {
            let progress = CGFloat(index) / CGFloat(max(points.count - 1, 1))
            context.setStrokeColor(routeSegmentColor(progress: progress).cgColor)
            context.setLineWidth(6.5)
            context.move(to: points[index - 1])
            context.addLine(to: points[index])
            context.strokePath()
        }
        context.restoreGState()
    }

    private func drawKilometerMarkers(
        coordinates: [CLLocationCoordinate2D],
        points: [CGPoint],
        distanceKm: Double,
        imageSize: CGSize
    ) {
        let markers = kilometerMarkers(coordinates: coordinates, points: points, distanceKm: distanceKm)
        for marker in markers {
            drawTextBubble("\(marker.km) km", at: marker.point, imageSize: imageSize)
        }
    }

    private func kilometerMarkers(
        coordinates: [CLLocationCoordinate2D],
        points: [CGPoint],
        distanceKm: Double
    ) -> [(km: Int, point: CGPoint)] {
        guard coordinates.count > 1, coordinates.count == points.count else { return [] }

        let routeMeters = routeDistanceMeters(for: coordinates)
        guard routeMeters > 0 else { return [] }

        let displayMeters = max(routeMeters, max(0, distanceKm) * 1000.0)
        let maxKm = max(0, Int(floor(displayMeters / 1000.0)))
        guard maxKm > 0 else { return [] }

        let stride = max(1, Int(ceil(Double(maxKm) / 8.0)))
        var markers: [(km: Int, point: CGPoint)] = []
        var cumulativeMeters = 0.0
        var targetKm = stride

        for index in 1..<coordinates.count {
            let segmentMeters = distanceMeters(from: coordinates[index - 1], to: coordinates[index])
            guard segmentMeters > 0 else { continue }

            while targetKm <= maxKm {
                let targetMeters = Double(targetKm) * 1000.0
                let targetRouteMeters = min(routeMeters, targetMeters * routeMeters / displayMeters)
                if targetRouteMeters > cumulativeMeters + segmentMeters {
                    break
                }

                let ratio = max(0, min(1, (targetRouteMeters - cumulativeMeters) / segmentMeters))
                let point = CGPoint(
                    x: points[index - 1].x + (points[index].x - points[index - 1].x) * CGFloat(ratio),
                    y: points[index - 1].y + (points[index].y - points[index - 1].y) * CGFloat(ratio)
                )
                markers.append((km: targetKm, point: point))
                targetKm += stride
            }

            cumulativeMeters += segmentMeters
        }

        if markers.last?.km != maxKm, let lastPoint = points.last {
            markers.append((km: maxKm, point: lastPoint))
        }

        return Array(markers.suffix(8))
    }

    private func routeDistanceMeters(for coordinates: [CLLocationCoordinate2D]) -> Double {
        guard coordinates.count > 1 else { return 0 }
        var total = 0.0
        for index in 1..<coordinates.count {
            total += distanceMeters(from: coordinates[index - 1], to: coordinates[index])
        }
        return total
    }

    private func distanceMeters(from start: CLLocationCoordinate2D, to end: CLLocationCoordinate2D) -> Double {
        CLLocation(latitude: start.latitude, longitude: start.longitude)
            .distance(from: CLLocation(latitude: end.latitude, longitude: end.longitude))
    }

    private func routeSegmentColor(progress: CGFloat) -> UIColor {
        if progress > 0.62 && progress < 0.78 {
            return UIColor(red: 1.0, green: 0.56, blue: 0.06, alpha: 1)
        }
        if progress > 0.78 {
            return UIColor(red: 0.64, green: 0.88, blue: 0.02, alpha: 1)
        }
        return UIColor(red: 0.45, green: 0.82, blue: 0.03, alpha: 1)
    }

    private func drawRouteEndpoint(at point: CGPoint, color: UIColor, radius: CGFloat) {
        let outerRect = CGRect(x: point.x - radius - 4, y: point.y - radius - 4, width: (radius + 4) * 2, height: (radius + 4) * 2)
        let innerRect = CGRect(x: point.x - radius, y: point.y - radius, width: radius * 2, height: radius * 2)

        UIColor.black.withAlphaComponent(0.18).setFill()
        UIBezierPath(ovalIn: outerRect.offsetBy(dx: 0, dy: 3)).fill()
        UIColor.white.setFill()
        UIBezierPath(ovalIn: outerRect).fill()
        color.setFill()
        UIBezierPath(ovalIn: innerRect).fill()
    }

    private func drawTextBubble(_ text: String, at point: CGPoint, imageSize: CGSize) {
        let font = UIFont.systemFont(ofSize: 17, weight: .bold)
        let attributes: [NSAttributedString.Key: Any] = [
            .font: font,
            .foregroundColor: UIColor.black
        ]
        let textSize = (text as NSString).size(withAttributes: attributes)
        let bubbleSize = CGSize(width: textSize.width + 22, height: 31)
        var rect = CGRect(
            x: point.x - bubbleSize.width / 2,
            y: point.y - bubbleSize.height - 8,
            width: bubbleSize.width,
            height: bubbleSize.height
        )
        rect.origin.x = min(max(8, rect.origin.x), max(8, imageSize.width - rect.width - 8))
        rect.origin.y = min(max(8, rect.origin.y), max(8, imageSize.height - rect.height - 8))

        let path = UIBezierPath(roundedRect: rect, cornerRadius: rect.height / 2)
        UIColor.black.withAlphaComponent(0.16).setFill()
        UIBezierPath(roundedRect: rect.offsetBy(dx: 0, dy: 3), cornerRadius: rect.height / 2).fill()
        UIColor.white.withAlphaComponent(0.96).setFill()
        path.fill()

        let textRect = CGRect(
            x: rect.midX - textSize.width / 2,
            y: rect.midY - textSize.height / 2 - 0.5,
            width: textSize.width,
            height: textSize.height
        )
        (text as NSString).draw(in: textRect, withAttributes: attributes)
    }

    private func drawLocationLabel(_ label: String, imageSize: CGSize) {
        let font = UIFont.systemFont(ofSize: 18, weight: .semibold)
        let maxWidth = imageSize.width * 0.72
        let attributes: [NSAttributedString.Key: Any] = [
            .font: font,
            .foregroundColor: UIColor.black
        ]
        let textSize = (label as NSString).boundingRect(
            with: CGSize(width: maxWidth - 30, height: 80),
            options: [.usesLineFragmentOrigin, .usesFontLeading],
            attributes: attributes,
            context: nil
        ).size
        let rect = CGRect(
            x: 24,
            y: 24,
            width: min(maxWidth, textSize.width + 30),
            height: max(48, textSize.height + 22)
        )

        UIColor.black.withAlphaComponent(0.1).setFill()
        UIBezierPath(roundedRect: rect.offsetBy(dx: 0, dy: 3), cornerRadius: 10).fill()
        UIColor.white.withAlphaComponent(0.95).setFill()
        UIBezierPath(roundedRect: rect, cornerRadius: 10).fill()

        let textRect = CGRect(x: rect.minX + 15, y: rect.minY + 11, width: rect.width - 30, height: rect.height - 20)
        (label as NSString).draw(in: textRect, withAttributes: attributes)
    }

    private func locationLabel(from placemark: CLPlacemark) -> String {
        var parts: [String] = []
        [placemark.locality, placemark.administrativeArea, placemark.country].forEach { value in
            guard let value = value?.trimmingCharacters(in: .whitespacesAndNewlines),
                  !value.isEmpty,
                  !parts.contains(value) else {
                return
            }
            parts.append(value)
        }

        if parts.isEmpty, let name = placemark.name?.trimmingCharacters(in: .whitespacesAndNewlines), !name.isEmpty {
            parts.append(name)
        }

        return parts.joined(separator: ", ")
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

    private func observeApplicationLifecycle() {
        let center = NotificationCenter.default
        center.addObserver(
            self,
            selector: #selector(applicationDidEnterBackground),
            name: UIApplication.didEnterBackgroundNotification,
            object: nil
        )
        center.addObserver(
            self,
            selector: #selector(applicationWillTerminate),
            name: UIApplication.willTerminateNotification,
            object: nil
        )
        center.addObserver(
            self,
            selector: #selector(applicationDidBecomeActive),
            name: UIApplication.didBecomeActiveNotification,
            object: nil
        )
    }

    @objc private func applicationDidEnterBackground() {
        persistLiveRunSession(force: true)
        if let session = liveRunSession, session.status != .stopped {
            updateLiveActivity(with: liveRunPayload(for: session, reason: "background"), force: true)
        }
    }

    @objc private func applicationWillTerminate() {
        persistLiveRunSession(force: true)
    }

    @objc private func applicationDidBecomeActive() {
        restorePersistedLiveRunIfNeeded(reason: "foreground_restore")
        guard liveRunSession != nil else { return }
        emitLiveRunUpdate(reason: "foreground")
    }

    private func persistLiveRunSession(force: Bool = false) {
        guard let session = liveRunSession, session.status != .stopped else {
            if force { clearPersistedLiveRunSession() }
            return
        }

        let now = Date().timeIntervalSince1970
        guard force || now - lastLiveRunPersistedAt >= 2.0 else { return }

        UserDefaults.standard.set(session.persistencePayload(), forKey: activeLiveRunSessionKey)
        lastLiveRunPersistedAt = now
        if force {
            UserDefaults.standard.synchronize()
        }
    }

    private func clearPersistedLiveRunSession() {
        UserDefaults.standard.removeObject(forKey: activeLiveRunSessionKey)
        lastLiveRunPersistedAt = 0
    }

    private func restorePersistedLiveRunIfNeeded(reason: String) {
        if let session = liveRunSession, session.status != .stopped {
            return
        }

        guard let snapshot = UserDefaults.standard.dictionary(forKey: activeLiveRunSessionKey) else {
            return
        }

        guard let session = LiveRunSession.restore(from: snapshot), session.status != .stopped else {
            clearPersistedLiveRunSession()
            return
        }

        liveRunSession = session
        configureWatchConnectivity()

        if session.status == .running {
            configureLocationTracking()
            startLocationUpdates()
            startPedometerUpdates(from: session.activeSegmentStart)
            startLiveRunTimers()
        } else {
            stopLocationUpdates()
            pedometer.stopUpdates()
        }

        let payload = liveRunPayload(for: session, reason: reason)
        startLiveActivity(with: payload)
        notifyListeners("liveRunUpdate", data: payload)
        persistLiveRunSession(force: true)
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

    private func currentWeatherLocationManager() -> CLLocationManager {
        if let weatherLocationManager = weatherLocationManager {
            return weatherLocationManager
        }

        let manager = CLLocationManager()
        manager.delegate = self
        manager.desiredAccuracy = kCLLocationAccuracyHundredMeters
        manager.distanceFilter = kCLDistanceFilterNone
        weatherLocationManager = manager
        return manager
    }

    private func resolveWeatherLocation(_ location: CLLocation) {
        guard let call = pendingWeatherLocationCall else { return }
        pendingWeatherLocationCall = nil
        call.resolve([
            "lat": rounded(location.coordinate.latitude, places: 5),
            "lon": rounded(location.coordinate.longitude, places: 5),
            "accuracy": rounded(location.horizontalAccuracy, places: 1)
        ])
    }

    private func rejectWeatherLocation(_ message: String, code: String) {
        guard let call = pendingWeatherLocationCall else { return }
        pendingWeatherLocationCall = nil
        call.reject(message, code)
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

        liveRunTimer = Timer.scheduledTimer(withTimeInterval: 0.5, repeats: true) { [weak self] _ in
            self?.queryLivePedometerSnapshot()
            self?.emitLiveRunUpdate(reason: "tick")
        }
        if let liveRunTimer = liveRunTimer {
            RunLoop.main.add(liveRunTimer, forMode: .common)
        }
    }

    private func stopLiveRunSensors() {
        stopLocationUpdates()
        pedometer.stopUpdates()
        liveRunTimer?.invalidate()
        liveRunTimer = nil
    }

    private func refreshFinalPedometerSnapshot(for session: LiveRunSession, endedAt: Date, completion: @escaping () -> Void) {
        guard CMPedometer.isStepCountingAvailable(), session.status == .running else {
            completion()
            return
        }

        var didFinish = false
        let finish: () -> Void = {
            guard !didFinish else { return }
            didFinish = true
            completion()
        }

        pedometer.queryPedometerData(from: session.activeSegmentStart, to: endedAt) { [weak self, weak session] data, _ in
            DispatchQueue.main.async {
                if let self = self,
                   let session = session,
                   self.liveRunSession === session,
                   let data = data {
                    session.updateStepMetrics(
                        segmentSteps: data.numberOfSteps.doubleValue,
                        currentCadenceStepsPerSecond: data.currentCadence?.doubleValue,
                        at: endedAt
                    )
                }
                finish()
            }
        }

        DispatchQueue.main.asyncAfter(deadline: .now() + 0.7) {
            finish()
        }
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
        persistLiveRunSession(force: !["tick", "pedometer", "pedometer_snapshot"].contains(reason))
        let payload = liveRunPayload(for: session, reason: reason)
        updateLiveActivity(with: payload, force: !["tick", "pedometer", "pedometer_snapshot"].contains(reason))
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
        let hasWatchHeartRate = session.latestHeartRate != nil
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
            "heart_rate_available": hasWatchHeartRate,
            "watch_connected": watchConnected,
            "watch_app_installed": watchAppInstalled(),
            "metrics_source": session.hasRecentWatchMetrics ? "apple_watch_workout" : "iphone"
        ]

        if let cadence = cadence, cadence.isFinite {
            payload["cadence"] = Int(round(cadence))
        }
        if let latestHeartRate = session.latestHeartRate {
            payload["heart_rate"] = Int(round(latestHeartRate))
            payload["heart_rate_source"] = "apple_watch_workout"
        }
        if session.heartRateSampleCount > 0 {
            payload["avg_heart_rate"] = Int(round(session.heartRateSum / Double(session.heartRateSampleCount)))
            payload["avg_heart_rate_source"] = "apple_watch_workout"
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
        case "watchStandaloneRunEnded":
            handleWatchStandaloneRunEnded(message)
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

    private func handleWatchStandaloneRunEnded(_ message: [String: Any]) {
        DispatchQueue.main.async {
            let run = self.normalizedWatchStandaloneRun(message)
            guard let id = run["id"] as? String, !id.isEmpty else { return }

            var pending = self.pendingWatchRuns()
            pending.removeAll { ($0["id"] as? String) == id }
            pending.insert(run, at: 0)
            self.savePendingWatchRuns(pending)
            self.notifyListeners("watchStandaloneRunEnded", data: [
                "run": run,
                "runs": pending,
                "count": pending.count
            ])
        }
    }

    private func normalizedWatchStandaloneRun(_ message: [String: Any]) -> [String: Any] {
        var run: [String: Any] = [
            "id": (message["id"] as? String) ?? "watch-\(UUID().uuidString)",
            "source": "apple_watch_standalone",
            "metrics_source": "apple_watch_standalone",
            "active": false,
            "status": "stopped",
            "received_at": isoString(Date())
        ]

        let stringKeys = [
            "date",
            "started_at",
            "startedAt",
            "ended_at",
            "endedAt",
            "duration",
            "avg_pace",
            "avgPace",
            "run_type",
            "runType"
        ]
        for key in stringKeys {
            if let value = message[key] as? String, !value.isEmpty {
                run[key] = value
            }
        }

        let numericKeys = [
            "distance_km",
            "distanceKm",
            "duration_seconds",
            "durationSeconds",
            "calories",
            "heart_rate",
            "heartRate",
            "avg_heart_rate",
            "avgHeartRate",
            "cadence",
            "step_count",
            "stepCount",
            "elevation_gain_m",
            "elevationGainM",
            "pace_seconds_per_km",
            "paceSecondsPerKm"
        ]
        for key in numericKeys {
            if let value = numericValue(message[key]) {
                run[key] = value
            }
        }

        if let routePoints = normalizedRoutePoints(message["route_points"] ?? message["routePoints"]), !routePoints.isEmpty {
            run["route_points"] = routePoints
            run["start_location"] = normalizedRoutePoint(message["start_location"] ?? message["startLocation"]) ?? routePoints.first
            run["end_location"] = normalizedRoutePoint(message["end_location"] ?? message["endLocation"]) ?? routePoints.last
        } else {
            if let start = normalizedRoutePoint(message["start_location"] ?? message["startLocation"]) {
                run["start_location"] = start
            }
            if let end = normalizedRoutePoint(message["end_location"] ?? message["endLocation"]) {
                run["end_location"] = end
            }
        }

        if run["date"] == nil,
           let startedAt = run["started_at"] as? String,
           let date = ISO8601DateFormatter().date(from: startedAt) {
            run["date"] = dateKey(date)
        }

        return run
    }

    private func normalizedRoutePoints(_ value: Any?) -> [[String: Any]]? {
        guard let points = value as? [[String: Any]] else { return nil }
        let normalized = points.compactMap { normalizedRoutePoint($0) }
        guard normalized.count <= 80 else {
            let step = max(1, Int(ceil(Double(normalized.count) / 80.0)))
            var sampled = normalized.enumerated().compactMap { index, point in
                index % step == 0 ? point : nil
            }
            if let last = normalized.last,
               let currentLast = sampled.last,
               numericValue(currentLast["lat"]) != numericValue(last["lat"]) ||
                numericValue(currentLast["lng"]) != numericValue(last["lng"]) {
                sampled.append(last)
            }
            return sampled
        }
        return normalized
    }

    private func normalizedRoutePoint(_ value: Any?) -> [String: Any]? {
        guard let point = value as? [String: Any],
              let latitude = numericValue(point["lat"] ?? point["latitude"]),
              let longitude = numericValue(point["lng"] ?? point["lon"] ?? point["longitude"]),
              latitude >= -90,
              latitude <= 90,
              longitude >= -180,
              longitude <= 180 else {
            return nil
        }

        return [
            "lat": rounded(latitude, places: 6),
            "lng": rounded(longitude, places: 6)
        ]
    }

    private func pendingWatchRuns() -> [[String: Any]] {
        UserDefaults.standard.array(forKey: pendingWatchRunsKey) as? [[String: Any]] ?? []
    }

    private func savePendingWatchRuns(_ runs: [[String: Any]]) {
        UserDefaults.standard.set(runs, forKey: pendingWatchRunsKey)
    }

    private func pendingWatchRunIds(from call: CAPPluginCall) -> Set<String> {
        var ids = Set<String>()
        if let id = call.getString("id")?.trimmingCharacters(in: .whitespacesAndNewlines), !id.isEmpty {
            ids.insert(id)
        }
        if let rawIds = call.getArray("ids", String.self) {
            for id in rawIds {
                let trimmed = id.trimmingCharacters(in: .whitespacesAndNewlines)
                if !trimmed.isEmpty {
                    ids.insert(trimmed)
                }
            }
        }
        return ids
    }

    private func handleWatchRunMetrics(_ message: [String: Any]) {
        DispatchQueue.main.async {
            guard let session = self.liveRunSession else { return }
            guard session.status == .running || session.status == .paused else { return }
            guard let runId = message["runId"] as? String, !runId.isEmpty, runId == session.id else {
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
                if session.lastCadenceSampleAt == nil || Date().timeIntervalSince(session.lastCadenceSampleAt ?? Date()) > 2.0 {
                    session.setCadenceStepsPerMinute(cadence)
                }
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

    func locationManagerDidChangeAuthorization(_ manager: CLLocationManager) {
        if manager === weatherLocationManager {
            guard pendingWeatherLocationCall != nil else { return }
            switch manager.authorizationStatus {
            case .authorizedAlways, .authorizedWhenInUse:
                manager.requestLocation()
            case .denied, .restricted:
                rejectWeatherLocation("위치 권한이 허용되지 않았어.", code: "location_permission_denied")
            case .notDetermined:
                break
            @unknown default:
                rejectWeatherLocation("현재 위치를 확인하지 못했어.", code: "location_unavailable")
            }
            return
        }

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
        if manager === weatherLocationManager {
            if let location = locations.last,
               location.horizontalAccuracy >= 0,
               location.coordinate.latitude.isFinite,
               location.coordinate.longitude.isFinite {
                resolveWeatherLocation(location)
            } else {
                rejectWeatherLocation("현재 위치를 확인하지 못했어.", code: "location_unavailable")
            }
            return
        }

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
        if manager === weatherLocationManager {
            rejectWeatherLocation("현재 위치를 확인하지 못했어.", code: "location_error")
            return
        }

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

    let id: String
    let startDate: Date
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

    init(runType: String, weightKg: Double, id: String = UUID().uuidString, startDate: Date = Date()) {
        self.id = id
        self.startDate = startDate
        self.runType = runType
        self.weightKg = weightKg
        self.activeSegmentStart = startDate
    }

    static func restore(from payload: [String: Any]) -> LiveRunSession? {
        guard let id = stringValue(payload["id"]),
              let startDate = dateValue(payload["startDate"] ?? payload["start_date"]),
              let runType = stringValue(payload["runType"] ?? payload["run_type"]),
              let statusRaw = stringValue(payload["status"]),
              let status = Status(rawValue: statusRaw),
              status != .stopped else {
            return nil
        }

        let weightKg = doubleValue(payload["weightKg"] ?? payload["weight_kg"]) ?? 60.0
        let session = LiveRunSession(runType: runType, weightKg: weightKg, id: id, startDate: startDate)
        session.status = status
        session.activeSegmentStart = dateValue(payload["activeSegmentStart"] ?? payload["active_segment_start"]) ?? startDate
        session.pausedAt = dateValue(payload["pausedAt"] ?? payload["paused_at"])
        session.pausedDuration = max(0, doubleValue(payload["pausedDuration"] ?? payload["paused_duration"]) ?? 0)
        session.endDate = dateValue(payload["endDate"] ?? payload["end_date"])
        session.distanceMeters = max(0, doubleValue(payload["distanceMeters"] ?? payload["distance_meters"]) ?? 0)
        session.watchDistanceMeters = doubleValue(payload["watchDistanceMeters"] ?? payload["watch_distance_meters"])
        session.instantPaceSecondsPerKm = doubleValue(payload["instantPaceSecondsPerKm"] ?? payload["instant_pace_seconds_per_km"])
        session.elevationGainMeters = max(0, doubleValue(payload["elevationGainMeters"] ?? payload["elevation_gain_meters"]) ?? 0)
        session.steps = max(0, doubleValue(payload["steps"]) ?? 0)
        session.watchSteps = doubleValue(payload["watchSteps"] ?? payload["watch_steps"])
        session.watchCalories = doubleValue(payload["watchCalories"] ?? payload["watch_calories"])
        session.stepOffset = max(0, doubleValue(payload["stepOffset"] ?? payload["step_offset"]) ?? session.steps)
        session.cadenceStepsPerMinute = doubleValue(payload["cadenceStepsPerMinute"] ?? payload["cadence_steps_per_minute"])
        session.lastCadenceSampleAt = dateValue(payload["lastCadenceSampleAt"] ?? payload["last_cadence_sample_at"])
        session.lastCadenceSampleSteps = max(0, doubleValue(payload["lastCadenceSampleSteps"] ?? payload["last_cadence_sample_steps"]) ?? session.steps)
        session.latestHeartRate = doubleValue(payload["latestHeartRate"] ?? payload["latest_heart_rate"])
        session.heartRateSum = max(0, doubleValue(payload["heartRateSum"] ?? payload["heart_rate_sum"]) ?? 0)
        session.heartRateSampleCount = max(0, intValue(payload["heartRateSampleCount"] ?? payload["heart_rate_sample_count"]) ?? 0)
        session.lastWatchHeartRateTimestamp = max(0, doubleValue(payload["lastWatchHeartRateTimestamp"] ?? payload["last_watch_heart_rate_timestamp"]) ?? 0)
        session.latestWatchMetricsAt = dateValue(payload["latestWatchMetricsAt"] ?? payload["latest_watch_metrics_at"])

        let route = (payload["routeLocations"] as? [[String: Any]]) ?? (payload["route_locations"] as? [[String: Any]])
        if let route = route {
            session.routeLocations = route.compactMap { locationValue($0) }
        }
        session.lastLocation = locationValue(payload["lastLocation"] ?? payload["last_location"]) ?? session.routeLocations.last
        session.lastAltitude = doubleValue(payload["lastAltitude"] ?? payload["last_altitude"]) ?? session.lastLocation?.altitude

        if session.status == .paused && session.pausedAt == nil {
            session.pausedAt = Date()
        }
        if session.status == .running {
            session.pausedAt = nil
        }

        return session
    }

    func persistencePayload() -> [String: Any] {
        var payload: [String: Any] = [
            "id": id,
            "startDate": startDate.timeIntervalSince1970,
            "runType": runType,
            "weightKg": weightKg,
            "status": status.rawValue,
            "activeSegmentStart": activeSegmentStart.timeIntervalSince1970,
            "pausedDuration": pausedDuration,
            "distanceMeters": distanceMeters,
            "elevationGainMeters": elevationGainMeters,
            "steps": steps,
            "stepOffset": stepOffset,
            "lastCadenceSampleSteps": lastCadenceSampleSteps,
            "heartRateSum": heartRateSum,
            "heartRateSampleCount": heartRateSampleCount,
            "lastWatchHeartRateTimestamp": lastWatchHeartRateTimestamp,
            "routeLocations": routeLocations.map { Self.locationPayload($0) }
        ]

        if let pausedAt = pausedAt {
            payload["pausedAt"] = pausedAt.timeIntervalSince1970
        }
        if let endDate = endDate {
            payload["endDate"] = endDate.timeIntervalSince1970
        }
        if let watchDistanceMeters = watchDistanceMeters {
            payload["watchDistanceMeters"] = watchDistanceMeters
        }
        if let instantPaceSecondsPerKm = instantPaceSecondsPerKm {
            payload["instantPaceSecondsPerKm"] = instantPaceSecondsPerKm
        }
        if let watchSteps = watchSteps {
            payload["watchSteps"] = watchSteps
        }
        if let watchCalories = watchCalories {
            payload["watchCalories"] = watchCalories
        }
        if let cadenceStepsPerMinute = cadenceStepsPerMinute {
            payload["cadenceStepsPerMinute"] = cadenceStepsPerMinute
        }
        if let lastCadenceSampleAt = lastCadenceSampleAt {
            payload["lastCadenceSampleAt"] = lastCadenceSampleAt.timeIntervalSince1970
        }
        if let lastLocation = lastLocation {
            payload["lastLocation"] = Self.locationPayload(lastLocation)
        }
        if let lastAltitude = lastAltitude {
            payload["lastAltitude"] = lastAltitude
        }
        if let latestHeartRate = latestHeartRate {
            payload["latestHeartRate"] = latestHeartRate
        }
        if let latestWatchMetricsAt = latestWatchMetricsAt {
            payload["latestWatchMetricsAt"] = latestWatchMetricsAt.timeIntervalSince1970
        }

        return payload
    }

    private static func stringValue(_ value: Any?) -> String? {
        guard let string = value as? String else { return nil }
        let trimmed = string.trimmingCharacters(in: .whitespacesAndNewlines)
        return trimmed.isEmpty ? nil : trimmed
    }

    private static func intValue(_ value: Any?) -> Int? {
        if let int = value as? Int {
            return int
        }
        if let number = value as? NSNumber {
            return number.intValue
        }
        if let string = value as? String {
            return Int(string)
        }
        return nil
    }

    private static func doubleValue(_ value: Any?) -> Double? {
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

    private static func dateValue(_ value: Any?) -> Date? {
        if let date = value as? Date {
            return date
        }
        if let timestamp = doubleValue(value), timestamp > 0 {
            return Date(timeIntervalSince1970: timestamp)
        }
        if let string = value as? String {
            let formatter = ISO8601DateFormatter()
            formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
            if let date = formatter.date(from: string) {
                return date
            }
            return ISO8601DateFormatter().date(from: string)
        }
        return nil
    }

    private static func locationValue(_ value: Any?) -> CLLocation? {
        guard let payload = value as? [String: Any],
              let latitude = doubleValue(payload["lat"] ?? payload["latitude"]),
              let longitude = doubleValue(payload["lng"] ?? payload["lon"] ?? payload["longitude"]),
              latitude >= -90,
              latitude <= 90,
              longitude >= -180,
              longitude <= 180 else {
            return nil
        }

        let timestamp = dateValue(payload["timestamp"]) ?? Date()
        let altitude = doubleValue(payload["altitude"]) ?? 0
        let horizontalAccuracy = max(0, doubleValue(payload["horizontalAccuracy"] ?? payload["horizontal_accuracy"]) ?? 20)
        let verticalAccuracy = max(0, doubleValue(payload["verticalAccuracy"] ?? payload["vertical_accuracy"]) ?? 20)
        let speed = doubleValue(payload["speed"]) ?? -1

        return CLLocation(
            coordinate: CLLocationCoordinate2D(latitude: latitude, longitude: longitude),
            altitude: altitude,
            horizontalAccuracy: horizontalAccuracy,
            verticalAccuracy: verticalAccuracy,
            course: -1,
            speed: speed,
            timestamp: timestamp
        )
    }

    private static func locationPayload(_ location: CLLocation) -> [String: Any] {
        [
            "lat": location.coordinate.latitude,
            "lng": location.coordinate.longitude,
            "timestamp": location.timestamp.timeIntervalSince1970,
            "altitude": location.altitude,
            "horizontalAccuracy": location.horizontalAccuracy,
            "verticalAccuracy": location.verticalAccuracy,
            "speed": location.speed
        ]
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
            setCadenceStepsPerMinute(currentCadenceStepsPerSecond * 60.0)
        } else if let lastCadenceSampleAt = lastCadenceSampleAt {
            let elapsed = date.timeIntervalSince(lastCadenceSampleAt)
            let stepDelta = steps - lastCadenceSampleSteps
            if elapsed >= 0.5, stepDelta >= 1 {
                setCadenceStepsPerMinute(stepDelta / (elapsed / 60.0))
            } else if cadenceStepsPerMinute == nil, elapsedSeconds > 0 {
                setCadenceStepsPerMinute(steps / max(elapsedSeconds / 60.0, 0.1))
            }
        } else if elapsedSeconds > 0 {
            setCadenceStepsPerMinute(steps / max(elapsedSeconds / 60.0, 0.1))
        }

        if lastCadenceSampleAt == nil || date.timeIntervalSince(lastCadenceSampleAt ?? date) >= 0.5 {
            lastCadenceSampleAt = date
            lastCadenceSampleSteps = steps
        }
    }

    func setCadenceStepsPerMinute(_ cadence: Double) {
        guard cadence.isFinite, cadence > 0 else { return }
        let bounded = min(max(cadence, 20), 260)
        if let current = cadenceStepsPerMinute {
            cadenceStepsPerMinute = current * 0.45 + bounded * 0.55
        } else {
            cadenceStepsPerMinute = bounded
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

    func stop(at date: Date = Date()) {
        if status == .paused, let pausedAt = pausedAt {
            pausedDuration += max(0, date.timeIntervalSince(pausedAt))
        }
        status = .stopped
        endDate = date
        stepOffset = steps
        pausedAt = nil
    }

    var hasRecentWatchMetrics: Bool {
        guard let latestWatchMetricsAt = latestWatchMetricsAt else { return false }
        return Date().timeIntervalSince(latestWatchMetricsAt) < 15
    }
}
