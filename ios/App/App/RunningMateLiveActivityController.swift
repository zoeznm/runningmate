import ActivityKit
import Foundation

@available(iOS 16.1, *)
final class RunningMateLiveActivityController {
    static let shared = RunningMateLiveActivityController()

    private var currentActivity: Activity<RunningMateLiveRunAttributes>?
    private var lastUpdateAt: Date = .distantPast
    private let minimumUpdateInterval: TimeInterval = 3

    private init() { }

    func start(with payload: [String: Any]) {
        guard ActivityAuthorizationInfo().areActivitiesEnabled else { return }

        if currentActivity == nil {
            currentActivity = Activity<RunningMateLiveRunAttributes>.activities.first
        }
        if currentActivity != nil {
            update(with: payload, force: true)
            return
        }

        let runType = stringValue(payload["run_type"], defaultValue: "jogging")
        let startedAt = dateValue(payload["started_at"]) ?? Date()
        let attributes = RunningMateLiveRunAttributes(
            runType: runType,
            runTypeText: runTypeText(runType),
            startedAt: startedAt
        )
        let state = contentState(from: payload)

        do {
            currentActivity = try Activity.request(attributes: attributes, contentState: state, pushType: nil)
            lastUpdateAt = Date()
        } catch {
            currentActivity = nil
        }
    }

    func update(with payload: [String: Any], force: Bool = false) {
        guard ActivityAuthorizationInfo().areActivitiesEnabled else { return }

        if currentActivity == nil {
            currentActivity = Activity<RunningMateLiveRunAttributes>.activities.first
        }
        guard let activity = currentActivity else { return }

        let status = stringValue(payload["status"], defaultValue: "running")
        let shouldUpdate = force
            || status != "running"
            || Date().timeIntervalSince(lastUpdateAt) >= minimumUpdateInterval
        guard shouldUpdate else { return }

        lastUpdateAt = Date()
        let state = contentState(from: payload)
        Task {
            await activity.update(using: state)
        }
    }

    func end(with payload: [String: Any]) {
        let activity = currentActivity ?? Activity<RunningMateLiveRunAttributes>.activities.first
        currentActivity = nil
        lastUpdateAt = .distantPast

        guard let activity = activity else { return }
        let state = contentState(from: payload)
        Task {
            await activity.end(using: state, dismissalPolicy: .default)
        }
    }

    private func contentState(from payload: [String: Any]) -> RunningMateLiveRunAttributes.ContentState {
        let status = stringValue(payload["status"], defaultValue: "running")
        let distanceKm = doubleValue(payload["distance_km"])
        let elapsedText = stringValue(payload["duration"], defaultValue: "00:00:00")
        let pace = stringValue(payload["avg_pace"], defaultValue: "-")
        let heartRate = intValue(payload["heart_rate"]) ?? intValue(payload["avg_heart_rate"])
        let cadence = intValue(payload["cadence"])
        let calories = intValue(payload["calories"])

        return RunningMateLiveRunAttributes.ContentState(
            status: status,
            statusText: statusText(status),
            distanceText: String(format: "%.2f km", distanceKm),
            elapsedText: elapsedText,
            paceText: pace == "-" ? "--" : "\(pace) /km",
            heartRateText: heartRate.map { "\($0) bpm" } ?? "--",
            cadenceText: cadence.map { "\($0) spm" } ?? "--",
            caloriesText: calories.map { "\($0) kcal" } ?? "--",
            updatedAt: Date()
        )
    }

    private func statusText(_ status: String) -> String {
        switch status {
        case "paused":
            return "일시정지"
        case "stopped":
            return "러닝 완료"
        default:
            return "러닝 중"
        }
    }

    private func runTypeText(_ runType: String) -> String {
        switch runType {
        case "long":
            return "롱런"
        case "interval":
            return "인터벌"
        case "tempo":
            return "템포런"
        case "race":
            return "레이스"
        case "recovery":
            return "회복런"
        default:
            return "조깅"
        }
    }

    private func stringValue(_ value: Any?, defaultValue: String) -> String {
        if let string = value as? String, !string.isEmpty {
            return string
        }
        return defaultValue
    }

    private func intValue(_ value: Any?) -> Int? {
        if let int = value as? Int {
            return int
        }
        if let double = value as? Double, double.isFinite {
            return Int(round(double))
        }
        if let string = value as? String, let int = Int(string) {
            return int
        }
        return nil
    }

    private func doubleValue(_ value: Any?) -> Double {
        if let double = value as? Double, double.isFinite {
            return double
        }
        if let int = value as? Int {
            return Double(int)
        }
        if let string = value as? String, let double = Double(string) {
            return double
        }
        return 0
    }

    private func dateValue(_ value: Any?) -> Date? {
        guard let string = value as? String else { return nil }
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        return formatter.date(from: string)
    }
}
