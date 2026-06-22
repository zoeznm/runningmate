import Foundation
import WidgetKit

struct RunningMateCompletedRunRecord: Codable, Hashable {
    let id: String
    let startDate: Date
    let endDate: Date
    let distanceKm: Double
    let durationSeconds: TimeInterval
}

struct RunningMateWeeklyProgress: Hashable {
    let weekStart: Date
    let weekEnd: Date
    let goalCount: Int
    let completedRuns: [RunningMateCompletedRunRecord]

    var completedCount: Int {
        min(completedRuns.count, goalCount)
    }

    var latestRunDate: Date? {
        completedRuns.map(\.endDate).max()
    }
}

enum RunningMateWidgetStore {
    static let appGroupIdentifier = "group.com.myrunningmate.run"
    static let weeklyGoalWidgetKind = "RunMateWeeklyGoalWidget"
    static let weeklyGoalCount = 5

    private static let completedRunsKey = "runningmate.widget.completedRuns.v1"
    private static let minimumRunDurationSeconds: TimeInterval = 60
    private static let minimumRunDistanceKm = 0.05

    static func weeklyProgress(referenceDate: Date = Date()) -> RunningMateWeeklyProgress {
        let interval = weekInterval(containing: referenceDate)
        let runs = loadCompletedRuns()
            .filter { $0.endDate >= interval.start && $0.endDate < interval.end }
            .sorted { $0.endDate < $1.endDate }

        return RunningMateWeeklyProgress(
            weekStart: interval.start,
            weekEnd: interval.end,
            goalCount: weeklyGoalCount,
            completedRuns: runs
        )
    }

    static func sampleProgress(completedCount: Int = 3) -> RunningMateWeeklyProgress {
        let now = Date()
        let interval = weekInterval(containing: now)
        let safeCompletedCount = max(0, min(completedCount, weeklyGoalCount))
        let runs = (0..<safeCompletedCount).map { index in
            let runDate = Calendar.current.date(byAdding: .day, value: index, to: interval.start) ?? now
            return RunningMateCompletedRunRecord(
                id: "sample-\(index)",
                startDate: runDate,
                endDate: runDate.addingTimeInterval(31 * 60),
                distanceKm: 5.0,
                durationSeconds: 31 * 60
            )
        }

        return RunningMateWeeklyProgress(
            weekStart: interval.start,
            weekEnd: interval.end,
            goalCount: weeklyGoalCount,
            completedRuns: runs
        )
    }

    static func recordCompletedRun(
        id: String,
        startDate: Date,
        endDate: Date,
        distanceKm: Double,
        durationSeconds: TimeInterval
    ) {
        guard qualifies(distanceKm: distanceKm, durationSeconds: durationSeconds) else { return }

        var runs = loadCompletedRuns()
        guard !containsDuplicateRun(in: runs, id: id, startDate: startDate, endDate: endDate) else {
            return
        }

        runs.append(RunningMateCompletedRunRecord(
            id: id,
            startDate: startDate,
            endDate: endDate,
            distanceKm: distanceKm,
            durationSeconds: durationSeconds
        ))
        saveCompletedRuns(runs)
        reloadWeeklyGoalWidget()
    }

    static func syncRecentRuns(from workouts: [[String: Any]]) {
        var runs = loadCompletedRuns()
        var didChange = false

        for workout in workouts {
            guard let parsed = record(from: workout),
                  qualifies(distanceKm: parsed.distanceKm, durationSeconds: parsed.durationSeconds),
                  !containsDuplicateRun(in: runs, id: parsed.id, startDate: parsed.startDate, endDate: parsed.endDate) else {
                continue
            }

            runs.append(parsed)
            didChange = true
        }

        guard didChange else { return }
        saveCompletedRuns(runs)
        reloadWeeklyGoalWidget()
    }

    private static func record(from workout: [String: Any]) -> RunningMateCompletedRunRecord? {
        let startDate = dateValue(workout["startDate"] ?? workout["started_at"]) ?? Date()
        let endDate = dateValue(workout["endDate"] ?? workout["ended_at"]) ?? startDate
        let distanceKm = doubleValue(workout["distance_km"]) ?? 0
        let durationSeconds = doubleValue(workout["durationSeconds"] ?? workout["duration_seconds"])
            ?? max(0, endDate.timeIntervalSince(startDate))
        let id = stringValue(workout["id"])
            ?? "\(Int(startDate.timeIntervalSince1970))-\(Int(endDate.timeIntervalSince1970))"

        return RunningMateCompletedRunRecord(
            id: id,
            startDate: startDate,
            endDate: endDate,
            distanceKm: distanceKm,
            durationSeconds: durationSeconds
        )
    }

    private static func qualifies(distanceKm: Double, durationSeconds: TimeInterval) -> Bool {
        distanceKm >= minimumRunDistanceKm || durationSeconds >= minimumRunDurationSeconds
    }

    private static func containsDuplicateRun(
        in runs: [RunningMateCompletedRunRecord],
        id: String,
        startDate: Date,
        endDate: Date
    ) -> Bool {
        runs.contains { run in
            if run.id == id {
                return true
            }

            let startDiff = abs(run.startDate.timeIntervalSince(startDate))
            let endDiff = abs(run.endDate.timeIntervalSince(endDate))
            return startDiff < 180 && endDiff < 180
        }
    }

    private static func loadCompletedRuns() -> [RunningMateCompletedRunRecord] {
        guard let data = defaults.data(forKey: completedRunsKey) else {
            return []
        }

        return (try? JSONDecoder().decode([RunningMateCompletedRunRecord].self, from: data)) ?? []
    }

    private static func saveCompletedRuns(_ runs: [RunningMateCompletedRunRecord]) {
        let cutoff = Calendar.current.date(byAdding: .day, value: -90, to: Date()) ?? Date()
        let prunedRuns = runs
            .filter { $0.endDate >= cutoff }
            .sorted { $0.endDate < $1.endDate }

        guard let data = try? JSONEncoder().encode(prunedRuns) else { return }
        defaults.set(data, forKey: completedRunsKey)
    }

    private static func reloadWeeklyGoalWidget() {
        if #available(iOS 14.0, *) {
            WidgetCenter.shared.reloadTimelines(ofKind: weeklyGoalWidgetKind)
        }
    }

    private static var defaults: UserDefaults {
        UserDefaults(suiteName: appGroupIdentifier) ?? .standard
    }

    private static func weekInterval(containing date: Date) -> (start: Date, end: Date) {
        var calendar = Calendar(identifier: .iso8601)
        calendar.timeZone = .current

        let components = calendar.dateComponents([.yearForWeekOfYear, .weekOfYear], from: date)
        let start = calendar.date(from: components) ?? calendar.startOfDay(for: date)
        let end = calendar.date(byAdding: .day, value: 7, to: start) ?? date.addingTimeInterval(7 * 24 * 60 * 60)
        return (start, end)
    }

    private static func stringValue(_ value: Any?) -> String? {
        if let string = value as? String, !string.isEmpty {
            return string
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
        guard let string = value as? String else { return nil }

        let fractionalFormatter = ISO8601DateFormatter()
        fractionalFormatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        if let date = fractionalFormatter.date(from: string) {
            return date
        }

        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime]
        return formatter.date(from: string)
    }
}
