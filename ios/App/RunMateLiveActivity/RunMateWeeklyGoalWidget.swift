import SwiftUI
import WidgetKit

struct RunMateWeeklyGoalWidget: Widget {
    static let kind = RunningMateWidgetStore.weeklyGoalWidgetKind

    var body: some WidgetConfiguration {
        StaticConfiguration(kind: Self.kind, provider: RunMateWeeklyGoalProvider()) { entry in
            RunMateWeeklyGoalView(entry: entry)
        }
        .configurationDisplayName("RunMate 주간 목표")
        .description("이번 주 러닝 5회 목표를 잠금화면에서 체크해요.")
        .supportedFamilies([.accessoryRectangular, .accessoryCircular, .systemSmall])
    }
}

private struct RunMateWeeklyGoalProvider: TimelineProvider {
    func placeholder(in context: Context) -> RunMateWeeklyGoalEntry {
        RunMateWeeklyGoalEntry(date: Date(), progress: RunningMateWidgetStore.sampleProgress())
    }

    func getSnapshot(in context: Context, completion: @escaping (RunMateWeeklyGoalEntry) -> Void) {
        let progress = context.isPreview
            ? RunningMateWidgetStore.sampleProgress()
            : RunningMateWidgetStore.weeklyProgress()
        completion(RunMateWeeklyGoalEntry(date: Date(), progress: progress))
    }

    func getTimeline(in context: Context, completion: @escaping (Timeline<RunMateWeeklyGoalEntry>) -> Void) {
        let now = Date()
        let entry = RunMateWeeklyGoalEntry(date: now, progress: RunningMateWidgetStore.weeklyProgress(referenceDate: now))
        completion(Timeline(entries: [entry], policy: .after(nextRefreshDate(after: now))))
    }

    private func nextRefreshDate(after date: Date) -> Date {
        Calendar.current.nextDate(
            after: date,
            matching: DateComponents(hour: 0, minute: 5),
            matchingPolicy: .nextTime
        ) ?? date.addingTimeInterval(60 * 60)
    }
}

private struct RunMateWeeklyGoalEntry: TimelineEntry {
    let date: Date
    let progress: RunningMateWeeklyProgress
}

private struct RunMateWeeklyGoalView: View {
    @Environment(\.widgetFamily) private var family
    let entry: RunMateWeeklyGoalEntry

    var body: some View {
        switch family {
        case .accessoryCircular:
            circularView
        case .accessoryRectangular:
            rectangularView
        default:
            smallView
        }
    }

    private var rectangularView: some View {
        HStack(spacing: 10) {
            VStack(alignment: .leading, spacing: 2) {
                Text("이번 주 러닝")
                    .font(.caption2.weight(.bold))
                    .foregroundStyle(.secondary)
                Text("\(entry.progress.completedCount)/\(entry.progress.goalCount)")
                    .font(.system(size: 24, weight: .black, design: .rounded))
                    .foregroundStyle(.primary)
                    .minimumScaleFactor(0.8)
            }

            Spacer(minLength: 4)

            RunMateGoalCircles(progress: entry.progress, size: 18, checkSize: 9, spacing: 4)
        }
        .padding(.vertical, 2)
    }

    private var circularView: some View {
        ZStack {
            AccessoryWidgetBackground()
            VStack(spacing: 3) {
                Text("\(entry.progress.completedCount)/\(entry.progress.goalCount)")
                    .font(.system(size: 17, weight: .black, design: .rounded))
                    .minimumScaleFactor(0.7)

                RunMateGoalCircles(progress: entry.progress, size: 6, checkSize: 4, spacing: 1)
            }
            .padding(3)
        }
    }

    private var smallView: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: "figure.run")
                    .font(.system(size: 18, weight: .bold))
                    .foregroundStyle(RunMateWeeklyGoalTheme.accent)
                Spacer()
                Text("\(entry.progress.completedCount)/\(entry.progress.goalCount)")
                    .font(.system(size: 20, weight: .black, design: .rounded))
            }

            VStack(alignment: .leading, spacing: 8) {
                Text("이번 주 러닝")
                    .font(.headline.weight(.black))
                    .lineLimit(1)
                RunMateGoalCircles(progress: entry.progress, size: 21, checkSize: 10, spacing: 6)
            }

            Spacer(minLength: 0)

            Text(statusText)
                .font(.caption2.weight(.semibold))
                .foregroundStyle(.secondary)
                .lineLimit(1)
        }
        .padding()
        .runMateWidgetBackground()
    }

    private var statusText: String {
        let remaining = max(0, entry.progress.goalCount - entry.progress.completedCount)
        if remaining == 0 {
            return "주간 목표 완료"
        }
        return "\(remaining)번 더 뛰면 완료"
    }
}

private struct RunMateGoalCircles: View {
    let progress: RunningMateWeeklyProgress
    let size: CGFloat
    let checkSize: CGFloat
    let spacing: CGFloat

    var body: some View {
        HStack(spacing: spacing) {
            ForEach(0..<progress.goalCount, id: \.self) { index in
                RunMateGoalCircle(
                    isCompleted: index < progress.completedCount,
                    size: size,
                    checkSize: checkSize
                )
            }
        }
        .accessibilityLabel("이번 주 러닝 \(progress.completedCount)회 완료, 목표 \(progress.goalCount)회")
    }
}

private struct RunMateGoalCircle: View {
    let isCompleted: Bool
    let size: CGFloat
    let checkSize: CGFloat

    var body: some View {
        ZStack {
            Circle()
                .fill(isCompleted ? RunMateWeeklyGoalTheme.accent : Color.primary.opacity(0.08))
            Circle()
                .stroke(isCompleted ? RunMateWeeklyGoalTheme.accent : Color.primary.opacity(0.34), lineWidth: 1.2)
            if isCompleted {
                Image(systemName: "checkmark")
                    .font(.system(size: checkSize, weight: .black))
                    .foregroundStyle(.black)
            }
        }
        .frame(width: size, height: size)
    }
}

private enum RunMateWeeklyGoalTheme {
    static let background = Color(red: 0.02, green: 0.055, blue: 0.048)
    static let accent = Color(red: 0.14, green: 0.84, blue: 0.71)
}

private extension View {
    @ViewBuilder
    func runMateWidgetBackground() -> some View {
        if #available(iOSApplicationExtension 17.0, *) {
            containerBackground(RunMateWeeklyGoalTheme.background, for: .widget)
        } else {
            background(RunMateWeeklyGoalTheme.background)
        }
    }
}
