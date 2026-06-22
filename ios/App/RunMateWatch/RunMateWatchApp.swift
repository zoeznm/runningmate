import HealthKit
import SwiftUI
import WatchKit

final class RunMateWatchAppDelegate: NSObject, WKApplicationDelegate {
    func handle(_ workoutConfiguration: HKWorkoutConfiguration) {
        RunMateWatchWorkoutManager.shared.start(runId: nil, runType: "jogging", configuration: workoutConfiguration)
    }
}

@main
struct RunMateWatchApp: App {
    @WKApplicationDelegateAdaptor(RunMateWatchAppDelegate.self) private var appDelegate
    @StateObject private var workoutManager = RunMateWatchWorkoutManager.shared

    var body: some Scene {
        WindowGroup {
            RunMateWatchContentView()
                .environmentObject(workoutManager)
        }
    }
}

struct RunMateWatchContentView: View {
    @EnvironmentObject private var workoutManager: RunMateWatchWorkoutManager

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("RunMate")
                .font(.headline)
                .foregroundStyle(.green)
            Text(workoutManager.statusText)
                .font(.caption)
                .foregroundStyle(.secondary)

            VStack(alignment: .leading, spacing: 4) {
                Text(workoutManager.heartRateText)
                    .font(.system(size: 24, weight: .bold, design: .rounded))
                Text(workoutManager.distanceText)
                    .font(.system(size: 18, weight: .semibold, design: .rounded))
                Text(workoutManager.paceText)
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }

            Spacer(minLength: 4)

            HStack {
                Button {
                    workoutManager.resume()
                } label: {
                    Image(systemName: "play.fill")
                }
                .disabled(!workoutManager.canResume)

                Button {
                    workoutManager.pause()
                } label: {
                    Image(systemName: "pause.fill")
                }
                .disabled(!workoutManager.canPause)

                Button(role: .destructive) {
                    workoutManager.stop()
                } label: {
                    Image(systemName: "stop.fill")
                }
                .disabled(!workoutManager.canStop)
            }
            .buttonStyle(.bordered)
            .labelStyle(.iconOnly)
        }
        .padding()
    }
}
