// SPDX-License-Identifier: AGPL-3.0-only
import Cocoa
import CryptoKit

enum RuntimeLocation {
    static var support: URL {
        FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask)[0].appendingPathComponent("E-reader Maker", isDirectory: true)
    }
    static var resources: URL { Bundle.main.resourceURL! }
    static var engine: URL { resources.appendingPathComponent("Engine", isDirectory: true) }
    static var python: URL {
        #if arch(arm64)
        let arch = "arm64"
        #else
        let arch = "x86_64"
        #endif
        let data = (try? Data(contentsOf: engine.appendingPathComponent("requirements-runtime.txt"))) ?? Data()
        let digest = SHA256.hash(data: data).map { String(format: "%02x", $0) }.joined().prefix(12)
        return support.appendingPathComponent("runtime-v1-\(arch)-\(digest)/python/bin/python3")
    }
    static var ready: Bool {
        FileManager.default.isExecutableFile(atPath: python.path) && FileManager.default.fileExists(atPath: python.deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent().appendingPathComponent(".ready").path)
    }
}
