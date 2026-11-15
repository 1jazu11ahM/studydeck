# StudyDeck

A free, open-source Quizlet-style flashcard app that runs in one HTML file. It needs no server, database or account.

## Features
- Study sets with terms, definitions, images, stars, folders, search, duplicate, print
- Bulk import (tab / comma / dash / custom separators, Quizlet export, .txt/.csv)
- Modes: Flashcards (flip, shuffle, autoplay, track progress), Learn (adaptive rounds), Write, Spell (text-to-speech), Test (true/false, multiple choice, matching, written), Match (timed game), Gravity (arcade game), Review (spaced repetition)
- Progress tracking (not studied / learning / mastered), day streak, best scores
- Share links (the set lives inside the URL), export to TXT / CSV / JSON, full backup & restore
- Read-aloud in 18 languages, dark mode, keyboard shortcuts, mobile layout

## Cloud sync
Click **☁️ Sign in** to create an account. Your sets, progress, folders and settings then sync across all your devices through Supabase (free plan). The app saves to the browser first, so it keeps working offline and uploads when you reconnect. If the same set is changed on two devices, the newer change wins.

- Database: one `docs` table protected by Row Level Security, so each user can only read and write their own rows.
- `.github/workflows/keep-supabase-awake.yml` pings the database every 3 days, because Supabase pauses free projects after 7 days without activity.
- The publishable key in `index.html` is meant to be public. Never put the **secret / service_role** key in this repo.

## Host it free on GitHub Pages
1. Create a new public repo on GitHub (e.g. `studydeck`).
2. Upload `index.html` (and this README) → Commit.
3. Settings → Pages → Source: *Deploy from a branch* → Branch: `main` / root → Save.
4. Your site will be live at `https://<your-username>.github.io/studydeck/` within a minute or two.
