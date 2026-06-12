import Capacitor
import Foundation
import HealthKit

@objc(RunningMateHealthKitPlugin)
class RunningMateHealthKitPlugin: CAPPlugin, CAPBridgedPlugin {
    let identifier = "RunningMateHealthKitPlugin"
    let jsName = "RunningMateHealthKit"
    let pluginMethods: [CAPPluginMethod] = [
        CAPPluginMethod(name: "isAvailable", returnType: CAPPluginReturnPromise),
        CAPPluginMethod(name: "requestAuthorization", returnType: CAPPluginReturnPromise),
        CAPPluginMethod(name: "getRunningWorkouts", returnType: CAPPluginReturnPromise)
    ]

    private let healthStore = HKHealthStore()

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
                    "distance_km": self.round(distanceKm, places: 2),
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

    private func round(_ value: Double, places: Int) -> Double {
        let power = pow(10.0, Double(places))
        return (value * power).rounded() / power
    }
}
