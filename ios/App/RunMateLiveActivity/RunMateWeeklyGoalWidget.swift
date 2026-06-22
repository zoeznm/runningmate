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
        Group {
            switch family {
            case .accessoryCircular:
                circularView
            case .accessoryRectangular:
                rectangularView
            default:
                smallView
            }
        }
        .runMateWidgetContainerBackground(for: family)
    }

    private var rectangularView: some View {
        RunMateGoalCircles(progress: entry.progress, size: 19, checkSize: 8, spacing: 5)
            .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    private var circularView: some View {
        ZStack {
            AccessoryWidgetBackground()
            RunMateGoalCircles(progress: entry.progress, size: 7, checkSize: 4, spacing: 2)
                .frame(maxWidth: .infinity, maxHeight: .infinity)
                .padding(.horizontal, 6)
        }
    }

    private var smallView: some View {
        RunMateGoalCircles(progress: entry.progress, size: 23, checkSize: 10, spacing: 7)
            .frame(maxWidth: .infinity, maxHeight: .infinity)
            .padding()
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
    func runMateWidgetContainerBackground(for family: WidgetFamily) -> some View {
        if #available(iOSApplicationExtension 17.0, *) {
            containerBackground(for: .widget) {
                if family == .systemSmall {
                    RunMateWeeklyGoalTheme.background
                } else {
                    Color.clear
                }
            }
        } else if family == .systemSmall {
            background(RunMateWeeklyGoalTheme.background)
        } else {
            self
        }
    }
}
