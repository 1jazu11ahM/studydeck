# QuizCraft

A free, open-source Quizlet-style flashcard app that runs in one HTML file. It needs no server, database or account.

## Features
- Study sets with terms, definitions, images, stars, folders, search, duplicate, print
- Bulk import (tab / comma / dash / custom separators, Quizlet export, .txt/.csv)
- Modes: Flashcards (flip, shuffle, autoplay, track progress), Learn (adaptive rounds), Write, Spell (text-to-speech), Test (true/false, multiple choice, matching, written), Match (timed game), Gravity (arcade game), Review (spaced repetition)
- Progress tracking (not studied / learning / mastered), day streak, best scores
- Share links (the set lives inside the URL), export to TXT / CSV / JSON, full backup & restore
- Themes: Midnight (night city skyline with searchlights and rain), Light and Dark
- Read-aloud in 18 languages, keyboard shortcuts, mobile layout

## Getting started
New visitors get a short guided tour and two starter sets (IT: OSI Model & Common Ports, Nursing: Vital Signs & Abbreviations). Replay the tour or re-add the starter sets from Settings → Help.

## Features
- **Command Center** dashboard: Nocturne City clock, daily briefing, Continue Training, weak spots, upcoming exams
- **XP, ranks and achievements**: Recruit → Vigilante → Detective → Night Warden → Master Detective; XP only for correct answers and mastery
- **Daily mission & weekly challenge**, **The Code** (daily line + reflection journal)
- **Case Files** (detective vocabulary, case numbers, case-closed stamps, linked cases, detective vision)
- **Training mode**: reveal, then rate 1–4 (Didn't know / Hard / Knew it / Easy) to schedule reviews
- **Detective Mode**: weakness report and an "unresolved evidence" study session across all sets
- **Training Simulator**: three-stage timed exam with streak scoring
- **Mission planner**: set an exam date and get a daily mastery target
- **Environments** (unlock by rank): Midnight City, The Rooftop, The Cave, Manor Library
- **Ambience**: rain, thunder and computer hum generated live with the Web Audio API

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
