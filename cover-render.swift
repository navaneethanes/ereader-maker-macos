// SPDX-License-Identifier: AGPL-3.0-only
import Cocoa
@main enum CoverRenderer {
    static func main() throws {
        let args=CommandLine.arguments
        guard args.count >= 4, let design=Int(args[2]), (0..<100).contains(design), args[1].count <= 240 else {
            fputs("Usage: cover-render TITLE DESIGN OUTPUT [CUSTOM_IMAGE]\n",stderr);exit(1)
        }
        var custom:NSImage?
        if args.count>4 {
            guard let image=NSImage(contentsOfFile:args[4]) else {fputs("Cannot read the selected cover image.\n",stderr);exit(1)}
            custom=image
        }
        guard let data=CoverArt.jpeg(CoverArt.render(title:args[1],design:design,custom:custom)) else {exit(1)}
        try data.write(to:URL(fileURLWithPath:args[3]),options:.atomic)
    }
}
