// SPDX-License-Identifier: AGPL-3.0-only
import Cocoa
import UniformTypeIdentifiers

func readableTitle(_ source: String) -> String {
    var value=source.replacingOccurrences(of:"[_]+|(?<=\\w)-(?=\\w)",with:" ",options:.regularExpression)
    value=value.replacingOccurrences(of:"\\s+",with:" ",options:.regularExpression).trimmingCharacters(in:CharacterSet(charactersIn:" .-"))
    let small:Set<String>=["a","an","and","at","by","for","in","of","on","or","the","to","with"]
    return String(value.split(separator:" ").enumerated().map { i,part -> String in
        let word=String(part)
        if word==word.uppercased() && word.count<=5{return word}
        if word==word.lowercased() || word==word.uppercased(){return i>0 && small.contains(word.lowercased()) ? word.lowercased():word.prefix(1).uppercased()+word.dropFirst().lowercased()}
        return word
    }.joined(separator:" ").prefix(240))
}

final class CoverGridView: NSView { override var isFlipped: Bool { true } }

final class CoverEditor: NSObject, NSTextFieldDelegate {
    let panel=NSPanel(contentRect:NSRect(x:0,y:0,width:830,height:650),styleMask:[.titled,.closable],backing:.buffered,defer:false)
    let titleField=NSTextField(string:"")
    let preview=NSImageView()
    let caption=NSTextField(wrappingLabelWithString:"")
    let mode=NSPopUpButton()
    let imageButton=NSButton(title:"Choose image…",target:nil,action:nil)
    var design=0
    var imagePath:String?
    var customImage:NSImage?
    var originalTitle=""
    var originalEdited=false
    var save:((String,Bool,String,Int,String?)->Void)?
    var thumbnails:[NSButton]=[]
    static var cachedThumbnails:[NSImage]=[]
    init(item:ReadingFile, save:@escaping (String,Bool,String,Int,String?)->Void) {
        super.init(); self.save=save
        panel.title="Cover & title";panel.appearance=NSAppearance(named:.darkAqua)
        let stem=URL(fileURLWithPath:item.path).deletingPathExtension().lastPathComponent
        originalTitle=item.title ?? readableTitle(stem);originalEdited=item.titleEdited ?? false
        titleField.stringValue=originalTitle;titleField.delegate=self;titleField.placeholderString="Book title"
        design=item.coverDesign ?? CoverArt.suggested(originalTitle);imagePath=item.coverImage
        if let path=imagePath{customImage=NSImage(contentsOfFile:path)}
        let book=["epub","mobi","azw","azw3","fb2"].contains(URL(fileURLWithPath:item.path).pathExtension.lowercased())
        mode.addItems(withTitles:[book ? "Keep existing cover":"No new cover","Designed cover","My image + title"])
        let choice=item.coverMode ?? "auto"
        mode.selectItem(at:choice=="custom" ? 2:choice=="design" ? 1:choice=="keep" ? 0:book ? 0:1)
        mode.target=self;mode.action=#selector(updatePreview)
        let root=NSStackView();root.orientation = .vertical;root.spacing=16;root.translatesAutoresizingMaskIntoConstraints=false
        panel.contentView!.addSubview(root)
        NSLayoutConstraint.activate([root.leadingAnchor.constraint(equalTo:panel.contentView!.leadingAnchor,constant:22),root.trailingAnchor.constraint(equalTo:panel.contentView!.trailingAnchor,constant:-22),root.topAnchor.constraint(equalTo:panel.contentView!.topAnchor,constant:20),root.bottomAnchor.constraint(equalTo:panel.contentView!.bottomAnchor,constant:-20)])
        let heading=NSTextField(labelWithString:"Make it look like a book.");heading.font = .systemFont(ofSize:22,weight:.semibold);root.addArrangedSubview(heading)
        let columns=NSStackView();columns.orientation = .horizontal;columns.alignment = .top;columns.spacing=20
        let left=NSStackView();left.orientation = .vertical;left.spacing=12;left.alignment = .leading
        preview.imageScaling = .scaleProportionallyUpOrDown
        left.addArrangedSubview(preview);preview.widthAnchor.constraint(equalToConstant:250).isActive=true;preview.heightAnchor.constraint(equalToConstant:355).isActive=true
        left.addArrangedSubview(titleField);titleField.widthAnchor.constraint(equalToConstant:250).isActive=true
        left.addArrangedSubview(mode);mode.widthAnchor.constraint(equalToConstant:250).isActive=true
        imageButton.target=self;imageButton.action=#selector(chooseImage);imageButton.bezelStyle = .rounded;left.addArrangedSubview(imageButton)
        caption.font = .systemFont(ofSize:11);caption.textColor = .secondaryLabelColor;caption.maximumNumberOfLines=3;left.addArrangedSubview(caption);caption.widthAnchor.constraint(equalToConstant:250).isActive=true
        columns.addArrangedSubview(left)
        let right=NSStackView();right.orientation = .vertical;right.alignment = .leading;right.spacing=8
        let text=NSTextField(labelWithString:"100 original designs · choose a cover");text.font = .systemFont(ofSize:12,weight:.medium);right.addArrangedSubview(text)
        let scroll=NSScrollView();scroll.hasVerticalScroller=true;scroll.drawsBackground=false
        let grid=CoverGridView(frame:NSRect(x:0,y:0,width:492,height:20*137))
        if Self.cachedThumbnails.isEmpty{Self.cachedThumbnails=(0..<100).map { CoverArt.render(title:"The Art of Reading",design:$0,width:100) }}
        for i in 0..<100 {
            let button=NSButton(frame:NSRect(x:(i%5)*96,y:(i/5)*137,width:90,height:130))
            button.image=Self.cachedThumbnails[i];button.imagePosition = .imageOnly;button.imageScaling = .scaleProportionallyUpOrDown;button.isBordered=false
            button.tag=i;button.target=self;button.action=#selector(selectDesign(_:));button.toolTip=CoverArt.name(i);button.setAccessibilityLabel(CoverArt.name(i));grid.addSubview(button);thumbnails.append(button)
        }
        scroll.documentView=grid;right.addArrangedSubview(scroll);scroll.widthAnchor.constraint(equalToConstant:492).isActive=true;scroll.heightAnchor.constraint(equalToConstant:480).isActive=true
        columns.addArrangedSubview(right);root.addArrangedSubview(columns)
        let cancel=NSButton(title:"Cancel",target:self,action:#selector(close));cancel.bezelStyle = .rounded;cancel.keyEquivalent="\u{1b}"
        let apply=NSButton(title:"Use this cover & title",target:self,action:#selector(apply));apply.bezelStyle = .rounded;apply.keyEquivalent="\r"
        let actions=NSStackView(views:[cancel,apply]);actions.spacing=10;root.addArrangedSubview(actions)
        updatePreview()
    }
    func controlTextDidChange(_ obj:Notification){if titleField.stringValue.count>240{titleField.stringValue=String(titleField.stringValue.prefix(240))};updatePreview()}
    @objc func selectDesign(_ sender:NSButton){design=sender.tag;mode.selectItem(at:1);updatePreview()}
    @objc func updatePreview(){
        let keep=mode.indexOfSelectedItem==0
        preview.image=keep ? nil:CoverArt.render(title:titleField.stringValue,design:design,custom:mode.indexOfSelectedItem==2 ? customImage:nil,width:500)
        caption.stringValue=keep ? "The book’s existing front pages stay as they are.":mode.indexOfSelectedItem==2 ? (imagePath==nil ? "Choose an image. It will be fitted without cropping.":"Your image is fitted without cropping. The original stays unchanged."):CoverArt.name(design)
        for button in thumbnails{button.wantsLayer=true;button.layer?.borderWidth=button.tag==design && !keep ? 2:0;button.layer?.borderColor=NSColor.controlAccentColor.cgColor;button.layer?.cornerRadius=4}
    }
    @objc func chooseImage(){let chooser=NSOpenPanel();chooser.allowedContentTypes=[.jpeg,.png,.tiff];chooser.canChooseDirectories=false;chooser.allowsMultipleSelection=false;chooser.prompt="Use image";chooser.beginSheetModal(for:panel){[weak self]result in guard let self=self,result == .OK,let url=chooser.url else{return};let size=(try? url.resourceValues(forKeys:[.fileSizeKey]).fileSize) ?? Int.max;guard size<=40*1024*1024,let image=NSImage(contentsOf:url),image.size.width*image.size.height<=40_000_000 else {self.caption.stringValue="Choose an image below 40 MB and 40 megapixels.";return};self.imagePath=url.path;self.customImage=image;self.mode.selectItem(at:2);self.updatePreview()}}
    @objc func apply(){let title=titleField.stringValue.trimmingCharacters(in:.whitespacesAndNewlines);guard !title.isEmpty else{caption.stringValue="Enter a book title.";return};guard mode.indexOfSelectedItem != 2 || imagePath != nil else{caption.stringValue="Choose an image first.";return};save?(title,originalEdited || title != originalTitle,["keep","design","custom"][mode.indexOfSelectedItem],design,imagePath);close()}
    @objc func close(){panel.sheetParent?.endSheet(panel);panel.orderOut(nil)}
}
