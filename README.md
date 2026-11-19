# QuizCraft

A free flashcard and study app, a Quizlet alternative, built as a single HTML file. It runs in any browser, works offline, and can sync across devices with a free account. There's also an iPhone app.

**Live:** https://1jazu11ahm.github.io/studydeck/

## How it's organised

Four pages, with a bar at the top on computers and a tab bar at the bottom on phones:

- **Home:** a greeting, today's goal ring, one **Start training** button that picks what to study next (due reviews first, then the set you're learning), a 7-day chart and your recent sets.
- **Library:** all sets and folders, search across every term, **New set** and **Import**.
- **Progress:** a mastery donut, daily and weekly goal rings, an activity grid, your rank, and anything that needs attention.
- **Profile:** sign-in and sync, theme, study sounds, voice, haptics, backup and restore, and help.

## Study modes

| Mode | What it does |
|---|---|
| Flashcards | Flip, shuffle and autoplay. Swipe on phones. Training mode lets you rate each card Again, Hard, Good or Easy, and each button shows when you'll see the card next. |
| Learn | Adaptive rounds: multiple choice first, then typing, until you get every card right twice. |
| Review | Spaced repetition: only the cards that are due. |
| Write | Type the answers. Small typos in long answers are forgiven. Answers under 6 letters must be exact. |
| Spell | Listen and type, with a letter-by-letter comparison. |
| Test | True/false, multiple choice, matching and written questions, with a score. |
| Timed exam | Beat the clock, no hints. |
| Match | Pair terms and definitions against the clock. |
| Gravity | Type the answer before the asteroid lands. |

**How scheduling works:** QuizCraft uses **FSRS**, the same scheduler modern Anki uses. For every card it tracks how strong the memory is (stability) and how hard the card is for you (difficulty), then schedules the next review for the day you'd have about a 90% chance of still remembering it. Getting a card right on time spreads reviews out (roughly 3, 11, 35, 100 and 270 days). Missing one brings it back the same day. You can change the 90% target in Profile → Memory target: higher means more reviews and less forgetting. The set page still shows the simple diagram (New → Learning → Reviewing → Long-term), worked out from each card's memory strength.

## AI feedback on typed answers

When you write a definition in your own words (Write or Learn, *Answer with: Definition*) and it doesn't match the card exactly, QuizCraft can ask Claude to check the **meaning**. You get a verdict (correct, partly right or wrong) with a score, what you got right, what was missing, and a full model answer. Correct counts as Good, partly right as Hard and wrong as Again. **I disagree** overrules the AI.

- It only runs when you're signed in, and it can be switched off in Profile → AI feedback on typed answers.
- The Claude key never touches the website. It lives in a Supabase Edge Function ([`supabase/functions/grade`](supabase/functions/grade/index.ts)) as the secret `ANTHROPIC_API_KEY`. The function checks that you're signed in, optionally only allows the emails in `ALLOWED_EMAILS`, and limits use to `DAILY_LIMIT` checks a day (200 by default).
- Exact answers and one-word answers are still checked instantly, without the AI.
- If the function isn't set up or can't be reached, the normal check is used.

## Card types

- **Basic:** a term and a definition, with an optional picture.
- **Fill in the blank (cloze):** write a sentence, select the words to hide and tap **Hide words**, or type Anki's format directly: `The {{c1::aorta}} carries blood from the {{c2::left ventricle::chamber}}.` Each number becomes its own card. The text after a second `::` is a hint shown in the blank.
- **Image with tapes (image occlusion):** add a picture, such as a labelled heart diagram, and draw gold tapes over the labels. Each tape becomes a card: the target tape shows a **?**, and you peel it to check. The other tapes stay on, and you can tap them to peek. Name a tape to also use it in Learn, Write and Test. Pictures are stored on the device in the browser's image storage, so they don't use up the 5 MB text limit, and they sync when you're signed in.

## Features

