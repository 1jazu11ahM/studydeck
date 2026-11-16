import SwiftUI
import AVFoundation

@main
struct QuizCraftApp: App {
    init() {
        // Study sounds keep playing when the ringer switch is on silent,
        // and mix with music from other apps instead of stopping it.
        try? AVAudioSession.sharedInstance().setCategory(.playback, mode: .default, options: [.mixWithOthers])
        try? AVAudioSession.sharedInstance().setActive(true)
    }

    var body: some Scene {
        WindowGroup {
            ContentView()
                .preferredColorScheme(.dark)
        }
    }
}

struct ContentView: View {
    @StateObject private var web = WebModel()
    @Environment(\.scenePhase) private var phase

    var body: some View {
        ZStack {
            Color("LaunchBackground").ignoresSafeArea()

            WebViewHost(webView: web.webView)
                .ignoresSafeArea()
                .opacity(web.offline ? 0 : 1)

            if web.offline {
                OfflineView { web.retry() }
                    .transition(.opacity)
            }

            // Same picture as the launch screen, so opening the app feels seamless.
            if !web.firstLoadDone {
                Image("LaunchLogo")
                    .resizable()
                    .frame(width: 96, height: 60)
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                    .background(Color("LaunchBackground"))
                    .ignoresSafeArea()
                    .transition(.opacity)
            }
        }
        .animation(.easeOut(duration: 0.3), value: web.firstLoadDone)
        .animation(.easeOut(duration: 0.2), value: web.offline)
        .onChange(of: phase) { newPhase in
            if newPhase == .active { web.appBecameActive() }
        }
    }
}

struct OfflineView: View {
    let retry: () -> Void

    var body: some View {
        VStack(spacing: 14) {
            Image("LaunchLogo")
                .resizable()
                .frame(width: 64, height: 40)
                .opacity(0.8)
            Text("You're offline")
                .font(.title2.weight(.semibold))
            Text("QuizCraft needs a connection the first time it opens. After that, your sets work offline.")
                .font(.subheadline)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
                .frame(maxWidth: 300)
            Button(action: retry) {
                Text("Try again")
                    .font(.body.weight(.semibold))
                    .padding(.horizontal, 28)
                    .padding(.vertical, 12)
                    .background(Color("Gold"), in: Capsule())
                    .foregroundStyle(Color("LaunchBackground"))
            }
            .padding(.top, 6)
        }
        .padding(32)
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Color("LaunchBackground"))
    }
}
