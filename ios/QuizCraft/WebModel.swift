import SwiftUI
import WebKit
import AuthenticationServices

/// Hosts the QuizCraft website in a native web view and adds the
/// pieces a website can't do on its own: Google sign-in through Apple's
/// secure sheet, saving exports through the share sheet, and opening
/// outside links in Safari.
final class WebModel: NSObject, ObservableObject {
    static let home = URL(string: "https://1jazu11ahm.github.io/studydeck/")!
    static let host = "1jazu11ahm.github.io"
    static let background = UIColor(red: 0x14 / 255, green: 0x15 / 255, blue: 0x18 / 255, alpha: 1)

    @Published var firstLoadDone = false
    @Published var offline = false

    let webView: WKWebView
    private var authSession: ASWebAuthenticationSession?
    private var downloads: [ObjectIdentifier: URL] = [:]
    private var lastActive = Date()

    override init() {
        let config = WKWebViewConfiguration()
        config.websiteDataStore = .default()          // keeps sets and sign-in between launches
        config.allowsInlineMediaPlayback = true
        config.mediaTypesRequiringUserActionForPlayback = []
        config.limitsNavigationsToAppBoundDomains = true // enables offline support for the site
        config.applicationNameForUserAgent = "QuizCraftiOS/1.0"

        let content = WKUserContentController()
        content.addUserScript(WKUserScript(
            source: "window.QC_IOS=true;document.documentElement.classList.add('ios-app');",
            injectionTime: .atDocumentStart,
            forMainFrameOnly: true))
        config.userContentController = content

        webView = WKWebView(frame: .zero, configuration: config)
        super.init()

        content.add(WeakMessageHandler(self), name: "qc")
        webView.navigationDelegate = self
        webView.uiDelegate = self
        webView.allowsBackForwardNavigationGestures = true // swipe from the left edge to go back
        webView.isOpaque = false
        webView.backgroundColor = Self.background
        webView.scrollView.backgroundColor = Self.background
        webView.scrollView.contentInsetAdjustmentBehavior = .never
        if #available(iOS 16.4, *) { webView.isInspectable = true }

        let refresh = UIRefreshControl()
        refresh.tintColor = UIColor(red: 0xC6 / 255, green: 0xA6 / 255, blue: 0x60 / 255, alpha: 1)
        refresh.addTarget(self, action: #selector(pullToRefresh(_:)), for: .valueChanged)
        webView.scrollView.refreshControl = refresh

        webView.load(URLRequest(url: Self.home))
    }

    @objc private func pullToRefresh(_ sender: UIRefreshControl) {
        webView.reload()
    }

    func retry() {
        offline = false
        if webView.url == nil { webView.load(URLRequest(url: Self.home)) } else { webView.reload() }
    }

    /// After a long time in the background, check for a newer version of the site.
    func appBecameActive() {
        if Date().timeIntervalSince(lastActive) > 60 * 60, firstLoadDone, !offline {
            webView.evaluateJavaScript("typeof sync==='function'&&user&&sync()", completionHandler: nil)
        }
        lastActive = Date()
    }

    private func endRefreshing() {
        webView.scrollView.refreshControl?.endRefreshing()
    }

    // MARK: Google sign-in

    private func startSignIn(_ url: URL) {
        let session = ASWebAuthenticationSession(url: url, callbackURLScheme: "quizcraft") { [weak self] callback, _ in
            DispatchQueue.main.async {
                guard let self else { return }
                let arg = callback.map { Self.jsString($0.absoluteString) } ?? "null"
                self.webView.evaluateJavaScript("window.qcAuthCallback&&window.qcAuthCallback(\(arg))", completionHandler: nil)
                self.authSession = nil
            }
        }
        session.presentationContextProvider = self
        session.prefersEphemeralWebBrowserSession = false
        authSession = session
        session.start()
    }

    private static func jsString(_ s: String) -> String {
        guard let data = try? JSONSerialization.data(withJSONObject: s, options: .fragmentsAllowed),
              let out = String(data: data, encoding: .utf8) else { return "null" }
        return out
    }

    // MARK: Sharing exported files

    private func share(_ fileURL: URL) {
        guard let top = UIApplication.topViewController() else { return }
        let sheet = UIActivityViewController(activityItems: [fileURL], applicationActivities: nil)
        sheet.popoverPresentationController?.sourceView = top.view
        sheet.popoverPresentationController?.sourceRect = CGRect(x: top.view.bounds.midX, y: top.view.bounds.midY, width: 0, height: 0)
        top.present(sheet, animated: true)
    }
}

// MARK: - Messages from the page

extension WebModel: WKScriptMessageHandler {
    func userContentController(_ controller: WKUserContentController, didReceive message: WKScriptMessage) {
        guard let body = message.body as? [String: Any], let type = body["type"] as? String else { return }
        switch type {
        case "oauth":
            if let s = body["url"] as? String, let url = URL(string: s) { startSignIn(url) }
        case "open":
            if let s = body["url"] as? String, let url = URL(string: s) { UIApplication.shared.open(url) }
        case "haptic":
            Haptics.play(body["style"] as? String ?? "light")
        default:
            break
        }
    }
}

/// Taptic Engine feedback requested by the page (correct/wrong answers, card flips, swipes).
enum Haptics {
    private static let selection = UISelectionFeedbackGenerator()
    private static let light = UIImpactFeedbackGenerator(style: .light)
    private static let medium = UIImpactFeedbackGenerator(style: .medium)
    private static let notify = UINotificationFeedbackGenerator()

