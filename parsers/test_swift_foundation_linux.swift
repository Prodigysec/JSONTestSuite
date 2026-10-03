// Linux Foundation JSONSerialization adapter. The runner passes one file path.
import Foundation

if CommandLine.arguments.count != 2 {
    exit(2)
}

let data: Data
do {
    data = try Data(contentsOf: URL(fileURLWithPath: CommandLine.arguments[1]))
} catch {
    exit(2)
}

do {
    _ = try JSONSerialization.jsonObject(with: data, options: [.fragmentsAllowed])
    exit(0)
} catch {
    exit(1)
}
