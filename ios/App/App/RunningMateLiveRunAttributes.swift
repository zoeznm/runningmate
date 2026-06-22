import ActivityKit
import Foundation

@available(iOS 16.1, *)
struct RunningMateLiveRunAttributes: ActivityAttributes {
    public struct ContentState: Codable, Hashable {
        var status: String
        var statusText: String
        var distanceText: String
        var elapsedText: String
        var paceText: String
        var heartRateText: String
        var cadenceText: String
        var caloriesText: String
        var updatedAt: Date
    }

    var runType: String
    var runTypeText: String
    var startedAt: Date
}