    static func play(_ style: String) {
        switch style {
        case "tick": selection.selectionChanged()
        case "light": light.impactOccurred()
        case "medium": medium.impactOccurred()
        case "success": notify.notificationOccurred(.success)
        case "error": notify.notificationOccurred(.error)
        case "celebrate":
            notify.notificationOccurred(.success)
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.18) { medium.impactOccurred(intensity: 0.8) }
        default: light.impactOccurred()
        }
    }
}

/// Avoids a retain cycle between the web view and its message handler.
final class WeakMessageHandler: NSObject, WKScriptMessageHandler {
    weak var target: WKScriptMessageHandler?
    init(_ target: WKScriptMessageHandler) { self.target = target }
    func userContentController(_ c: WKUserContentController, didReceive m: WKScriptMessage) {
        target?.userContentController(c, didReceive: m)
    }
}

// MARK: - Navigation

extension WebModel: WKNavigationDelegate {
    func webView(_ webView: WKWebView, decidePolicyFor action: WKNavigationAction, decisionHandler: @escaping (WKNavigationActionPolicy) -> Void) {
        if action.shouldPerformDownload { decisionHandler(.download); return }
        guard let url = action.request.url else { decisionHandler(.allow); return }
        if ["blob", "data", "about"].contains(url.scheme ?? "") { decisionHandler(.allow); return }
        let isMainFrame = action.targetFrame?.isMainFrame ?? true
        if isMainFrame && url.host != Self.host {
            // Anything outside QuizCraft (help pages, email links, Google Docs…) opens in Safari.
            UIApplication.shared.open(url)
            decisionHandler(.cancel)
            return
        }
        decisionHandler(.allow)
    }

    func webView(_ webView: WKWebView, decidePolicyFor response: WKNavigationResponse, decisionHandler: @escaping (WKNavigationResponsePolicy) -> Void) {
        decisionHandler(response.canShowMIMEType ? .allow : .download)
    }

    func webView(_ webView: WKWebView, navigationAction: WKNavigationAction, didBecome download: WKDownload) {
        download.delegate = self
    }

    func webView(_ webView: WKWebView, navigationResponse: WKNavigationResponse, didBecome download: WKDownload) {
        download.delegate = self
    }