- **Sets:** terms, definitions, images, stars, folders, duplicate, print, and links between related cards in other sets.
- **Import:** paste text (tab, comma, dash or custom separators), a Quizlet export, or a .txt/.csv file.
- **Anki decks:** import an `.apkg` file (Anki → File → Export → Anki Deck Package). Each deck becomes a set, and subdecks are grouped in a folder. Basic cards, reversed cards, cloze, image occlusion and pictures come across, and so does your review progress, including Anki's own FSRS memory data when it's there. Newer (2.1.50+) and older package formats both work. Sounds and custom card templates aren't imported. The Anki reader (about 1 MB) only downloads when you import a deck.
- **Share:** a link that contains the whole set. Export to TXT, CSV or JSON, and back up or restore everything.
- **Exam plan:** set an exam date (in the set's ⋯ menu) to get a daily mastery target.
- **Goals and ranks:** a daily goal of 25 correct answers, a weekly goal of 150, XP, 13 achievements, and ranks from Civilian to Master Detective.
- **Weak spots:** a report across every set, plus a practice session for the cards you keep missing.
- **Read-aloud** in 18 languages, **keyboard shortcuts** on computers, and **haptics** on phones.
- **Study sounds:** real recordings of rain, a fireplace and a café, plus thunder and a soft hum, each with its own slider. Five ready-made mixes (Rainy night, Fireside, Coffee shop, Cozy café, Deep focus), and you can save up to six of your own. They fade in and out, download only when first played (about 2 MB in total) and then work offline. They're off by default; turn them on with the headphones button. Recordings are public domain; see [`sounds/CREDITS.md`](sounds/CREDITS.md).
- **Themes:** Charcoal (default), Midnight city (animated, with backgrounds you unlock by rank), Dark, Light, or Match my device.

## Getting started

New visitors get a one-minute tour and one starter set, **How memory works**: 10 study-science terms that also explain how QuizCraft schedules reviews. Charts appear after the first study day. Replay the tour or re-add the starter set from Profile → Help.

## Saving and cloud sync

- **Saved in the browser first.** Every answer is stored on the device instantly, so the app opens fast and works offline.
- **Synced with an account.** Sign in from Profile (Google or email) and your sets, progress, folders, settings and daily study log sync through Supabase's free plan. If the same set is changed on two devices, the newer change wins. Progress such as XP and achievements is merged, never lost.
- **Backups.** Profile → Export saves everything to a .json file.
- Safari on iPhone can clear website storage after about 7 days without a visit, so sign in or use the iPhone app if you study on a phone.

Technical details:

- Database: one `docs` table protected by Row Level Security, so each user can only read and write their own rows.
- `.github/workflows/keep-supabase-awake.yml` pings the database every 3 days, because Supabase pauses free projects after 7 days without activity.
- The publishable key in `index.html` is meant to be public. Never put the **secret / service_role** key in this repo.

## iPhone app

`ios/` holds a small native SwiftUI app that loads the live site, so website updates appear without reinstalling. It adds:

- Google sign-in through Apple's secure sign-in sheet
- Study sounds that play in silent mode
- Haptics through the Taptic Engine
- A launch screen and app icon
- Exports through the share sheet
- An offline screen, pull to refresh, and swipe back

**Install:**

1. Download `QuizCraft.ipa` from the [`ios-latest` release](https://github.com/1jazu11ahM/studydeck/releases/tag/ios-latest).
2. Drag it into Sideloadly on Windows and sign in with your Apple ID.
3. On the iPhone: Settings → General → VPN & Device Management → trust your Apple ID.

With a free Apple ID the app must be re-installed every 7 days; your data stays.

**Builds:** every change under `ios/` runs **Build iPhone app** in GitHub Actions, which publishes a new unsigned `.ipa` to that release. If GitHub's Mac machines are busy, run the workflow by hand from the Actions tab and pick another runner (`macos-15`, `macos-26`).

Without the app, you can still install the website from Safari: Share → **Add to Home Screen**. It opens full screen and works offline.

## Testing

`tests/pressure_learning.py` runs about 115 checks across every study mode, on a simulated phone (taps and swipes) and a desktop (keyboard). It covers:

- Grading, multiple-choice options and FSRS scheduling
- Streaks, goals, the exam plan and the study log
- Odd sets: one card, shared answers, long text, Dari and empty sets
- Double taps and leaving mid-session
- Fonts and keyboard hints

It needs Python, Playwright and Chrome.

## Design versions

Every earlier design is kept, and all of them read the same saved data, so you can switch freely. Profile links to the most recent ones.

| Version | Where | What it was |
|---|---|---|
| Current | `/` | FSRS scheduling, fill-in-the-blank cards, image tapes and Anki import |
| v5 | [`archive/v5/`](archive/v5/) | Calm layout with charts, standard fonts and touch-friendly study screens (before FSRS and the new card types) |
| v4 | [`archive/v4/`](archive/v4/) | First chart layout (before the font, sound and button changes) |
| v3 | [`archive/v3/`](archive/v3/) | Apple-style pass: system font, swipe-to-rate, bottom sheets, goal ring, installable app |
| v2 | [`archive/v2/`](archive/v2/) | First minimal redesign: Home / Library / Progress / Profile, Charcoal theme |
| v1 | [`archive/v1/`](archive/v1/) | The original Batman-themed design |

To make an older design the main one again, copy its `archive/vN/index.html` over `index.html`. Older versions don't understand fill-in-the-blank or image-tape cards, so those show up blank there.

## Host your own copy on GitHub Pages

1. Create a public repo on GitHub.
2. Upload `index.html`, `manifest.webmanifest`, `sw.js`, `auth-ios.html` and the `icons/` folder.
3. Settings → Pages → Source: *Deploy from a branch* → Branch: `main` / root → Save.
4. The site is live at `https://<your-username>.github.io/<repo>/` within a minute or two.

Cloud sync needs your own free Supabase project: in `index.html`, search for `SB_URL` and replace the project URL and publishable key with yours.
