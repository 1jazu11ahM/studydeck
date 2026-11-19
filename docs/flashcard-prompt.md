# Prompt: generate QuizCraft flashcards

Paste the prompt below into any AI chat (Claude works well). Fill in the three [brackets], add the **subject add-on** for your course right under the TOPIC line, then attach or paste your lecture notes, slides or textbook section.

```
You are an expert tutor and flashcard designer. Make flashcards for me to study in my flashcard app.

TOPIC: [course and topic, e.g. "Advanced Networking – OSPF"]
LEVEL: [e.g. "2nd-year IT student"]
NUMBER OF CARDS: [e.g. 30]
SOURCE MATERIAL: [paste notes/slides below, or say "use standard textbook knowledge"]

## Goal
Cards that make me THINK and help me understand concepts, not just memorise words. Cover the most important ideas first. Build from foundations to advanced ideas, so later cards build on earlier ones.

## How my app grades me (design the cards for this)
- I usually see the TERM and write the DEFINITION in my own words. An AI grades my answer by MEANING and checks for the key ideas and qualifiers.
- Sometimes I see the definition and must type the term exactly. So terms must be short and exact.
- The app notices when my answer describes a DIFFERENT card in the set, and flags it as a mix-up. So include concepts that are easy to confuse.

## Card types (use a mix, roughly 60% basic and 40% fill-in-the-blank)
1. BASIC CARDS, for concepts and comparisons
   - Term: 1–5 words, exact (e.g. "OSPF", "Administrative distance"). Never a question.
   - Definition: ONE clear sentence of at most 25 words that contains:
     (a) what it is, and (b) the key feature that makes it different from similar concepts.
     Put the distinguishing detail in the definition (e.g. "...unlike RIP, it uses cost instead of hop count").
   - Never repeat the term inside its own definition.
2. FILL-IN-THE-BLANK CARDS, for facts, numbers, processes, cause and effect
   - Write one sentence and hide the important words with {{c1::answer}}, {{c2::answer}}, and so on. Each number becomes its own card, so hide 1–3 things per sentence, never trivial words.
   - Add a hint with {{c1::answer::hint}} when the blank would be ambiguous (e.g. {{c1::22::port number}}).
   - Use them for: port numbers, ordered steps ("the {{c1::DORA}} process..."), cause and effect ("if X happens, {{c1::Y}} because {{c2::Z}}"), and "why" explanations.

## Make it challenging
- Include 3–5 CONFUSABLE PAIRS (e.g. TCP/UDP, OSPF/EIGRP, hub/switch, authentication/authorization), each with its own card. Their definitions must make the difference obvious.
- Include "why" and "what happens if" knowledge, not only "what is".
- Include 2–4 short SCENARIO cards as fill-in-the-blank: "A host gets 169.254.x.x, which means {{c1::the DHCP server was unreachable::cause}}."
- One idea per card. No lists of more than 3 items in one answer. Split big ideas into several cards.
- No trick questions, no vague wording, nothing outside the source material unless it's standard, well-established knowledge.
- Use plain, simple English, but keep the correct technical terms.

## Output format (strict, so I can paste it straight into my app)
- Put ALL cards inside ONE code block, one card per line, no blank lines.
- Basic card:            Term | Definition
- Fill-in-the-blank:     Sentence with {{c1::answer}} | optional extra note shown after answering (or nothing after the |)
- Use the | character ONLY as the separator. Never use | anywhere else, and never use tabs.
- No numbering, no bullet points, no headings, no bold, no extra text inside the code block.

After the code block, give me:
1. A suggested SET TITLE.
2. The confusable pairs you included (one line each).
3. Anything in the source that was unclear, or that you left out.

Before answering, check every line: one | only, terms short, definitions one sentence, blanks balanced {{ }}.
```

## Subject add-ons (paste the matching one under the TOPIC line)

| Subject | Fit | What changes |
|---|---|---|
| Networking | Great | Nothing; the prompt was built around it |
| Cloud | Great | Service comparisons and "which service for this need" scenarios |
| Computer security | Great | Attack → defence pairs and "what happens if" scenarios |
| Law & ethics | Good with tweaks | Longer definitions; scenarios matter most |
| Stats | Partly | Cards teach when to use what and what results mean, not how to solve problems |

**Cloud**
```
SUBJECT NOTES: Compare similar services (e.g. IaaS/PaaS/SaaS, scaling up vs out, region vs availability zone). Include scenario blanks: "A company needs X, so it should use {{c1::service}} because {{c2::reason}}." Include the shared responsibility model: who secures what.
```

**Computer security**
```
SUBJECT NOTES: Pair every attack with its defence on separate cards. Include confusable pairs (authentication/authorization, symmetric/asymmetric, IDS/IPS, vulnerability/threat/risk, hashing/encryption). Include "what happens if" scenarios and which part of the CIA triad each attack breaks.
```

**Law & ethics for IT**
```
SUBJECT NOTES: Use Canadian law where relevant, only as stated in my source material. Do not invent section numbers, case names or penalties. Definitions may be up to 30 words. Include confusable pairs (privacy/confidentiality, copyright/patent/trademark, law/ethics, consent/implied consent). At least 30% of cards should be scenario blanks: "An employee does X, which is {{c1::legal concept}} because {{c2::reason}}." Include the main ethical frameworks and how each would judge a situation.
```

**Stats**
```
SUBJECT NOTES: Focus on understanding, not calculation. Cards should cover: what each measure means in plain words, WHEN to use each test or formula, how to interpret results ("a p-value of 0.03 means {{c1::...}}"), and common mistakes. Write formulas in plain text (e.g. "mean = sum of values / number of values"); no LaTeX or symbols my app can't show. Include confusable pairs (mean/median, population/sample, standard deviation/variance, correlation/causation, Type I/Type II error).
```

**Warnings**
- **Stats:** flashcards don't replace solving problems. Learn from worked examples first, taught from the ground up, then practise problems; use the cards for *when* and *why*.
- **Law:** AI can invent section numbers and case names that sound real. Check any card citing a specific section against your course notes.

## How to import
1. In QuizCraft, go to Library → **Import**.
2. Paste the lines from the code block and give the set a title.
3. Under **Between term and definition**, choose **Custom** and type `|`. Leave **Between cards** as **New line**.
4. Check the preview count, then tap **Create set**.

## Best way to study these cards
- **New set:** Learn, then Write with *Answer with: Definition* (AI feedback), with strictness on **Lenient**.
- **Daily:** Review (the due cards only).
- **Exam week:** Write on **Strict**, then Test and Timed exam.
- **Mix-ups:** check Progress → Weak spots → *Mixed-up terms*.
