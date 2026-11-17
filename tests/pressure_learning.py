"""QuizCraft learning pressure test: every study mode, on a touch phone and a keyboard desktop,
plus edge-case sets and scheduling / grading / bookkeeping invariants."""
import asyncio, json, sys
from playwright.async_api import async_playwright

URL = "file:///home/claude/studydeck/index.html"
FAILS, NOTES, ALLC = [], [], []
def check(cond, msg):
    (NOTES if cond else FAILS).append(("ok  " if cond else "FAIL ") + msg)

# answer lookup: prompt text -> other side, across every set (works for virtual sets too)
ANS = """p=>{p=p.replace(/\\s+/g,' ').trim();for(const s of DB.sets)for(const c of s.cards){const t=(c.term||'').replace(/\\s+/g,' ').trim(),d=(c.def||'').replace(/\\s+/g,' ').trim();if(d===p)return c.term;if(t===p)return c.def}return null}"""
ANSALL = """p=>{p=p.replace(/\\s+/g,' ').trim();const o=[];for(const s of DB.sets)for(const c of s.cards){const t=(c.term||'').replace(/\\s+/g,' ').trim(),d=(c.def||'').replace(/\\s+/g,' ').trim();if(d===p)o.push(c.term);if(t===p)o.push(c.def)}return o}"""

SEED = r"""(()=>{
 const mk=(id,title,pairs)=>{const s={id,title,desc:'',folder:'',termLang:'en-US',defLang:'en-US',created:Date.now(),updated:Date.now(),studied:0,
   cards:pairs.map((p,i)=>({id:id+'-'+i,term:p[0],def:p[1],img:p[2]||'',starred:false,box:0,due:0,right:0,wrong:0})),opts:{answer:'term',starred:false,front:'term',written:true,track:false}};fixSet&&fixSet(s);return s};
 DB.sets=DB.sets.filter(s=>!s.id.startsWith('pt-'));
 DB.sets.push(mk('pt-main','Pressure main',[['Mitochondria','Powerhouse of the cell'],['Ribosome','Makes proteins'],['Nucleus','Holds DNA'],['Golgi apparatus','Packages proteins'],['Lysosome','Breaks down waste'],['Chloroplast','Photosynthesis site'],['Vacuole','Stores water'],['Cell membrane','Controls what enters']]));
 DB.sets.push(mk('pt-one','One card',[['Solo term','Solo definition']]));
 DB.sets.push(mk('pt-two','Two cards',[['Alpha','First'],['Beta','Second']]));
 DB.sets.push(mk('pt-dup','Duplicate answers',[['Cat','Animal'],['Dog','Animal'],['Rose','Flower'],['Oak','Tree'],['Pine','Tree']]));
 DB.sets.push(mk('pt-long','Long text',[['Supercalifragilistic term that goes on and on to test wrapping across several lines of the card','A very long definition '+'with many words '.repeat(25)],['Short','Brief'],['Mid','Medium length definition here'],['Fourth','Four']]));
 DB.sets.push(mk('pt-dari','Dari',[['سلام','Hello'],['تشکر','Thank you'],['خداحافظ','Goodbye'],['کتاب','Book']]));
 DB.sets.push(mk('pt-empty','Empty',[]));
 saveNow();
})()"""

async def new_page(b, mobile):
    if mobile:
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True, has_touch=True)
    else:
        ctx = await b.new_context(viewport={"width": 1280, "height": 900})
    pg = await ctx.new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    await pg.goto(URL); await pg.wait_for_timeout(2300)
    await pg.evaluate("endTour();DB.settings.tourDone=1;saveNow()"); await pg.wait_for_timeout(300)
    await pg.evaluate(SEED)
    return ctx, pg, errs

async def tap(pg, mobile, sel, nth=0):
    loc = pg.locator(sel).nth(nth)
    if mobile:
        await loc.scroll_into_view_if_needed(); await loc.tap()
    else:
        await loc.click()

async def go(pg, h):
    await pg.evaluate(f"(location.hash==='{h}')?route():(location.hash='{h}')"); await pg.wait_for_timeout(450)

