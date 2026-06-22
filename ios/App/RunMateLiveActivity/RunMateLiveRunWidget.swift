import ActivityKit
import SwiftUI
import WidgetKit

struct RunMateLiveRunWidget: Widget {
    var body: some WidgetConfiguration {
        ActivityConfiguration(for: RunningMateLiveRunAttributes.self) { context in
            RunMateLiveRunLockView(context: context)
                .activityBackgroundTint(RunMateLiveRunTheme.background)
                .activitySystemActionForegroundColor(.white)
        } dynamicIsland: { context in
            DynamicIsland {
                DynamicIslandExpandedRegion(.leading) {
                    RunMateIslandMetric(title: "거리", value: context.state.distanceText)
                }
                DynamicIslandExpandedRegion(.trailing) {
                    RunMateIslandMetric(title: "시간", value: context.state.elapsedText)
                }
                DynamicIslandExpandedRegion(.center) {
                    HStack(spacing: 6) {
                        Image(systemName: context.state.status == "paused" ? "pause.fill" : "figure.run")
                        Text(context.state.statusText)
                    }
                    .font(.caption.weight(.bold))
                    .foregroundStyle(RunMateLiveRunTheme.accent)
                }
                DynamicIslandExpandedRegion(.bottom) {
                    HStack(spacing: 12) {
                        RunMateCompactMetric(icon: "speedometer", text: context.state.paceText)
                        RunMateCompactMetric(icon: "heart.fill", text: context.state.heartRateText)
                        RunMateCompactMetric(icon: "flame.fill", text: context.state.caloriesText)
                    }
                    .foregroundStyle(.white.opacity(0.86))
                }
            } compactLeading: {
                Image(systemName: context.state.status == "paused" ? "pause.fill" : "figure.run")
                    .foregroundStyle(RunMateLiveRunTheme.accent)
            } compactTrailing: {
                Text(context.state.distanceText.replacingOccurrences(of: " km", with: ""))
                    .font(.caption2.weight(.bold))
                    .foregroundStyle(.white)
            } minimal: {
                Image(systemName: "figure.run")
                    .foregroundStyle(RunMateLiveRunTheme.accent)
            }
            .keylineTint(RunMateLiveRunTheme.accent)
        }
    }
}

private struct RunMateLiveRunLockView: View {
    let context: ActivityViewContext<RunningMateLiveRunAttributes>

    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            HStack(alignment: .center, spacing: 10) {
                ZStack {
                    RoundedRectangle(cornerRadius: 12, style: .continuous)
                        .fill(RunMateLiveRunTheme.accent.opacity(0.16))
                    Image(systemName: context.state.status == "paused" ? "pause.fill" : "figure.run")
                        .font(.system(size: 18, weight: .bold))
                        .foregroundStyle(RunMateLiveRunTheme.accent)
                }
                .frame(width: 42, height: 42)

                VStack(alignment: .leading, spacing: 2) {
                    Text("RunMate")
                        .font(.headline.weight(.black))
                        .foregroundStyle(.white)
                    Text("\(context.attributes.runTypeText) · \(context.state.statusText)")
                        .font(.caption.weight(.semibold))
                        .foregroundStyle(.white.opacity(0.68))
                }

                Spacer(minLength: 10)

                Text(context.state.updatedAt, style: .time)
                    .font(.caption2.weight(.semibold))
                    .foregroundStyle(.white.opacity(0.52))
            }

            HStack(alignment: .bottom, spacing: 18) {
                VStack(alignment: .leading, spacing: 4) {
                    Text("거리")
                        .font(.caption2.weight(.bold))
                        .foregroundStyle(.white.opacity(0.56))
                    Text(context.state.distanceText)
                        .font(.system(size: 31, weight: .black, design: .rounded))
                        .foregroundStyle(.white)
                        .minimumScaleFactor(0.78)
                }

                VStack(alignment: .leading, spacing: 4) {
                    Text("시간")
                        .font(.caption2.weight(.bold))
                        .foregroundStyle(.white.opacity(0.56))
                    Text(context.state.elapsedText)
                        .font(.system(size: 24, weight: .heavy, design: .rounded))
                        .foregroundStyle(RunMateLiveRunTheme.accent)
                        .minimumScaleFactor(0.78)
                }
            }

            HStack(spacing: 8) {
                RunMateLockMetric(title: "페이스", value: context.state.paceText)
                RunMateLockMetric(title: "심박", value: context.state.heartRateText)
                RunMateLockMetric(title: "케이던스", value: context.state.cadenceText)
                RunMateLockMetric(title: "칼로리", value: context.state.caloriesText)
            }
        }
        .padding(18)
    }
}

private struct RunMateLockMetric: View {
    let title: String
    let value: String

    var body: some View {
        VStack(alignment: .leading, spacing: 3) {
            Text(title)
                .font(.caption2.weight(.bold))
                .foregroundStyle(.white.opacity(0.52))
            Text(value)
                .font(.caption.weight(.heavy))
                .foregroundStyle(.white.opacity(0.92))
                .lineLimit(1)
                .minimumScaleFactor(0.65)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(.vertical, 9)
        .padding(.horizontal, 8)
        .background(.white.opacity(0.075), in: RoundedRectangle(cornerRadius: 10, style: .continuous))
    }
}

private struct RunMateIslandMetric: View {
    let title: String
    let value: String

    var body: some View {
        VStack(alignment: .leading, spacing: 2) {
            Text(title)
                .font(.caption2.weight(.bold))
                .foregroundStyle(.white.opacity(0.56))
            Text(value)
                .font(.headline.weight(.black))
                .foregroundStyle(.white)
                .lineLimit(1)
                .minimumScaleFactor(0.72)
        }
    }
}

private struct RunMateCompactMetric: View {
    let icon: String
    let text: String

    var body: some View {
        HStack(spacing: 4) {
            Image(systemName: icon)
                .font(.caption2.weight(.bold))
            Text(text)
                .font(.caption2.weight(.bold))
                .lineLimit(1)
                .minimumScaleFactor(0.7)
        }
    }
}

private enum RunMateLiveRunTheme {
    static let background = Color(red: 0.02, green: 0.055, blue: 0.048)
    static let accent = Color(red: 0.14, green: 0.84, blue: 0.71)
}
