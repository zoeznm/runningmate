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
        completion(RunMateWeeklyGoalEntry(date: Date(), progress: RunningMateWidgetStore.weeklyProgress()))
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
        VStack(spacing: 6) {
            statusLabel(font: .system(size: 13, weight: .bold, design: .rounded))
            RunMateGoalCircles(progress: entry.progress, size: 17, checkSize: 7, spacing: 5)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    private var smallView: some View {
        VStack(spacing: 12) {
            statusLabel(font: .system(size: 17, weight: .black, design: .rounded))
            RunMateGoalCircles(progress: entry.progress, size: 23, checkSize: 10, spacing: 7)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .padding()
    }

    private func statusLabel(font: Font) -> some View {
        Text(statusText)
            .font(font)
            .foregroundStyle(RunMateWeeklyGoalTheme.foreground)
            .lineLimit(1)
            .minimumScaleFactor(0.72)
            .multilineTextAlignment(.center)
            .frame(maxWidth: .infinity)
    }

    private var circularView: some View {
        ZStack {
            Circle()
                .fill(RunMateWeeklyGoalTheme.background)
            RunMateGoalCircles(progress: entry.progress, size: 7, checkSize: 4, spacing: 2)
                .frame(maxWidth: .infinity, maxHeight: .infinity)
                .padding(.horizontal, 6)
        }
    }

    private var statusText: String {
        switch entry.progress.completedCount {
        case 0:
            return "이번주도 러닝 시작!"
        case 1:
            return "1회 러닝 완료!"
        case 2:
            return "2회 러닝 완료!"
        case 3:
            return "3회 러닝 완료!"
        case 4:
            return "4회 러닝 완료!"
        default:
            return "이번주 러닝 완료!"
        }
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
                .fill(isCompleted ? RunMateWeeklyGoalTheme.accent : RunMateWeeklyGoalTheme.foreground.opacity(0.10))
            Circle()
                .stroke(isCompleted ? RunMateWeeklyGoalTheme.accent : RunMateWeeklyGoalTheme.foreground.opacity(0.38), lineWidth: 1.2)
            if isCompleted {
                Image(systemName: "checkmark")
                    .font(.system(size: checkSize, weight: .black))
                    .foregroundStyle(RunMateWeeklyGoalTheme.checkmark)
            }
        }
        .frame(width: size, height: size)
    }
}

private enum RunMateWeeklyGoalTheme {
    static let background = Color(red: 36 / 255, green: 214 / 255, blue: 181 / 255)
    static let foreground = Color.black
    static let accent = Color.black
    static let checkmark = Color.white
}

private extension View {
    @ViewBuilder
    func runMateWidgetContainerBackground(for family: WidgetFamily) -> some View {
        if #available(iOSApplicationExtension 17.0, *) {
            containerBackground(for: .widget) {
                RunMateWeeklyGoalTheme.background
            }
        } else {
            background(RunMateWeeklyGoalTheme.background)
        }
    }
}