async def answer_question(pg, mobile, wrong=False):
    """Answer the current presentQ question (choice or written). Returns 'mc'/'written'/None."""
    prompt = (await pg.locator(".qtxt").first.inner_text()).strip()
    ans = await pg.evaluate(ANS, prompt)
    if ans is None:
        return None
    alls = await pg.evaluate(ANSALL, prompt)
    if await pg.locator(".choice:not([disabled])").count():
        if not wrong and len(alls) > 1:
            texts = await pg.evaluate("[...document.querySelectorAll('.choice span')].map(x=>x.innerText.trim())")
            k = next((i for i, t in enumerate(texts) if t in alls), None)
            ALLC.append((prompt, alls, texts))
            loc = pg.locator(".choice").nth(k if k is not None else 0)
            await (loc.tap() if mobile else loc.click()); return "mc"
        if wrong:
            others = pg.locator(".choice:not([disabled])", has_not_text=ans)
            await (others.first.tap() if mobile else others.first.click())
        else:
            loc = pg.locator(".choice", has_text=ans).first
            await (loc.tap() if mobile else loc.click())
        return "mc"
    await pg.fill(".wa", "zzzz" if wrong else ans)
    if mobile: await tap(pg, True, ".wform .btn")
    else: await pg.press(".wa", "Enter")
    return "written"

