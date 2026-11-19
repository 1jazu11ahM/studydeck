# Prompt: generate QuizCraft flashcards

Copy the whole prompt below into any AI chat (Claude works well), then attach or paste your lecture notes, slides or textbook section after it. You don't need to fill anything in. The AI works out the subject, applies the matching rules, and decides how many cards to make.

Optional: to choose the count yourself, add a line at the end such as `Make 25 cards.` You can also change the ABOUT ME line to describe yourself.

```
You are an expert tutor and flashcard designer. Make flashcards for me to study in my flashcard app, from the material I attach or paste at the end of this message.

ABOUT ME: college IT student, beginner programmer. I want to UNDERSTAND concepts, not just memorise words.

## Step 1: Work out the topic and subject
Read ALL the material first. Work out the course, the topic, and which subject type it is: Networking, Cloud, Computer security, Law & ethics, Stats, or Other. Apply the matching SUBJECT RULES further down. If the material mixes subjects, apply each subject's rules to its own part. If I only named a topic and gave no material, use standard, well-established textbook knowledge.

## Step 2: Decide how many cards
- One important idea = one card. List the key ideas in the material, then make exactly as many cards as you need to cover all of them. Do not pad with trivial facts, and do not squeeze several ideas into one card.
- Typical sizes: a short topic needs 15–25 lines, one lecture or slide deck needs 30–50. Plan about 1–1.5 lines per content slide; slides with comparisons or processes need 2–3. Skip title, agenda and review slides.
- Maximum 50 lines per set. If the material needs more, stop at 50 at a natural break between subtopics and tell me what is left, so I can ask you for "Part 2".
- If I wrote a number of cards at the end of this message, use my number instead.

## Goal
Cards that make me THINK. Cover the most important ideas first. Build from foundations to advanced ideas, so later cards build on earlier ones.

## How my app grades me (design the cards for this)
- I usually see the TERM and write the DEFINITION in my own words. An AI grades my answer by MEANING and checks for the key ideas and qualifiers.
- Sometimes I see the definition and must type the term exactly. So terms must be short and exact.
- The app notices when my answer describes a DIFFERENT card in the set and flags it as a mix-up. So include concepts that are easy to confuse.

## Card types (use a mix, roughly 60% basic and 40% fill-in-the-blank)
1. BASIC CARDS, for concepts and comparisons
   - Term: 1–5 words, exact (e.g. "OSPF", "Administrative distance"). Never a question.
   - Definition: ONE clear sentence of at most 25 words (30 for Law & ethics) that contains:
     (a) what it is, and (b) the key feature that makes it different from similar concepts.
     Put the distinguishing detail in the definition (e.g. "...unlike RIP, it uses cost instead of hop count").
   - Never repeat the term inside its own definition.
2. FILL-IN-THE-BLANK CARDS, for facts, numbers, processes, cause and effect
   - Write one sentence and hide the important words with {{c1::answer}}, {{c2::answer}}, and so on. Each number becomes its own card, so hide 1–3 things per sentence, never trivial words.
   - Add a hint with {{c1::answer::hint}} when the blank would be ambiguous (e.g. {{c1::22::port number}}).
   - Use them for: numbers, ordered steps ("the {{c1::DORA}} process..."), cause and effect ("if X happens, {{c1::Y}} because {{c2::Z}}"), and "why" explanations.

## Make it challenging
- Include 3–5 CONFUSABLE PAIRS, each concept with its own card. Their definitions must make the difference obvious.
- Include "why" and "what happens if" knowledge, not only "what is".
- Include 2–4 short SCENARIO cards as fill-in-the-blank: "A host gets 169.254.x.x, which means {{c1::the DHCP server was unreachable::cause}}."
- One idea per card. No lists of more than 3 items in one answer. Split big ideas into several cards.
- No trick questions, no vague wording, nothing outside the source material unless it's standard, well-established knowledge.
- Use plain, simple English, but keep the correct technical terms.

## SUBJECT RULES (apply the one that matches)
NETWORKING: Include port numbers, protocol comparisons (TCP/UDP, OSPF/EIGRP, hub/switch, router/switch), ordered processes (DORA, three-way handshake), and troubleshooting scenarios ("a host can ping by IP but not by name, so {{c1::DNS}} is failing").
CLOUD: Compare similar services (IaaS/PaaS/SaaS, scaling up vs out, region vs availability zone). Include scenario blanks: "A company needs X, so it should use {{c1::service}} because {{c2::reason}}." Include the shared responsibility model: who secures what.
COMPUTER SECURITY: Pair every attack with its defence on separate cards. Include confusable pairs (authentication/authorization, symmetric/asymmetric, IDS/IPS, vulnerability/threat/risk, hashing/encryption). Include "what happens if" scenarios and which part of the CIA triad each attack breaks.
LAW & ETHICS: Use Canadian law where relevant, only as stated in my source material. Do NOT invent section numbers, case names or penalties. Definitions may be up to 30 words. Include confusable pairs (privacy/confidentiality, copyright/patent/trademark, law/ethics, consent/implied consent). At least 30% of cards should be scenario blanks: "An employee does X, which is {{c1::legal concept}} because {{c2::reason}}." Include the main ethical frameworks and how each would judge a situation.
STATS: Focus on understanding, not calculation. Cover what each measure means in plain words, WHEN to use each test or formula, how to interpret results ("a p-value of 0.03 means {{c1::...}}"), and common mistakes. Write formulas in plain text (e.g. "mean = sum of values / number of values"); no LaTeX or special symbols. Include confusable pairs (mean/median, population/sample, standard deviation/variance, correlation/causation, Type I/Type II error).
OTHER: Follow the general rules above. Pick confusable pairs and scenarios that fit the subject.

## Output format (strict, so I can paste it straight into my app)
- Put ALL cards inside ONE code block, one card per line, no blank lines.
- Basic card:            Term | Definition
- Fill-in-the-blank:     Sentence with {{c1::answer}} | optional extra note shown after answering (or nothing after the |)
- Use the | character ONLY as the separator. Never use | anywhere else, and never use tabs.
- No numbering, no bullet points, no headings, no bold, no extra text inside the code block.

After the code block, give me:
1. A suggested SET TITLE (add "Part 1" if a Part 2 is needed).
2. The subject type you detected.
3. The card count: number of lines, and total cards in the app (each {{cN}} blank counts as its own card).
4. Whether a Part 2 is needed, and which subtopics it should cover.
5. The confusable pairs you included (one line each).
6. Anything in the source that was unclear, or that you left out.

Before answering, check every line: one | only, terms short, definitions one sentence, blanks balanced {{ }}, every key idea covered once.

MY MATERIAL:
```

## Warnings
- **Stats:** flashcards don't replace solving problems. Learn from worked examples first, taught from the ground up, then practise problems; use the cards for *when* and *why*.
- **Law:** AI can invent section numbers and case names that sound real. Check any card citing a specific section against your course notes.
- **Part 2:** if the AI says a Part 2 is needed, reply in the same chat: `Make Part 2 with the same rules.`

## How to import
1. In QuizCraft, go to Library → **Import**.
2. Paste the lines from the code block and give the set a title.
3. Under **Between term and definition**, choose **Custom** and type `|`. Leave **Between cards** as **New line**.
4. Check that the preview count matches the AI's number of **lines** (the preview counts lines; fill-in-the-blank lines with several blanks become more cards after import), then tap **Create set**.

## Best way to study these cards
- **New set:** Learn, then Write with *Answer with: Definition* (AI feedback), with strictness on **Lenient**.
- **Daily:** Review (the due cards only).
- **Exam week:** Write on **Strict**, then Test and Timed exam.
- **Mix-ups:** check Progress → Weak spots → *Mixed-up terms*.
- **Multiple choice:** open the set once while signed in so it gets **✓ AI-checked**, and look at any *cards to review* it flags.
