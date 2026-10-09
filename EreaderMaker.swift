// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (c) 2026 Navaneethan and E-reader Maker contributors
import Cocoa
import UniformTypeIdentifiers

struct ReadingFile: Codable {
    var id = UUID().uuidString
    var path: String
    var state = "Ready to convert"
    var result: String? = nil
    var notes: [String] = []
    var failed = false
}

final class DropSurface: NSView {
    var receive: (([URL]) -> Void)?
    override init(frame frameRect: NSRect) {
        super.init(frame: frameRect)
        registerForDraggedTypes([.fileURL])
    }
    required init?(coder: NSCoder) { fatalError() }
    override func draggingEntered(_ sender: NSDraggingInfo) -> NSDragOperation { .copy }
    override func performDragOperation(_ sender: NSDraggingInfo) -> Bool {
        let urls = sender.draggingPasteboard.readObjects(forClasses: [NSURL.self], options: [.urlReadingFileURLsOnly: true]) as? [URL] ?? []
        receive?(urls)
        return !urls.isEmpty
    }
}

final class AppDelegate: NSObject, NSApplicationDelegate, NSWindowDelegate, NSTableViewDataSource, NSTableViewDelegate {
    var window: NSWindow!
    let table = NSTableView()
    let emptyState = NSStackView()
    let status = NSTextField(labelWithString: "Ready when you are.")
    let detail = NSTextField(wrappingLabelWithString: "Images, tables, and spacing are prepared for a smaller screen.")
    let destinationLabel = NSTextField(labelWithString: "")
    let addButton = NSButton(title: "Add files", target: nil, action: nil)
    let convertButton = NSButton(title: "Convert for Kindle", target: nil, action: nil)
    let cancelButton = NSButton(title: "Cancel", target: nil, action: nil)
    let folderButton = NSButton(title: "Open folder", target: nil, action: nil)
    let sendButton = NSButton(title: "Send to Kindle ↗", target: nil, action: nil)
    let removeButton = NSButton(title: "Remove", target: nil, action: nil)
    let layout = NSSegmentedControl(labels: ["Smart reading", "Keep page layout"], trackingMode: .selectOne, target: nil, action: nil)
    let progress = NSProgressIndicator()
    var files: [ReadingFile] = []
    var task: Process?
    var cancelled = false
    var fatalMessage: String?
    var manifestURL: URL?
    let root = Bundle.main.bundleURL.deletingLastPathComponent()
    var destination: URL!
    var historyURL: URL { root.appendingPathComponent("data/native-library.json") }
    let accent = NSColor(calibratedRed: 0.68, green: 0.76, blue: 1.0, alpha: 1)

