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
        ScrollView {
            VStack(alignment: .leading, spacing: 10) {
                header
                heartRatePanel
                metricGrid
                controls
            }
            .padding(.horizontal, 10)
            .padding(.vertical, 8)
        }
        .background(RunMateWatchTheme.background)
    }

    private var header: some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack(spacing: 6) {
                Image(systemName: workoutManager.isWorkoutActive ? "figure.run" : "applewatch")
                    .font(.caption.weight(.bold))
                    .foregroundStyle(RunMateWatchTheme.accent)
                Text("RunMate")
                    .font(.headline.weight(.black))
                    .foregroundStyle(.white)
                Spacer(minLength: 2)
            }

            Text(workoutManager.statusText)
                .font(.caption2.weight(.semibold))
                .foregroundStyle(.white.opacity(0.72))
                .lineLimit(2)

            Text(workoutManager.connectionText)
                .font(.system(size: 10, weight: .semibold))
                .foregroundStyle(RunMateWatchTheme.accent.opacity(0.9))
                .lineLimit(1)
        }
    }

    private var heartRatePanel: some View {
        VStack(alignment: .leading, spacing: 5) {
            Text("심박수")
                .font(.caption2.weight(.bold))
                .foregroundStyle(.white.opacity(0.58))
            HStack(alignment: .firstTextBaseline, spacing: 6) {
                Text(workoutManager.heartRateText.replacingOccurrences(of: " bpm", with: ""))
                    .font(.system(size: 36, weight: .black, design: .rounded))
                    .foregroundStyle(.white)
                    .lineLimit(1)
                    .minimumScaleFactor(0.55)
                Text("bpm")
                    .font(.caption.weight(.heavy))
                    .foregroundStyle(RunMateWatchTheme.accent)
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(12)
        .background(RunMateWatchTheme.surface, in: RoundedRectangle(cornerRadius: 16, style: .continuous))
    }

    private var metricGrid: some View {
        LazyVGrid(columns: [
            GridItem(.flexible(), spacing: 6),
            GridItem(.flexible(), spacing: 6)
        ], spacing: 6) {
            RunMateWatchMetric(title: "거리", value: workoutManager.distanceText)
            RunMateWatchMetric(title: "페이스", value: workoutManager.paceText)
            RunMateWatchMetric(title: "시간", value: workoutManager.elapsedText)
            RunMateWatchMetric(title: "칼로리", value: workoutManager.caloriesText)
        }
    }

    private var controls: some View {
        VStack(spacing: 7) {
            if !workoutManager.isWorkoutActive {
                Button {
                    workoutManager.startFromWatch()
                } label: {
                    Label("워치에서 측정 시작", systemImage: "play.fill")
                        .font(.caption.weight(.bold))
                }
                .buttonStyle(.borderedProminent)
                .tint(RunMateWatchTheme.accent)

                Text("iPhone이 없어도 측정하고, 나중에 iPhone 앱을 열면 기록이 동기화돼요.")
                    .font(.system(size: 10, weight: .semibold))
                    .foregroundStyle(.white.opacity(0.58))
                    .multilineTextAlignment(.leading)
            } else {
                HStack(spacing: 7) {
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
        }
    }
}

private struct RunMateWatchMetric: View {
    let title: String
    let value: String

    var body: some View {
        VStack(alignment: .leading, spacing: 3) {
            Text(title)
                .font(.system(size: 10, weight: .bold))
                .foregroundStyle(.white.opacity(0.54))
            Text(value)
                .font(.system(size: 13, weight: .heavy, design: .rounded))
                .foregroundStyle(.white)
                .lineLimit(1)
                .minimumScaleFactor(0.58)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(.vertical, 8)
        .padding(.horizontal, 8)
        .background(.white.opacity(0.08), in: RoundedRectangle(cornerRadius: 10, style: .continuous))
    }
}

private enum RunMateWatchTheme {
    static let background = Color(red: 0.02, green: 0.055, blue: 0.048)
    static let surface = Color.white.opacity(0.09)
    static let accent = Color(red: 0.14, green: 0.84, blue: 0.71)
}