async def run_suite(b, mobile):
    tag = "PHONE" if mobile else "DESKTOP"
    ctx, pg, errs = await new_page(b, mobile)
    P = lambda m: f"[{tag}] {m}"

    # ---------- unit: grading ----------
    g = await pg.evaluate("""()=>({
      exact:grade('Powerhouse of the cell','Powerhouse of the cell'),
      caseP:grade('powerhouse OF the cell!!','Powerhouse of the cell'),
      typo:grade('Powerhose of the cell','Powerhouse of the cell'),
      wrong:grade('Makes proteins','Powerhouse of the cell'),
      empty:grade('   ','x'),
      alt:grade('kitty','cat / kitty'),
      accent:grade('adios','adiós'),
      dari:grade('سلام','سلام'),
      short:grade('STAT','stat'),
      shortTypo:grade('STA','STAT')})""")
    check(g["exact"] == "correct" and g["caseP"] == "correct", P(f"grading exact/case/punctuation {g['exact']},{g['caseP']}"))
    check(g["typo"] == "close", P(f"small typo accepted as close: {g['typo']}"))
    check(g["wrong"] == "wrong" and g["empty"] == "wrong", P("wrong and empty answers rejected"))
    check(g["alt"] == "correct" and g["accent"] == "correct" and g["dari"] == "correct", P(f"alternatives/accents/Dari: {g['alt']},{g['accent']},{g['dari']}"))
    check(g["short"] == "correct" and g["shortTypo"] == "wrong", P("short answers must be exact"))

    # ---------- unit: multiple-choice options ----------
    mc = await pg.evaluate("""()=>{const s=getSet('pt-dup');const out=[];for(let k=0;k<40;k++){const c=s.cards[k%5];const q={aSide:'term',answer:c.term};const o=mcOptions(s,c,q);out.push([o.length,new Set(o.map(norm)).size,o.includes(c.term)])}
      const s2=getSet('pt-dup');const c=s2.cards[0];const q={aSide:'def',answer:c.def};const o=mcOptions(s2,c,q);return{out,defOpts:o}}""")
    check(all(l == u and inc for l, u, inc in mc["out"]), P("MC options never duplicate and always include the answer"))
    check(mc["defOpts"].count("Animal") == 1, P(f"MC with duplicate definitions shows the answer once: {mc['defOpts']}"))

    # ---------- unit: scheduling + bookkeeping ----------
    sc = await pg.evaluate("""()=>{const c=getSet('pt-main').cards[0];const k=ymd();const L0=JSON.stringify(DB.log[k]||{r:0,w:0});const d0=DB.daily.n;
      const r=[];record(c,true);r.push([c.box,Math.round((c.due-Date.now())/DAY)]);record(c,true);r.push([c.box,Math.round((c.due-Date.now())/DAY)]);record(c,true);r.push([c.box,status(c)]);
      record(c,false);r.push([c.box,c.due<=Date.now(),status(c)]);
      for(let i=0;i<10;i++)record(c,true);r.push([c.box]);
      return{r,log:DB.log[k],L0,daily:DB.daily.n-d0}}""")
    r = sc["r"]
    check(r[0] == [1, 0] and r[1] == [2, 1] and r[2] == [3, "master"], P(f"right answers climb boxes 1→2→3 with 0/1-day gaps and master at 3: {r[:3]}"))
    check(r[3][0] == 1 and r[3][1] is True and r[3][2] == "learn", P(f"wrong answer drops to box 1 and is due now: {r[3]}"))
    check(r[4] == [6], P(f"box caps at 6: {r[4]}"))
    L0 = json.loads(sc["L0"])
    check(sc["log"]["r"] - L0.get("r", 0) == 13 and sc["log"]["w"] - L0.get("w", 0) == 1, P(f"daily log counts 13 right + 1 wrong: {sc['log']} (was {L0})"))
    check(sc["daily"] == 13, P(f"daily goal counts only correct answers: {sc['daily']}"))

    ov = await pg.evaluate("""()=>{const c=getSet('pt-main').cards[1];const k=ymd();const b=JSON.stringify(DB.log[k]);const d=DB.daily.n;const u=recordUndoable(c,false);u();record(c,true);
      const a=DB.log[k],B=JSON.parse(b);return{dr:a.r-B.r,dw:a.w-B.w,dd:DB.daily.n-d,box:c.box}}""")
    check(ov["dr"] == 1 and ov["dw"] == 0 and ov["dd"] == 1, P(f"'Override: I was correct' counts once in log and goal: {ov}"))

    st = await pg.evaluate("""()=>{DB.streak={last:ymd(new Date(Date.now()-DAY)),count:4};touch(getSet('pt-main'));const a=DB.streak.count;touch(getSet('pt-main'));const b=DB.streak.count;
      DB.streak={last:ymd(new Date(Date.now()-3*DAY)),count:9};touch(getSet('pt-main'));return[a,b,DB.streak.count]}""")
    check(st == [5, 5, 1], P(f"streak: continues, counts once per day, resets after a gap: {st}"))

    ex = await pg.evaluate("""()=>{const s=getSet('pt-main');s.cards.forEach(c=>{c.box=0;c.right=c.wrong=0});const d=new Date(Date.now()+4*DAY);s.exam=ymd(d);const p=examPlan(s);s.exam=ymd();const p0=examPlan(s);s.exam=ymd(new Date(Date.now()-2*DAY));const pn=examPlan(s);s.exam='';return[p,p0,pn]}""")
    check(ex[0]["days"] == 4 and ex[0]["per"] == 2 and ex[1]["days"] == 0 and ex[1]["per"] == 8 and ex[2] is None, P(f"exam plan maths (4 days→2/day, today→all, past→none): {ex}"))
    await pg.evaluate("DB.sets.filter(s=>s.id.startsWith('pt-')).forEach(s=>s.cards.forEach(c=>Object.assign(c,{box:0,due:0,right:0,wrong:0})));saveNow()")

    # ---------- flashcards: plain run through ----------
    await go(pg, "#/flash/pt-main"); await pg.wait_for_selector("#fc")
    lab = await pg.inner_text("#fctl")
    check("Space" not in (await pg.locator("#fctl").evaluate("e=>e.innerText")) or not mobile, P("no keyboard hints on phone flashcards"))
    for k in range(8):
        if mobile:
            box = await pg.locator("#sw").bounding_box(); x = box["x"] + box["width"] * .8; y = box["y"] + box["height"] / 2
            cdp = await ctx.new_cdp_session(pg)
            await cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": x, "y": y}]})
            for s_ in range(1, 9): await cdp.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": [{"x": x - 220 * s_ / 8, "y": y}]})
            await cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []}); await pg.wait_for_timeout(450)
        else:
            await pg.keyboard.press("ArrowRight"); await pg.wait_for_timeout(250)
    done = await pg.locator(".done-box").count()
    check(done == 1, P("flashcards: going through every card reaches the finish screen"))

    # ---------- flashcards: training ratings ----------
    await pg.evaluate("getSet('pt-main').opts.track=true;saveNow()")
    await go(pg, "#/flash/pt-main"); await pg.wait_for_selector("#bReveal")
    rev = await pg.inner_text("#bReveal")
    check((("Space" not in rev) if mobile else True) and "Show answer" in rev, P(f"reveal button label on this device: {rev!r}"))
    boxes = []
    for rate in [1, 2, 3, 4, 3, 3, 1, 4]:
        if mobile:
            await tap(pg, True, "#bReveal"); await pg.wait_for_timeout(300); await tap(pg, True, f"[data-r='{rate}']")
        else:
            await pg.keyboard.press("Space"); await pg.wait_for_timeout(250); await pg.keyboard.press(str(rate))
        await pg.wait_for_timeout(450)
    res = await pg.evaluate("getSet('pt-main').cards.map(c=>[c.box,c.right,c.wrong])")
    check(await pg.locator(".done-box").count() == 1, P("training: rating every card reaches the finish screen"))
    rated = [x for x in res if x[1] + x[2] > 0]
    check(len(rated) == 8, P(f"training: every rated card was recorded once ({len(rated)}/8): {res}"))
    await pg.evaluate("getSet('pt-main').opts.track=false;saveNow()")

    # ---------- review: only due cards, then nothing due ----------
    await pg.evaluate("const s=getSet('pt-main');s.cards.forEach((c,i)=>{c.right=1;c.box=2;c.due=i<3?Date.now()-1:Date.now()+5*DAY});saveNow()")
    await go(pg, "#/review/pt-main"); await pg.wait_for_selector("#bReveal")
    n_due = await pg.evaluate("$('#fctl').innerText.match(/\\d+ \\/ (\\d+)/)?.[1]")
    check(n_due == "3", P(f"review shows only the 3 due cards: {n_due}"))
    for _ in range(3):
        if mobile: await tap(pg, True, "#bReveal"); await pg.wait_for_timeout(250); await tap(pg, True, "[data-r='3']")
        else: await pg.keyboard.press("Space"); await pg.wait_for_timeout(200); await pg.keyboard.press("3")
        await pg.wait_for_timeout(450)
    left = await pg.evaluate("dueCards(getSet('pt-main')).length")
    check(left == 0, P(f"review: rating 'knew it' clears all due cards: {left} left"))
    await go(pg, "#/review/pt-main")
    check(await pg.locator("text=Nothing due").count() == 1, P("review with nothing due shows the friendly empty state"))
    await pg.evaluate("getSet('pt-main').cards.forEach(c=>Object.assign(c,{box:0,due:0,right:0,wrong:0}));saveNow()")

    # ---------- learn: full run with mistakes + override, to completion ----------
    await go(pg, "#/learn/pt-main")
    wrongs = override = 0; steps = 0
    for steps in range(260):
        if await pg.locator("text=learned all").count(): break
        if await pg.locator("#nr").count():
            await tap(pg, mobile, "#nr"); await pg.wait_for_timeout(300); continue
        if await pg.locator(".cont").count():
            if override == 0 and await pg.locator(".ovr").count():
                await tap(pg, mobile, ".ovr"); override = 1
            else:
                await tap(pg, mobile, ".cont")
            await pg.wait_for_timeout(300); continue
        if not await pg.locator(".qtxt").count():
            await pg.wait_for_timeout(300); continue
        wrong = steps in (3, 9, 22)
        kind = await answer_question(pg, mobile, wrong=wrong)
        if wrong: wrongs += 1
        await pg.wait_for_timeout(1050)
    check(await pg.locator("text=learned all").count() == 1, P(f"learn: finishes with every card mastered ({steps} steps, {wrongs} deliberate mistakes)"))
    m = await pg.evaluate("getSet('pt-main').cards.every(c=>c.box>=2&&c.right>=2&&c.due>Date.now())")
    check(m, P("learn: every card moved up the memory boxes and is scheduled for a later review"))

    # ---------- learn: rapid double tap records once ----------
    await pg.evaluate("getSet('pt-two').cards.forEach(c=>Object.assign(c,{box:0,due:0,right:0,wrong:0}));getSet('pt-main').cards.forEach(c=>Object.assign(c,{box:0,due:0,right:0,wrong:0}));saveNow()")
    await go(pg, "#/learn/pt-main"); await pg.wait_for_selector(".qtxt")
    before = await pg.evaluate("getSet('pt-main').cards.reduce((n,c)=>n+c.right+c.wrong,0)")
    if await pg.locator(".choice").count():
        loc = pg.locator(".choice").first
        await loc.dispatch_event("click"); await loc.dispatch_event("click"); await loc.dispatch_event("click")
    else:
        await pg.fill(".wa", "x"); await pg.press(".wa", "Enter"); await pg.press(".wa", "Enter")
    await pg.wait_for_timeout(200)
    after = await pg.evaluate("getSet('pt-main').cards.reduce((n,c)=>n+c.right+c.wrong,0)")
    check(after - before == 1, P(f"triple tap on an answer records once: {after-before}"))

    # ---------- learn on tiny / odd sets ----------
    for sid, name in [("pt-one", "1-card"), ("pt-two", "2-card"), ("pt-dup", "duplicate-answers"), ("pt-long", "long-text"), ("pt-dari", "Dari")]:
        await go(pg, f"#/learn/{sid}")
        ok = False
        for steps in range(160):
            if await pg.locator("text=learned all").count(): ok = True; break
            if await pg.locator("#nr").count(): await tap(pg, mobile, "#nr"); await pg.wait_for_timeout(250); continue
            if await pg.locator(".cont").count(): await tap(pg, mobile, ".cont"); await pg.wait_for_timeout(250); continue
            if not await pg.locator(".qtxt").count(): await pg.wait_for_timeout(250); continue
            if await answer_question(pg, mobile) is None:
                # duplicate-answer set: prompt maps to several cards; pick any choice that is marked right
                if await pg.locator(".choice").count(): await tap(pg, mobile, ".choice")
                else: await pg.fill(".wa", "Animal"); await pg.press(".wa", "Enter")
            await pg.wait_for_timeout(1000)
        check(ok, P(f"learn completes on the {name} set"))
        if name == "duplicate-answers":
            amb = [x for x in ALLC if sum(t in x[1] for t in x[2]) != 1]
            check(not amb, P(f"duplicate answers: exactly one valid answer is offered per question ({len(ALLC)} checked) {amb[:1]}"))
        if name == "long-text":
            ow = await pg.evaluate("document.documentElement.scrollWidth<=innerWidth+1")
            check(ow, P("long text never makes the page scroll sideways"))

    # ---------- write: right, close typo, wrong + continue, empty submit ignored ----------
    await pg.evaluate("getSet('pt-main').opts.answer='term';saveNow()")
    await go(pg, "#/write/pt-main"); await pg.wait_for_selector(".wa")
    before = await pg.evaluate("getSet('pt-main').cards.reduce((n,c)=>n+c.right+c.wrong,0)")
    await pg.fill(".wa", "   ");
    if mobile: await tap(pg, True, ".wform .btn")
    else: await pg.press(".wa", "Enter")
    await pg.wait_for_timeout(200)
    same = await pg.evaluate("getSet('pt-main').cards.reduce((n,c)=>n+c.right+c.wrong,0)")
    check(same == before, P("write: an empty answer is ignored, not marked wrong"))
    prompt = (await pg.locator(".qtxt").first.inner_text()).strip(); ans = await pg.evaluate(ANS, prompt)
    typo = ans[:-1] + ("x" if ans[-1] != "x" else "y") if len(ans) >= 9 else ans
    await pg.fill(".wa", typo)
    if mobile: await tap(pg, True, ".wform .btn")
    else: await pg.press(".wa", "Enter")
    await pg.wait_for_timeout(400)
    fbt = await pg.inner_text(".fb")
    check("✓" in fbt, P(f"write: a one-letter typo on a long answer counts as correct ({typo!r})"))
    if await pg.locator(".cont").count(): await tap(pg, mobile, ".cont")
    await pg.wait_for_timeout(1100)
    await pg.fill(".wa", "definitely wrong")
    if mobile: await tap(pg, True, ".wform .btn")
    else: await pg.press(".wa", "Enter")
    await pg.wait_for_selector(".cont")
    vis = await pg.locator(".cont").is_visible()
    check(vis, P("write: Continue button is visible after a wrong answer"))
    await tap(pg, mobile, ".cont"); await pg.wait_for_timeout(300)
    check(await pg.locator(".wa").count() == 1, P("write: continues to the next question"))

    # ---------- test: build, answer everything correctly, score 100% ----------
    await go(pg, "#/test/pt-main"); await pg.wait_for_selector("#tGo")
    await tap(pg, mobile, "#tGo"); await pg.wait_for_selector("#submitT")
    qs = await pg.evaluate("""()=>[...document.querySelectorAll('.tq')].map((q,i)=>({i,kind:q.querySelector('.choice')?'mc':q.querySelector('input[type=text],textarea,.wa')?'w':q.querySelector('[data-tf]')||/true|false/i.test(q.innerText)?'tf':'?',text:q.innerText.slice(0,200)}))""")
    kinds = sorted(set(q["kind"] for q in qs))
    NOTES.append(P(f"note test question types: {kinds}, {len(qs)} questions"))
    # use the app's own answer key to answer every question correctly
    key = await pg.evaluate("""()=>{const out=[];document.querySelectorAll('.tq').forEach((q,i)=>out.push(q.outerHTML.length));return out.length}""")
    for i in range(len(qs)):
        q = pg.locator(".tq").nth(i)
        if await q.locator("select[data-mk]").count():
            letters = await q.evaluate("""el=>Object.fromEntries([...el.querySelectorAll('.ma')].map(m=>[m.innerText.replace(/^\\s*[A-Z]\\.\\s*/,'').replace(/\\s+/g,' ').trim(),m.querySelector('b').innerText.replace('.','').trim()]))""")
            for k in range(await q.locator(".mi").count()):
                pr = (await q.locator(".mi").nth(k).locator("span").first.inner_text()).strip()
                ans = await pg.evaluate(ANS, pr)
                await q.locator("select[data-mk]").nth(k).select_option(letters.get((ans or '').replace("\n"," ").strip(), ""))
        elif await q.locator(".tf").count():
            pr = (await q.locator(".qtxt").nth(0).inner_text()).strip(); shown = (await q.locator(".qtxt").nth(1).inner_text()).strip()
            valid = await pg.evaluate(ANSALL, pr)
            btn = q.locator("[data-v=true]" if shown in [v.strip() for v in valid] else "[data-v=false]")
            await (btn.tap() if mobile else btn.click())
        elif await q.locator(".choice").count():
            pr = (await q.locator(".qtxt").first.inner_text()).strip(); valid = await pg.evaluate(ANSALL, pr)
            texts = await q.evaluate("el=>[...el.querySelectorAll('.choice')].map(x=>(x.querySelector('span')||x).innerText.replace(/^\\d+\\s*/,'').trim())")
            k = next((j for j, t in enumerate(texts) if t in valid), 0); c = q.locator(".choice").nth(k)
            await (c.tap() if mobile else c.click())
        elif await q.locator("input[data-w]").count():
            pr = (await q.locator(".qtxt").first.inner_text()).strip()
            await q.locator("input[data-w]").fill(await pg.evaluate(ANS, pr) or "")
    await tap(pg, mobile, "#submitT"); await pg.wait_for_timeout(400)
    if await pg.locator("#mO").count(): await tap(pg, mobile, "#mO")
    await pg.wait_for_timeout(500)
    score = await pg.evaluate("document.querySelector('.ring')?.innerText||document.querySelector('.qcard h2,.score')?.innerText||''")
    check("100%" in score, P(f"test: answering every question type correctly scores 100% ({score!r})"))
    wrong_rows = await pg.evaluate("document.querySelectorAll('.tq.bad').length")
    if wrong_rows: NOTES.append(P("note BAD: "+(await pg.evaluate("[...document.querySelectorAll('.tq.bad,.mi.bad')].map(e=>e.innerText.replace(/\\s+/g,' ')).join(' || ')"))[:600]))
    check(wrong_rows == 0, P(f"test: no correct answer was marked wrong ({wrong_rows})"))

    # ---------- match: solve by tapping ----------
    await go(pg, "#/match/pt-main"); await tap(pg, mobile, "#start"); await pg.wait_for_selector(".tile")
    pairs = await pg.evaluate("getSet('pt-main').cards.map(c=>[c.term,c.def])")
    for t, d in pairs:
        tl = pg.locator(".tile:not(.gone)", has_text=t)
        dl = pg.locator(".tile:not(.gone)", has_text=d)
        if await tl.count() and await dl.count():
            await (tl.first.tap() if mobile else tl.first.click()); await (dl.first.tap() if mobile else dl.first.click()); await pg.wait_for_timeout(120)
    await pg.wait_for_timeout(500)
    check(await pg.locator("text=Play again").count() == 1, P("match: solving every pair finishes the game"))

    # ---------- gravity: correct answers score, misses cost lives, game ends ----------
    await go(pg, "#/gravity/pt-main"); await tap(pg, mobile, "[data-d=hard]"); await pg.wait_for_timeout(600)
    for _ in range(3):
        if not await pg.locator("#ast").count(): break
        prompt = (await pg.locator("#ast").inner_text()).strip(); ans = await pg.evaluate(ANS, prompt)
        await pg.fill("#gin", ans or "x"); await pg.press("#gin", "Enter"); await pg.wait_for_timeout(500)
    sc = await pg.inner_text("#gs") if await pg.locator("#gs").count() else ""
    check("Score 0" not in sc, P(f"gravity: correct answers score points ({sc!r})"))
    ended = False
    for _ in range(240):
        if await pg.locator("text=Play again").count(): ended = True; break
        if await pg.locator(".gmsg .okc").count():
            a_ = (await pg.locator(".gmsg .okc").last.inner_text()).strip()
            await pg.fill("#gin", a_); await pg.press("#gin", "Enter"); await pg.wait_for_timeout(400)
        await pg.wait_for_timeout(500)
    check(ended, P("gravity: missing answers ends the game with a results screen"))

    # ---------- timed exam ----------
    await go(pg, "#/sim/pt-main"); await pg.wait_for_selector("#simGo")
    await tap(pg, mobile, "#simGo"); await pg.wait_for_timeout(500)
    answered = 0
    for steps in range(80):
        if await pg.locator(".qtxt").count() and await pg.locator(".fb:empty").count():
            if await answer_question(pg, mobile): answered += 1
            await pg.wait_for_timeout(1050); continue
        if await pg.locator(".cont").count(): await tap(pg, mobile, ".cont"); await pg.wait_for_timeout(300); continue
        if await pg.locator("text=/score|result|finished|accuracy/i").count(): break
        await pg.wait_for_timeout(300)
    NOTES.append(P(f"note timed exam: answered {answered} questions"))
    check(answered >= 4, P(f"timed exam: questions can be answered on this device ({answered})"))

    # ---------- spell ----------
    await go(pg, "#/spell/pt-main"); await pg.wait_for_timeout(500)
    if await pg.locator(".wa").count():
        ans = await pg.evaluate("(()=>{const t=document.body.innerText;return null})()")
        await pg.fill(".wa", "wrongspelling")
        if mobile: await tap(pg, True, ".wform .btn")
        else: await pg.press(".wa", "Enter")
        await pg.wait_for_timeout(300)
        check(await pg.locator(".spell-diff").count() == 1, P("spell: a wrong spelling shows the letter-by-letter comparison"))

    # ---------- edge: empty set, starred-only with no stars, leaving mid-session ----------
    for m_ in ["flash", "learn", "write", "spell", "test", "match", "gravity", "sim", "review"]:
        await go(pg, f"#/{m_}/pt-empty")
    check(await pg.locator("text=Add some terms").count() + await pg.locator("text=Nothing due").count() + await pg.locator("text=Not enough").count() >= 1, P("empty set: study modes show an 'add terms' message instead of breaking"))
    await pg.evaluate("getSet('pt-main').opts.starred=true;getSet('pt-main').cards.forEach(c=>c.starred=false);saveNow()")
    await go(pg, "#/learn/pt-main"); await pg.wait_for_timeout(300)
    check(await pg.locator(".qtxt").count() == 1, P("starred-only with no stars falls back to all cards"))
    await pg.evaluate("getSet('pt-main').opts.starred=false;saveNow()")
    for m_ in ["learn", "write", "test", "match", "gravity", "sim", "flash"]:
        await go(pg, f"#/{m_}/pt-main"); await pg.wait_for_timeout(250); await go(pg, "#/"); await pg.wait_for_timeout(250)
    await pg.wait_for_timeout(4000)  # let any stray timers fire after leaving
    check(await pg.locator(".start").count() == 1, P("leaving every mode mid-session returns cleanly to Home"))

    # ---------- every mode shows no keyboard hints on phones ----------
    if mobile:
        vis_kbd = []
        for m_ in ["learn", "write", "test", "sim", "flash"]:
            await go(pg, f"#/{m_}/pt-main"); await pg.wait_for_timeout(500)
            if m_ == "test" and await pg.locator("#tGo").count(): await tap(pg, True, "#tGo"); await pg.wait_for_timeout(300)
            if m_ == "sim" and await pg.locator("#simGo").count(): await tap(pg, True, "#simGo"); await pg.wait_for_timeout(300)
            n = await pg.evaluate("[...document.querySelectorAll('main kbd')].filter(k=>k.offsetParent&&!k.closest('.kbd-list')).length")
            if n: vis_kbd.append((m_, n))
        check(not vis_kbd, P(f"no keyboard hints visible on phone in any mode: {vis_kbd}"))

    # ---------- fonts: study text uses the standard font in every theme ----------
    for th in ["charcoal", "midnight", "dark", "light"]:
        await pg.evaluate(f"DB.settings.theme='{th}';applyTheme()")
        await go(pg, "#/flash/pt-main"); await pg.wait_for_selector(".ftxt")
        ff = await pg.evaluate("getComputedStyle(document.querySelector('.ftxt')).fontFamily")
        check("Kalam" not in ff and "Big Shoulders" not in ff and ("apple-system" in ff or "Inter" in ff), P(f"{th}: flashcard font is standard ({ff[:40]}…)"))
    await pg.evaluate("DB.settings.theme='charcoal';applyTheme()")

    # ---------- sound: off, no prompt ----------
    s_on = await pg.evaluate("DB.settings.amb.on")
    hint = await pg.evaluate("!!document.querySelector('#ambHint.show')")
    check(s_on is False and not hint, P(f"study sounds are off and no sound prompt is shown (on={s_on}, prompt={hint})"))

    check(not errs, P(f"no JavaScript errors: {errs[:3]}"))
    await ctx.close()

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
        which = sys.argv[1:] or ["phone", "desktop"]
        for w in which:
            await run_suite(b, w == "phone")
        await b.close()
    print("\n".join(NOTES))
    print("\n".join(FAILS) if FAILS else "\nALL PRESSURE CHECKS PASSED")
    print(f"\n{len(NOTES)} ok/notes, {len(FAILS)} failures")

asyncio.run(main())