    func applicationDidFinishLaunching(_ notification: Notification) {
        NSApp.setActivationPolicy(.regular)
        NSApp.appearance = NSAppearance(named: .darkAqua)
        if let iconURL = Bundle.main.url(forResource: "EreaderMaker", withExtension: "icns"),
           let icon = NSImage(contentsOf: iconURL) {
            NSApp.applicationIconImage = icon
        }
        destination = root.appendingPathComponent("Kindle Books", isDirectory: true)
        if let stored = UserDefaults.standard.string(forKey: "destination") { destination = URL(fileURLWithPath: stored) }
        if let data = try? Data(contentsOf: historyURL), let saved = try? JSONDecoder().decode([ReadingFile].self, from: data) {
            files = saved.filter { $0.result != nil }.suffix(100).map { $0 }
        }
        buildMenu()
        window = NSWindow(contentRect: NSRect(x: 0, y: 0, width: 780, height: 685), styleMask: [.titled, .closable, .miniaturizable, .resizable], backing: .buffered, defer: false)
        window.title = "E-reader Maker"
        window.titleVisibility = .hidden
        window.titlebarAppearsTransparent = true
        window.backgroundColor = NSColor(calibratedWhite: 0.075, alpha: 1)
        window.minSize = NSSize(width: 700, height: 635)
        window.delegate = self
        window.isReleasedWhenClosed = false
        window.center()
        let content = DropSurface()
        content.receive = { [weak self] in self?.add($0) }
        window.contentView = content
        let stack = NSStackView()
        stack.orientation = .vertical; stack.alignment = .leading; stack.spacing = 17
        stack.translatesAutoresizingMaskIntoConstraints = false
        content.addSubview(stack)
        NSLayoutConstraint.activate([
            stack.leadingAnchor.constraint(equalTo: content.leadingAnchor, constant: 30),
            stack.trailingAnchor.constraint(equalTo: content.trailingAnchor, constant: -30),
            stack.topAnchor.constraint(equalTo: content.topAnchor, constant: 18),
            stack.bottomAnchor.constraint(equalTo: content.bottomAnchor, constant: -24)
        ])
        let kicker = label("E - R E A D E R   M A K E R    /    F O R  K I N D L E", size: 10, weight: .semibold, color: accent)
        stack.addArrangedSubview(kicker)
        let title = label("Your next read. Ready for Kindle.", size: 28, weight: .semibold)
        stack.addArrangedSubview(title)
        stack.setCustomSpacing(6, after: title)
        stack.addArrangedSubview(label("Add your files. We’ll take care of the reading layout.", size: 13, color: .secondaryLabelColor))

        let box = DropSurface(); box.receive = { [weak self] in self?.add($0) }
        box.wantsLayer = true; box.layer?.backgroundColor = NSColor(calibratedWhite: 0.105, alpha: 1).cgColor
        box.layer?.cornerRadius = 13; box.layer?.borderWidth = 1; box.layer?.borderColor = NSColor(calibratedWhite: 0.21, alpha: 1).cgColor
        stack.addArrangedSubview(box)
        box.widthAnchor.constraint(equalTo: stack.widthAnchor).isActive = true
        box.heightAnchor.constraint(greaterThanOrEqualToConstant: 220).isActive = true
        let scroll = NSScrollView(); scroll.translatesAutoresizingMaskIntoConstraints = false
        scroll.hasVerticalScroller = true; scroll.drawsBackground = false
        table.backgroundColor = .clear; table.headerView = nil; table.rowHeight = 58
        table.style = .plain; table.selectionHighlightStyle = .regular
        table.allowsMultipleSelection = true; table.intercellSpacing = NSSize(width: 0, height: 3)
        let nameColumn = NSTableColumn(identifier: NSUserInterfaceItemIdentifier("book")); nameColumn.width = 445; nameColumn.minWidth = 250
        let actionColumn = NSTableColumn(identifier: NSUserInterfaceItemIdentifier("action")); actionColumn.width = 155; actionColumn.minWidth = 130; actionColumn.maxWidth = 175
        table.addTableColumn(nameColumn); table.addTableColumn(actionColumn)
        table.columnAutoresizingStyle = .firstColumnOnlyAutoresizingStyle
        table.delegate = self; table.dataSource = self
        table.target = self; table.doubleAction = #selector(revealSelected)
        scroll.documentView = table; box.addSubview(scroll)
        NSLayoutConstraint.activate([scroll.leadingAnchor.constraint(equalTo: box.leadingAnchor, constant: 10), scroll.trailingAnchor.constraint(equalTo: box.trailingAnchor, constant: -10), scroll.topAnchor.constraint(equalTo: box.topAnchor, constant: 9), scroll.bottomAnchor.constraint(equalTo: box.bottomAnchor, constant: -9)])
        emptyState.orientation = .vertical; emptyState.alignment = .centerX; emptyState.spacing = 13
        emptyState.translatesAutoresizingMaskIntoConstraints = false
        let icon = NSImageView(image: NSImage(systemSymbolName: "books.vertical", accessibilityDescription: "Drop reading files")!)
        icon.contentTintColor = accent; icon.symbolConfiguration = NSImage.SymbolConfiguration(pointSize: 34, weight: .light)
        emptyState.addArrangedSubview(icon)
        emptyState.addArrangedSubview(label("Drop something worth reading", size: 17, weight: .medium))
        emptyState.addArrangedSubview(label("PDF · Word · EPUB · images · comics · text", size: 12, color: .secondaryLabelColor))
        box.addSubview(emptyState)
        NSLayoutConstraint.activate([emptyState.centerXAnchor.constraint(equalTo: box.centerXAnchor), emptyState.centerYAnchor.constraint(equalTo: box.centerYAnchor)])

        configure(addButton, action: #selector(pickFiles), symbol: "plus")
        configure(removeButton, action: #selector(removeSelected), symbol: nil)
        layout.selectedSegment = 0; layout.target = self; layout.action = #selector(layoutChanged)
        layout.toolTip = "Smart reading reflows simple pages and preserves complex layouts. Keep page layout uses page images for every PDF page."
        let fileActions = NSStackView(views: [addButton, removeButton, spacer(), layout]); fileActions.spacing = 9
        stack.addArrangedSubview(fileActions); fileActions.widthAnchor.constraint(equalTo: stack.widthAnchor).isActive = true
        detail.font = .systemFont(ofSize: 11); detail.textColor = .secondaryLabelColor; detail.maximumNumberOfLines = 2
        stack.addArrangedSubview(detail); detail.widthAnchor.constraint(equalTo: stack.widthAnchor).isActive = true
        let rule = NSBox(); rule.boxType = .separator; stack.addArrangedSubview(rule); rule.widthAnchor.constraint(equalTo: stack.widthAnchor).isActive = true
        configure(convertButton, action: #selector(start), symbol: "sparkles")
        convertButton.keyEquivalent = "\r"; convertButton.bezelColor = NSColor(calibratedRed: 0.32, green: 0.40, blue: 0.70, alpha: 1)
        configure(cancelButton, action: #selector(cancel), symbol: nil)
        configure(folderButton, action: #selector(openFolder), symbol: "folder")
        configure(sendButton, action: #selector(sendToKindle), symbol: nil)
        let mainActions = NSStackView(views: [convertButton, cancelButton, spacer(), folderButton, sendButton]); mainActions.spacing = 9
        stack.addArrangedSubview(mainActions); mainActions.widthAnchor.constraint(equalTo: stack.widthAnchor).isActive = true
        progress.style = .bar; progress.isIndeterminate = true; progress.isHidden = true
        stack.addArrangedSubview(progress); progress.widthAnchor.constraint(equalTo: stack.widthAnchor).isActive = true
        status.font = .systemFont(ofSize: 12, weight: .medium); status.maximumNumberOfLines = 2; status.lineBreakMode = .byWordWrapping
        stack.addArrangedSubview(status); status.widthAnchor.constraint(equalTo: stack.widthAnchor).isActive = true
        let bottom = NSStackView(); bottom.spacing = 8
        destinationLabel.font = .systemFont(ofSize: 10); destinationLabel.textColor = .secondaryLabelColor; destinationLabel.lineBreakMode = .byTruncatingMiddle
        let change = NSButton(title: "Change…", target: self, action: #selector(changeFolder)); change.bezelStyle = .inline; change.controlSize = .small; change.tag = 100
        bottom.addArrangedSubview(destinationLabel); bottom.addArrangedSubview(change)
        stack.addArrangedSubview(bottom); bottom.widthAnchor.constraint(equalTo: stack.widthAnchor).isActive = true
        updateDestination(); refresh()
        window.makeKeyAndOrderFront(nil); NSApp.activate(ignoringOtherApps: true)
    }

    func label(_ text: String, size: CGFloat, weight: NSFont.Weight = .regular, color: NSColor = .labelColor) -> NSTextField {
        let l = NSTextField(labelWithString: text); l.font = .systemFont(ofSize: size, weight: weight); l.textColor = color; return l
    }
    func spacer() -> NSView { let v = NSView(); v.setContentHuggingPriority(.defaultLow, for: .horizontal); return v }
    func configure(_ button: NSButton, action: Selector, symbol: String?) {
        button.target = self; button.action = action; button.bezelStyle = .rounded; button.controlSize = .large
        if let symbol = symbol { button.image = NSImage(systemSymbolName: symbol, accessibilityDescription: nil); button.imagePosition = .imageLeading }
    }
    func buildMenu() {
        let menu = NSMenu(); let rootItem = NSMenuItem(); let appMenu = NSMenu()
        appMenu.addItem(withTitle: "About E-reader Maker", action: #selector(about), keyEquivalent: "")
        appMenu.addItem(withTitle: "License and notices", action: #selector(showLicense), keyEquivalent: "")
        appMenu.addItem(withTitle: "Source code", action: #selector(showSource), keyEquivalent: "")
        appMenu.addItem(.separator()); appMenu.addItem(withTitle: "Quit E-reader Maker", action: #selector(NSApplication.terminate(_:)), keyEquivalent: "q")
        rootItem.submenu = appMenu; menu.addItem(rootItem)
        let file = NSMenuItem(); let fileMenu = NSMenu(title: "File")
        fileMenu.addItem(withTitle: "Add files…", action: #selector(pickFiles), keyEquivalent: "o")
        fileMenu.addItem(withTitle: "Open saved folder", action: #selector(openFolder), keyEquivalent: "f")
        file.submenu = fileMenu; menu.addItem(file); NSApp.mainMenu = menu
    }
    @objc func about() {
        let alert = NSAlert(); alert.messageText = "E-reader Maker"
        alert.informativeText = "A local, native Mac converter for e-readers.\n\nCopyright © 2026 Navaneethan and E-reader Maker contributors. Licensed under GNU AGPL version 3. You may use, modify, and redistribute it under that license. Provided without warranty. See License and notices in the E-reader Maker menu.\n\nIndependent project; not affiliated with or endorsed by Amazon or Apple. Convert only documents you have permission to use. E-reader Maker does not remove DRM.\n\nConversion runs locally. Send to Kindle opens Amazon’s website; uploading there is your choice. Keep this app beside its project files and .venv folder."
        alert.runModal()
    }
    @objc func showLicense() {
        if let url = Bundle.main.resourceURL?.appendingPathComponent("Legal") { NSWorkspace.shared.open(url) }
    }
    @objc func showSource() { NSWorkspace.shared.open(URL(string: "https://github.com/navaneethanes/ereader-maker-macos")!) }
    func numberOfRows(in tableView: NSTableView) -> Int { files.count }
    func tableView(_ tableView: NSTableView, viewFor tableColumn: NSTableColumn?, row: Int) -> NSView? {
        let item = files[row]
        if tableColumn?.identifier.rawValue == "action" {
            let stack = NSStackView(); stack.spacing = 8; stack.alignment = .centerY
            if item.result != nil {
                let button = NSButton(title: "Show in Finder", target: self, action: #selector(revealRow(_:))); button.tag = row; button.bezelStyle = .rounded; button.controlSize = .small; stack.addArrangedSubview(button)
            }
            if item.failed || !item.notes.isEmpty {
                let info = NSButton(image: NSImage(systemSymbolName: "info.circle", accessibilityDescription: "Conversion notes")!, target: self, action: #selector(showNotes(_:))); info.tag = row; info.bezelStyle = .inline; stack.addArrangedSubview(info)
            }
            return stack
        }
        let cell = NSTableCellView()
        let icon = NSImageView(image: NSImage(systemSymbolName: item.result != nil ? "book.closed.fill" : "doc.text", accessibilityDescription: nil)!)
        icon.contentTintColor = item.failed ? .systemOrange : accent; icon.translatesAutoresizingMaskIntoConstraints = false
        cell.addSubview(icon)
        let name = label(URL(fileURLWithPath: item.path).lastPathComponent, size: 13, weight: .medium); name.lineBreakMode = .byTruncatingMiddle
        let state = label(item.state, size: 11, color: item.failed ? .systemOrange : .secondaryLabelColor); state.lineBreakMode = .byTruncatingTail
        let text = NSStackView(views: [name, state]); text.orientation = .vertical; text.alignment = .leading; text.spacing = 5; text.translatesAutoresizingMaskIntoConstraints = false
        cell.addSubview(text); cell.textField = name
        NSLayoutConstraint.activate([icon.leadingAnchor.constraint(equalTo: cell.leadingAnchor, constant: 9), icon.centerYAnchor.constraint(equalTo: cell.centerYAnchor), icon.widthAnchor.constraint(equalToConstant: 23), icon.heightAnchor.constraint(equalToConstant: 28), text.leadingAnchor.constraint(equalTo: icon.trailingAnchor, constant: 12), text.trailingAnchor.constraint(equalTo: cell.trailingAnchor, constant: -10), text.centerYAnchor.constraint(equalTo: cell.centerYAnchor), name.widthAnchor.constraint(equalTo: text.widthAnchor), state.widthAnchor.constraint(equalTo: text.widthAnchor)])
        return cell
    }
    func tableViewSelectionDidChange(_ notification: Notification) { removeButton.isEnabled = task == nil && !table.selectedRowIndexes.isEmpty }
    @objc func pickFiles() {
        guard task == nil else { return }
        let panel = NSOpenPanel(); panel.canChooseFiles = true; panel.canChooseDirectories = false; panel.allowsMultipleSelection = true; panel.allowsOtherFileTypes = true
        panel.message = "Choose documents, ebooks, images, or comics to read on your Kindle."
        panel.beginSheetModal(for: window) { [weak self] response in if response == .OK { self?.add(panel.urls) } }
    }
    func add(_ urls: [URL]) {
        guard task == nil else { status.stringValue = "Wait for this conversion to finish, or press Cancel."; return }
        var count = 0
        for url in urls {
            var directory: ObjCBool = false
            guard FileManager.default.fileExists(atPath: url.path, isDirectory: &directory), !directory.boolValue else { continue }
            if files.contains(where: { $0.path == url.path && $0.result == nil }) { continue }
            files.append(ReadingFile(path: url.path)); count += 1
        }
        status.stringValue = count > 0 ? "\(count) file\(count == 1 ? "" : "s") added. Ready to make a better read." : "Choose files that aren’t already waiting in the list."
        refresh()
    }
    @objc func removeSelected() {
        guard task == nil else { return }
        for index in table.selectedRowIndexes.reversed() { files.remove(at: index) }
        persist(); refresh(); status.stringValue = "Removed from this list. Saved books are still in their folder."
    }
    @objc func layoutChanged() {
        detail.stringValue = layout.selectedSegment == 0 ? "Images, tables, and spacing are prepared for a smaller screen." : "PDF pages stay exactly as they look. Text on page images won’t resize."
    }
    func refresh() {
        table.reloadData(); emptyState.isHidden = !files.isEmpty
        let busy = task != nil
        addButton.isEnabled = !busy; layout.isEnabled = !busy
        convertButton.isEnabled = !busy && files.contains(where: { $0.result == nil })
        removeButton.isEnabled = !busy && !table.selectedRowIndexes.isEmpty
        cancelButton.isHidden = !busy; cancelButton.isEnabled = busy && !cancelled
        sendButton.isEnabled = files.contains { $0.result != nil }
        progress.isHidden = !busy
        if busy { progress.startAnimation(nil) } else { progress.stopAnimation(nil) }
    }
    func persist() {
        do { try FileManager.default.createDirectory(at: historyURL.deletingLastPathComponent(), withIntermediateDirectories: true); try JSONEncoder().encode(files.filter { $0.result != nil }).write(to: historyURL, options: .atomic) } catch { status.stringValue = "Books are saved, but the recent list could not be stored." }
    }
    func updateDestination() { destinationLabel.stringValue = "Saved to \(destination.path)"; destinationLabel.toolTip = destination.path }
    @objc func changeFolder() {
        guard task == nil else { status.stringValue = "Finish this conversion before changing the folder."; return }
        let panel = NSOpenPanel(); panel.canChooseFiles = false; panel.canChooseDirectories = true; panel.canCreateDirectories = true; panel.prompt = "Save books here"
        panel.beginSheetModal(for: window) { [weak self] response in
            if response == .OK, let url = panel.url { self?.destination = url; UserDefaults.standard.set(url.path, forKey: "destination"); self?.updateDestination() }
        }
    }
    @objc func openFolder() {
        do { try FileManager.default.createDirectory(at: destination, withIntermediateDirectories: true); NSWorkspace.shared.open(destination) }
        catch { status.stringValue = "Could not open the saved folder: \(error.localizedDescription)" }
    }
    @objc func sendToKindle() { NSWorkspace.shared.open(URL(string: "https://www.amazon.com/sendtokindle")!) }
    @objc func revealRow(_ sender: NSButton) { reveal(sender.tag) }
    @objc func revealSelected() { if table.clickedRow >= 0 { reveal(table.clickedRow) } }
    func reveal(_ index: Int) {
        guard files.indices.contains(index), let path = files[index].result else { return }
        if FileManager.default.fileExists(atPath: path) { NSWorkspace.shared.activateFileViewerSelecting([URL(fileURLWithPath: path)]) }
        else { status.stringValue = "This book was moved or deleted. Add the original again to recreate it." }
    }
    @objc func showNotes(_ sender: NSButton) {
        let item = files[sender.tag]; let alert = NSAlert(); alert.messageText = URL(fileURLWithPath: item.path).lastPathComponent
        alert.informativeText = item.notes.joined(separator: "\n\n"); alert.beginSheetModal(for: window)
    }
    @objc func start() {
        guard task == nil else { return }
        let pending = files.filter { $0.result == nil }
        guard !pending.isEmpty else { return }
        guard pending.count <= 100 else { status.stringValue = "Convert at most 100 files at a time."; return }
        let python = root.appendingPathComponent(".venv/bin/python")
        guard FileManager.default.isExecutableFile(atPath: python.path) else { status.stringValue = "Keep E-reader Maker in its project folder beside .venv."; return }
        do {
            let manifest = FileManager.default.temporaryDirectory.appendingPathComponent("ereader-maker-\(UUID().uuidString).json")
            try JSONEncoder().encode(pending).write(to: manifest, options: .atomic); manifestURL = manifest
            let process = Process(); let output = Pipe(); let errorOutput = Pipe()
            process.executableURL = python; process.currentDirectoryURL = root
            process.arguments = [root.appendingPathComponent("native_worker.py").path, "--manifest", manifest.path, "--destination", destination.path, "--layout", layout.selectedSegment == 0 ? "auto" : "pages"]
            var env = ProcessInfo.processInfo.environment; env["PYTHONUNBUFFERED"] = "1"; env["PATH"] = "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"; process.environment = env
            process.standardOutput = output; process.standardError = errorOutput; process.standardInput = FileHandle.nullDevice
            cancelled = false; fatalMessage = nil; task = process
            for i in files.indices where files[i].result == nil { files[i].state = "Waiting…"; files[i].failed = false; files[i].notes = [] }
            status.stringValue = "Preparing \(pending.count) book\(pending.count == 1 ? "" : "s")…"; refresh()
            try process.run(); try? output.fileHandleForWriting.close(); try? errorOutput.fileHandleForWriting.close()
            // Drain stderr separately so a diagnostic cannot block conversion.
            DispatchQueue.global(qos: .utility).async { _ = errorOutput.fileHandleForReading.readDataToEndOfFile() }
            DispatchQueue.global(qos: .utility).async { [weak self] in
                var buffer = Data()
                while true {
                    let data = output.fileHandleForReading.availableData
                    if data.isEmpty { break }
                    buffer.append(data)
                    while let newline = buffer.firstIndex(of: 10) {
                        let line = buffer.subdata(in: 0..<newline); buffer.removeSubrange(0...newline)
                        if let event = try? JSONSerialization.jsonObject(with: line) as? [String: Any] {
                            DispatchQueue.main.async { self?.handle(event) }
                        }
                    }
                }
                process.waitUntilExit()
                DispatchQueue.main.async { self?.finished(process.terminationStatus) }
            }
        } catch {
            task = nil; if let url = manifestURL { try? FileManager.default.removeItem(at: url) }; manifestURL = nil
            status.stringValue = "Could not start: \(error.localizedDescription)"; refresh()
        }
    }
    func handle(_ event: [String: Any]) {
        guard let kind = event["event"] as? String else { return }
        if kind == "fatal" { fatalMessage = event["message"] as? String; return }
        guard let id = event["id"] as? String, let i = files.firstIndex(where: { $0.id == id }) else { return }
        if kind == "progress" {
            files[i].state = event["message"] as? String ?? "Converting…"; status.stringValue = files[i].state
        } else if kind == "done" {
            files[i].result = event["path"] as? String; files[i].notes = event["notes"] as? [String] ?? []
            let size = ByteCountFormatter.string(fromByteCount: (event["size"] as? NSNumber)?.int64Value ?? 0, countStyle: .file)
            files[i].state = "Ready for Kindle · EPUB · \(size)"; persist()
        } else if kind == "error" || kind == "cancelled" {
            let message = event["message"] as? String ?? "Could not convert this file."
            files[i].state = message; files[i].failed = true; files[i].notes = [message]
        }
        table.reloadData()
    }
    func finished(_ code: Int32) {
        task = nil; if let url = manifestURL { try? FileManager.default.removeItem(at: url) }; manifestURL = nil
        for i in files.indices where files[i].result == nil && !files[i].failed { files[i].state = cancelled ? "Cancelled · ready to retry" : "Ready to retry" }
        let failures = files.filter { $0.result == nil }.count
        status.stringValue = cancelled ? "Cancelled. Completed books are saved; originals are unchanged." : (fatalMessage ?? (code != 0 ? "The conversion stopped unexpectedly. You can retry the remaining files." : failures > 0 ? "\(failures) file\(failures == 1 ? " needs" : "s need") attention. Click ⓘ for details." : "Ready to read. Open the folder, then send your EPUBs to Kindle."))
        persist(); refresh()
    }
    @objc func cancel() {
        guard let process = task else { return }; cancelled = true
        // The worker becomes a process group leader shortly after launching.
        if kill(-process.processIdentifier, SIGTERM) != 0 { process.terminate() }
        status.stringValue = "Cancelling…"; cancelButton.isEnabled = false
    }
    func windowShouldClose(_ sender: NSWindow) -> Bool {
        if task != nil { cancel() }
        return true
    }
    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool { true }
    func applicationShouldTerminate(_ sender: NSApplication) -> NSApplication.TerminateReply {
        if task != nil { cancel() }
        return .terminateNow
    }
}

let application = NSApplication.shared
let delegate = AppDelegate()
application.delegate = delegate
application.run()