    func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
        offline = false
        firstLoadDone = true
        endRefreshing()
    }

    func webView(_ webView: WKWebView, didFailProvisionalNavigation navigation: WKNavigation!, withError error: Error) {
        handle(error)
    }

    func webView(_ webView: WKWebView, didFail navigation: WKNavigation!, withError error: Error) {
        handle(error)
    }

    private func handle(_ error: Error) {
        endRefreshing()
        let e = error as NSError
        if e.domain == NSURLErrorDomain && e.code == NSURLErrorCancelled { return }
        if e.domain == NSURLErrorDomain { offline = true }
        firstLoadDone = true
    }

    func webViewWebContentProcessDidTerminate(_ webView: WKWebView) {
        webView.reload()
    }
}

// MARK: - Pop-ups, alerts, new windows

extension WebModel: WKUIDelegate {
    func webView(_ webView: WKWebView, createWebViewWith configuration: WKWebViewConfiguration, for action: WKNavigationAction, windowFeatures: WKWindowFeatures) -> WKWebView? {
        if let url = action.request.url {
            if url.host == Self.host { webView.load(action.request) } else { UIApplication.shared.open(url) }
        }
        return nil
    }

    func webView(_ webView: WKWebView, runJavaScriptAlertPanelWithMessage message: String, initiatedByFrame frame: WKFrameInfo, completionHandler: @escaping () -> Void) {
        let alert = UIAlertController(title: nil, message: message, preferredStyle: .alert)
        alert.addAction(UIAlertAction(title: "OK", style: .default) { _ in completionHandler() })
        guard let top = UIApplication.topViewController() else { completionHandler(); return }
        top.present(alert, animated: true)
    }

    func webView(_ webView: WKWebView, runJavaScriptConfirmPanelWithMessage message: String, initiatedByFrame frame: WKFrameInfo, completionHandler: @escaping (Bool) -> Void) {
        let alert = UIAlertController(title: nil, message: message, preferredStyle: .alert)
        alert.addAction(UIAlertAction(title: "Cancel", style: .cancel) { _ in completionHandler(false) })
        alert.addAction(UIAlertAction(title: "OK", style: .default) { _ in completionHandler(true) })
        guard let top = UIApplication.topViewController() else { completionHandler(false); return }
        top.present(alert, animated: true)
    }
}

// MARK: - Downloads (exports and backups)

extension WebModel: WKDownloadDelegate {
    func download(_ download: WKDownload, decideDestinationUsing response: URLResponse, suggestedFilename: String, completionHandler: @escaping (URL?) -> Void) {
        let dir = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString, isDirectory: true)
        try? FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
        let file = dir.appendingPathComponent(suggestedFilename.isEmpty ? "quizcraft-export" : suggestedFilename)
        downloads[ObjectIdentifier(download)] = file
        completionHandler(file)
    }

    func downloadDidFinish(_ download: WKDownload) {
        if let file = downloads.removeValue(forKey: ObjectIdentifier(download)) {
            DispatchQueue.main.async { self.share(file) }
        }
    }

    func download(_ download: WKDownload, didFailWithError error: Error, resumeData: Data?) {
        downloads.removeValue(forKey: ObjectIdentifier(download))
    }
}

// MARK: - Sign-in sheet anchor

extension WebModel: ASWebAuthenticationPresentationContextProviding {
    func presentationAnchor(for session: ASWebAuthenticationSession) -> ASPresentationAnchor {
        UIApplication.keyWindow ?? ASPresentationAnchor()
    }
}

// MARK: - SwiftUI wrapper

struct WebViewHost: UIViewRepresentable {
    let webView: WKWebView
    func makeUIView(context: Context) -> WKWebView { webView }
    func updateUIView(_ uiView: WKWebView, context: Context) {}
}

extension UIApplication {
    static var keyWindow: UIWindow? {
        UIApplication.shared.connectedScenes
            .compactMap { $0 as? UIWindowScene }
            .flatMap { $0.windows }
            .first { $0.isKeyWindow }
    }

    static func topViewController(_ base: UIViewController? = UIApplication.keyWindow?.rootViewController) -> UIViewController? {
        if let presented = base?.presentedViewController { return topViewController(presented) }
        if let nav = base as? UINavigationController { return topViewController(nav.visibleViewController) }
        return base
    }
}
