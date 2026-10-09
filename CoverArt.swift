// SPDX-License-Identifier: AGPL-3.0-only
// Original decorative artwork produced by this file is dedicated under CC0-1.0.
import Cocoa

struct CoverArt {
    static let themes = ["Wildflowers", "Fern", "Rose", "Lotus", "Leaves", "Butterfly", "Fox", "Owl", "Whale", "Cat", "Mountains", "Waves", "Moon", "Constellation", "Orbit", "Circuits", "Geometry", "Arches", "Sunrise", "Meadow"]
    static let palettes = ["Ivory & ink", "Forest", "Terracotta", "Plum", "Midnight"]
    static func color(_ hex: UInt32) -> NSColor {
        NSColor(srgbRed: CGFloat((hex >> 16) & 255)/255, green: CGFloat((hex >> 8) & 255)/255, blue: CGFloat(hex & 255)/255, alpha: 1)
    }
    static func suggested(_ title: String) -> Int {
        Int.random(in: 0..<100)
    }
    static func name(_ index: Int) -> String { themes[(index % 100)/5] + " · " + palettes[index % 5] }
    static func render(title: String, design: Int, custom: NSImage? = nil, width: Int = 1200) -> NSImage {
        let bitmap = NSBitmapImageRep(bitmapDataPlanes:nil, pixelsWide:width, pixelsHigh:width*3/2, bitsPerSample:8, samplesPerPixel:4, hasAlpha:true, isPlanar:false, colorSpaceName:.deviceRGB, bytesPerRow:0, bitsPerPixel:0)!
        NSGraphicsContext.saveGraphicsState()
        NSGraphicsContext.current = NSGraphicsContext(bitmapImageRep:bitmap)
        NSGraphicsContext.current?.imageInterpolation = .high
        let scale = NSAffineTransform(); scale.scale(by:CGFloat(width)/600); scale.concat()
        let palette = ((design % 5)+5)%5
        let backgrounds: [UInt32] = [0xF5F0E6,0xE9EEE4,0xF5E6D9,0xF0E7EB,0x172D3C]
        let inks: [UInt32] = [0x203446,0x193D32,0x663527,0x4D2A47,0xF2E8CE]
        let accents: [UInt32] = [0x9A7450,0x718066,0xA85439,0x9F738F,0xC6A879]
        let bg=color(backgrounds[palette]), ink=color(inks[palette]), accent=color(accents[palette])
        bg.setFill(); NSRect(x:0,y:0,width:600,height:900).fill()
        func line(_ pts: [(CGFloat,CGFloat)], _ thickness: CGFloat = 2, _ c: NSColor? = nil, close: Bool = false, fill: Bool = false) {
            let path=NSBezierPath(); path.lineWidth=thickness; path.lineCapStyle = .round; path.lineJoinStyle = .round
            guard let first=pts.first else{return}; path.move(to:NSPoint(x:first.0,y:first.1))
            for p in pts.dropFirst(){path.line(to:NSPoint(x:p.0,y:p.1))}
            if close{path.close()}; (c ?? ink).setStroke(); (c ?? ink).setFill(); if fill{path.fill()}else{path.stroke()}
        }
        func oval(_ x:CGFloat,_ y:CGFloat,_ w:CGFloat,_ h:CGFloat,_ c:NSColor?=nil,fill:Bool=false) {
            let p=NSBezierPath(ovalIn:NSRect(x:x,y:y,width:w,height:h));p.lineWidth=2;(c ?? ink).setStroke();(c ?? ink).setFill();if fill{p.fill()}else{p.stroke()}
        }
        func curve(_ a:NSPoint,_ b:NSPoint,_ c:NSPoint,_ d:NSPoint,_ col:NSColor?=nil,_ width:CGFloat=2){let p=NSBezierPath();p.move(to:a);p.curve(to:d,controlPoint1:b,controlPoint2:c);p.lineWidth=width;(col ?? ink).setStroke();p.stroke()}
        func leaf(_ x:CGFloat,_ y:CGFloat,_ dx:CGFloat,_ dy:CGFloat,_ col:NSColor?=nil){let p=NSBezierPath();p.move(to:NSPoint(x:x,y:y));p.curve(to:NSPoint(x:x+dx,y:y+dy),controlPoint1:NSPoint(x:x+dx*0.12-dy*0.27,y:y+dy*0.15+dx*0.27),controlPoint2:NSPoint(x:x+dx*0.7-dy*0.22,y:y+dy*0.7+dx*0.22));p.curve(to:NSPoint(x:x,y:y),controlPoint1:NSPoint(x:x+dx*0.65+dy*0.25,y:y+dy*0.7-dx*0.25),controlPoint2:NSPoint(x:x+dx*0.25+dy*0.18,y:y+dy*0.2-dx*0.18));(col ?? ink).setFill();p.fill()}
        func flower(_ x:CGFloat,_ y:CGFloat,_ r:CGFloat,_ petals:Int=8){for n in 0..<petals{let a=CGFloat(n)*2*CGFloat.pi/CGFloat(petals);leaf(x,y,cos(a)*r,sin(a)*r,accent)};oval(x-7,y-7,14,14,ink,fill:true)}
        // A restrained frame remains visible on monochrome e-ink screens.
        line([(34,34),(566,34),(566,866),(34,866)],1,accent,close:true)
        line([(50,52),(550,52)],1,accent)
        if let image=custom {
            let box=NSRect(x:70,y:180,width:460,height:380)
            let ratio=min(box.width/max(1,image.size.width),box.height/max(1,image.size.height))
            let size=NSSize(width:image.size.width*ratio,height:image.size.height*ratio)
            image.draw(in:NSRect(x:box.midX-size.width/2,y:box.midY-size.height/2,width:size.width,height:size.height))
            line([(70,160),(530,160)],1,accent)
        } else {
            let theme=((design % 100)+100)%100/5
            switch theme {
            case 0,19:
                for (i,x) in [CGFloat(160),240,325,420].enumerated(){let y=CGFloat([390,500,435,465][i]);curve(NSPoint(x:300,y:155),NSPoint(x:x+35,y:250),NSPoint(x:x-30,y:y-90),NSPoint(x:x,y:y));flower(x,y,CGFloat([47,60,48,38][i]),theme==19 ? 5:8);leaf(x+8,y-90,55,35);leaf(x-3,y-110,-42,40,accent)}
            case 1,4:
                for j in 0..<3 {let base=CGFloat(230+j*55); let tip=CGFloat(485+j*23);curve(NSPoint(x:300,y:155),NSPoint(x:base,y:235),NSPoint(x:base-30,y:360),NSPoint(x:base,y:tip));for i in 0..<(theme==4 ? 4:7){let y=CGFloat(235+i*(theme==4 ? 65:37));let span=CGFloat(theme==4 ? 112-i*14:72-i*6);leaf(base,y,-span,30, j==1 ? ink:accent);leaf(base+2,y+12,span,36,j==1 ? ink:accent)}}
            case 2:
                curve(NSPoint(x:290,y:160),NSPoint(x:345,y:240),NSPoint(x:270,y:355),NSPoint(x:300,y:435));leaf(296,280,-98,46);leaf(310,245,86,60,accent)
                for i in (0..<7).reversed(){let radius=CGFloat(20+i*9);let a=CGFloat(i)*0.7;oval(300-radius+sin(a)*12,435-radius+cos(a)*9,radius*2,radius*1.65,i%2==0 ? ink:accent)}
            case 3:
                line([(135,215),(465,215)],1,accent);for i in -3...3{let a=CGFloat(i)*0.37;leaf(300,270,sin(a)*170,cos(a)*215,i%2==0 ? ink:accent)};oval(200,243,200,23,accent)
            case 5:
                leaf(300,350,-175,160,accent);leaf(300,350,175,160,accent);leaf(300,350,-135,-115);leaf(300,350,135,-115)
                line([(300,245),(300,455)],6);curve(NSPoint(x:300,y:445),NSPoint(x:280,y:515),NSPoint(x:255,y:490),NSPoint(x:255,y:480));curve(NSPoint(x:300,y:445),NSPoint(x:320,y:515),NSPoint(x:345,y:490),NSPoint(x:345,y:480))
                for dx in [-1,1]{oval(300+CGFloat(dx)*95-20,405,40,45,bg);oval(300+CGFloat(dx)*72-12,295,24,30,bg)}
            case 6:
                line([(300,235),(155,435),(165,545),(265,450),(335,450),(435,545),(445,435)],3,ink,close:true,fill:true)
                line([(300,257),(179,416),(260,389)],1,bg,close:true,fill:true);line([(300,257),(421,416),(340,389)],1,bg,close:true,fill:true)
                line([(185,508),(196,445),(246,455)],1,accent,close:true,fill:true);line([(415,508),(404,445),(354,455)],1,accent,close:true,fill:true)
                oval(248,403,10,14,bg,fill:true);oval(342,403,10,14,bg,fill:true);line([(287,276),(313,276),(300,262)],1,ink,close:true,fill:true)
            case 7:
                oval(183,210,234,315,ink,fill:true);line([(190,460),(195,555),(265,497)],1,ink,close:true,fill:true);line([(410,460),(405,555),(335,497)],1,ink,close:true,fill:true)
                for x in [CGFloat(245),355]{oval(x-47,395,94,100,bg,fill:true);oval(x-15,424,30,38,ink,fill:true)}
                line([(283,405),(317,405),(300,379)],1,accent,close:true,fill:true)
                for y in stride(from:260,through:350,by:30){for x in stride(from:240,through:360,by:40){line([(CGFloat(x)-7,CGFloat(y)+7),(CGFloat(x),CGFloat(y)),(CGFloat(x)+7,CGFloat(y)+7)],2,bg)}}
            case 8:
                let p=NSBezierPath();p.move(to:NSPoint(x:130,y:340));p.curve(to:NSPoint(x:420,y:300),controlPoint1:NSPoint(x:145,y:525),controlPoint2:NSPoint(x:355,y:450));p.curve(to:NSPoint(x:487,y:430),controlPoint1:NSPoint(x:450,y:315),controlPoint2:NSPoint(x:428,y:395));p.line(to:NSPoint(x:505,y:495));p.line(to:NSPoint(x:454,y:465));p.line(to:NSPoint(x:400,y:500));p.line(to:NSPoint(x:424,y:420));p.curve(to:NSPoint(x:130,y:340),controlPoint1:NSPoint(x:405,y:175),controlPoint2:NSPoint(x:165,y:170));ink.setFill();p.fill();oval(180,348,10,10,bg,fill:true);for i in 0..<3{line([(170,CGFloat(270+i*13)),(295,CGFloat(245+i*13))],2,accent)};curve(NSPoint(x:222,y:442),NSPoint(x:210,y:528),NSPoint(x:190,y:550),NSPoint(x:174,y:523),accent);curve(NSPoint(x:224,y:440),NSPoint(x:235,y:530),NSPoint(x:258,y:541),NSPoint(x:275,y:524),accent)
            case 9:
                oval(205,190,190,265,ink,fill:true);oval(210,375,180,145,ink,fill:true);line([(215,455),(213,555),(274,500)],1,ink,close:true,fill:true);line([(385,455),(387,555),(326,500)],1,ink,close:true,fill:true);for x in [CGFloat(263),337]{oval(x-14,448,28,11,bg,fill:true)};line([(291,425),(309,425),(300,416)],1,accent,close:true,fill:true);curve(NSPoint(x:352,y:217),NSPoint(x:485,y:130),NSPoint(x:478,y:340),NSPoint(x:430,y:326),ink,16)
            case 10:
                oval(354,445,85,85,accent,fill:true);line([(100,215),(247,495),(360,310),(420,420),(520,215)],2,ink,close:true);line([(180,345),(247,495),(309,395),(266,412),(242,390),(225,414)],2,ink);for i in 0..<5{line([(100,CGFloat(180-i*12)),(520,CGFloat(180-i*12))],1,accent)}
            case 11:
                for i in 0..<10{let y=CGFloat(210+i*28);curve(NSPoint(x:95,y:y),NSPoint(x:200,y:y+100),NSPoint(x:400,y:y-100),NSPoint(x:505,y:y),i%3==0 ? accent:ink,2)}
            case 12:
                oval(183,280,234,234,ink,fill:true);oval(243,320,194,210,bg,fill:true);for (x,y) in [(135,435),(435,270),(390,540),(178,240)]{line([(CGFloat(x)-8,CGFloat(y)),(CGFloat(x)+8,CGFloat(y))],2,accent);line([(CGFloat(x),CGFloat(y)-8),(CGFloat(x),CGFloat(y)+8)],2,accent)}
            case 13:
                let pts:[(CGFloat,CGFloat)]=[(150,260),(235,345),(197,495),(315,535),(435,440),(370,290)];line(pts,1,accent);for p in pts{oval(p.0-5,p.1-5,10,10,ink,fill:true);oval(p.0-12,p.1-12,24,24,accent)}
                for i in 0..<28{let x=CGFloat(95+(i*73)%410),y=CGFloat(180+(i*113)%390);oval(x,y,2.5,2.5,ink,fill:true)}
            case 14:
                oval(235,315,130,130,ink,fill:true);for i in 0..<5{let p=NSBezierPath(ovalIn:NSRect(x:CGFloat(90+i*23),y:CGFloat(210+i*15),width:CGFloat(420-i*46),height:CGFloat(320-i*30)));p.lineWidth=1.5;accent.setStroke();p.stroke()};oval(160,458,25,25,ink,fill:true)
            case 15:
                for i in 0..<8{let x=CGFloat(145+i*42);let y=CGFloat(255+(i%3)*65);line([(x,180),(x,y),(x+24,y+24),(x+24,515)],2,i%2==0 ? ink:accent);oval(x+19,515,10,10,ink);oval(x-5,170,10,10,accent)}
            case 16:
                for i in 0..<7{let r=CGFloat(35+i*22);var pts:[(CGFloat,CGFloat)]=[];for n in 0..<6{let a=CGFloat(n)*CGFloat.pi/3;pts.append((300+cos(a)*r,370+sin(a)*r))};line(pts,1.5,i%2==0 ? ink:accent,close:true)}
            case 17:
                for i in 0..<8{let inset=CGFloat(i*15);let p=NSBezierPath();p.move(to:NSPoint(x:145+inset,y:195));p.line(to:NSPoint(x:145+inset,y:380));p.curve(to:NSPoint(x:455-inset,y:380),controlPoint1:NSPoint(x:145+inset,y:580-inset),controlPoint2:NSPoint(x:455-inset,y:580-inset));p.line(to:NSPoint(x:455-inset,y:195));p.lineWidth=2;(i%2==0 ? ink:accent).setStroke();p.stroke()}
            default:
                oval(220,320,160,160,accent,fill:true);for i in 0..<8{let y=CGFloat(205+i*16);line([(100,y),(500,y)],1,ink)};for i in 0..<15{let a=CGFloat(i)*CGFloat.pi/14;line([(300+cos(a)*120,400+sin(a)*120),(300+cos(a)*165,400+sin(a)*165)],1,ink)}
            }
        }
        // Typeset the full title with system font fallback; no clipping/ellipsis.
        let paragraph=NSMutableParagraphStyle();paragraph.alignment = .center;paragraph.lineBreakMode = .byWordWrapping;paragraph.lineSpacing=3
        let titleBox=NSRect(x:66,y:620,width:468,height:208)
        let safeTitle=title.trimmingCharacters(in:.whitespacesAndNewlines).isEmpty ? "Untitled" : title
        var fontSize:CGFloat=54
        let fontName = design/5 % 3 == 0 ? "Georgia-Bold" : design/5 % 3 == 1 ? "Baskerville" : "AvenirNext-DemiBold"
        var text=NSAttributedString()
        while true {
            text=NSAttributedString(string:safeTitle,attributes:[.font:NSFont(name:fontName,size:fontSize) ?? NSFont.systemFont(ofSize:fontSize,weight:.semibold),.foregroundColor:ink,.paragraphStyle:paragraph])
            let bounds=text.boundingRect(with:NSSize(width:titleBox.width,height:1000),options:[.usesLineFragmentOrigin,.usesFontLeading])
            if (bounds.height<=titleBox.height && bounds.width<=titleBox.width+1) || fontSize<=12 {break};fontSize-=1
        }
        let bounds=text.boundingRect(with:NSSize(width:titleBox.width,height:1000),options:[.usesLineFragmentOrigin,.usesFontLeading])
        text.draw(with:NSRect(x:titleBox.minX,y:titleBox.midY-bounds.height/2,width:titleBox.width,height:bounds.height+2),options:[.usesLineFragmentOrigin,.usesFontLeading])
        line([(260,592),(340,592)],2,accent);oval(297,590,6,6,accent,fill:true)
        line([(275,100),(325,100)],1,accent);oval(296,96,8,8,accent,fill:true)
        NSGraphicsContext.restoreGraphicsState()
        let image=NSImage(size:NSSize(width:width,height:width*3/2));image.addRepresentation(bitmap);return image
    }
    static func jpeg(_ image:NSImage) -> Data? {
        (image.representations.first as? NSBitmapImageRep)?.representation(using:.jpeg,properties:[.compressionFactor:0.92])
    }
}
