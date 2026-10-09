// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (c) 2026 Navaneethan and E-reader Maker contributors
import Cocoa
let directory = CommandLine.arguments[1]
try FileManager.default.createDirectory(atPath: directory, withIntermediateDirectories: true)
for points in [16, 32, 128, 256, 512] {
    for scale in [1, 2] {
        let size = points * scale
        let bitmap = NSBitmapImageRep(bitmapDataPlanes: nil, pixelsWide: size, pixelsHigh: size,
            bitsPerSample: 8, samplesPerPixel: 4, hasAlpha: true, isPlanar: false,
            colorSpaceName: .deviceRGB, bytesPerRow: 0, bitsPerPixel: 0)!
        NSGraphicsContext.saveGraphicsState()
        NSGraphicsContext.current = NSGraphicsContext(bitmapImageRep: bitmap)
        let transform = NSAffineTransform(); transform.scale(by: CGFloat(size) / 1024); transform.concat()
        NSColor(calibratedWhite: 0.095, alpha: 1).setFill()
        NSBezierPath(roundedRect: NSRect(x: 30, y: 30, width: 964, height: 964), xRadius: 215, yRadius: 215).fill()
        NSColor(calibratedRed: 0.68, green: 0.76, blue: 1, alpha: 1).setStroke()
        let book = NSBezierPath(); book.lineWidth = 37; book.lineJoinStyle = .round
        book.move(to: NSPoint(x: 512, y: 265)); book.curve(to: NSPoint(x: 235, y: 305), controlPoint1: NSPoint(x: 410, y: 340), controlPoint2: NSPoint(x: 290, y: 335))
        book.line(to: NSPoint(x: 235, y: 725)); book.curve(to: NSPoint(x: 512, y: 680), controlPoint1: NSPoint(x: 350, y: 755), controlPoint2: NSPoint(x: 430, y: 750))
        book.curve(to: NSPoint(x: 789, y: 725), controlPoint1: NSPoint(x: 600, y: 750), controlPoint2: NSPoint(x: 680, y: 755))
        book.line(to: NSPoint(x: 789, y: 305)); book.curve(to: NSPoint(x: 512, y: 265), controlPoint1: NSPoint(x: 690, y: 335), controlPoint2: NSPoint(x: 600, y: 340)); book.close(); book.stroke()
        let spine = NSBezierPath(); spine.lineWidth = 27; spine.move(to: NSPoint(x: 512,y: 280)); spine.line(to: NSPoint(x: 512,y: 672)); spine.stroke()
        NSColor(calibratedRed: 0.84, green: 0.88, blue: 1, alpha: 1).setStroke()
        for y in [450, 535, 620] {
            let line = NSBezierPath(); line.lineWidth = 19; line.lineCapStyle = .round; line.move(to: NSPoint(x: 300,y: y)); line.line(to: NSPoint(x: 420,y: y - 10)); line.stroke()
        }
        NSGraphicsContext.restoreGraphicsState()
        let data = bitmap.representation(using: .png, properties: [:])!
        let suffix = scale == 2 ? "@2x" : ""
        try data.write(to: URL(fileURLWithPath: "\(directory)/icon_\(points)x\(points)\(suffix).png"))
    }
}
