"""AI tutor features: try again, explain more, mix-ups, mistake memory, strictness (stand-in AI)."""
import asyncio
from playwright.async_api import async_playwright
FAILS=[]
def check(c,m): print(("ok   " if c else "FAIL ")+m); (None if c else FAILS.append(m))
STUB = """()=>{window.__calls=[];user={id:'u1',email:'me@x.com'};
  sb={functions:{invoke:async(name,{body})=>{window.__calls.push(body);await new Promise(r=>setTimeout(r,200));
    if(body.ping)return{data:{ok:true,configured:true},error:null};
    if(body.mode==='explain')return{data:{simple:'Plain idea for '+body.term,analogy:'It is like sorting socks.',example:'A phone number 416-555-1234.',why:'Helps you remember more.',hook:'Chunk = chunks of chocolate.',mistake:body.given?'You described another idea.':''},error:null};
    const g=body.given.toLowerCase();
    if(g.includes('mix'))return{data:{verdict:'wrong',score:1,right:'',missing:'That is the other card.',better:'The right idea.',confused_with:body.others[0][0]},error:null};
    if(g.includes('good'))return{data:{verdict:'correct',score:9,right:'Yes.',missing:'',better:'The right idea.',confused_with:''},error:null};
    return{data:{verdict:'wrong',score:1,right:'',missing:'Not the idea.',better:'The right idea.',confused_with:''},error:null};}}};}"""
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--no-sandbox"])
        ctx=await b.new_context(viewport={"width":1280,"height":1000}); pg=await ctx.new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)))
        await pg.goto("file://" + __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.dirname(__import__("os").path.abspath(__file__))), "index.html") + ""); await pg.wait_for_timeout(1800); await pg.evaluate("endTour()")
        await pg.evaluate(STUB); await pg.evaluate("DB.sets[0].opts.answer='def';DB.settings.aiStrict='strict'")
        sid=await pg.evaluate("DB.sets[0].id")
        async def open_card(term=None):
            # put a chosen card first by starring only it isn't available; instead loop until it shows up
            for _ in range(30):
                await pg.evaluate("location.hash='#/home'"); await pg.wait_for_timeout(120)
                await pg.evaluate(f"location.hash='#/write/{sid}'"); await pg.wait_for_selector(".wa")
                q=(await pg.inner_text(".qtxt")).strip()
                if term is None or q==term: return q
            return None
        async def submit(v): await pg.fill(".wa",v); await pg.click(".wform button"); await pg.wait_for_selector(".fb .fbx:not(.aiwait)")
        # ---- 1. wrong answer, then Try again with the exact answer
        t=await open_card(); await submit("random words here")
        cid=await pg.evaluate(f"DB.sets[0].cards.find(x=>x.term.trim()==={t!r}).id")
        call=await pg.evaluate("__calls[__calls.length-1]")
        check(call.get("strictness")=="strict" and len(call.get("others",[]))==9, f"sends strictness and the 9 other cards: {call.get('strictness')}, {len(call.get('others',[]))}")
        check(await pg.locator(".tryb").count()==1 and await pg.locator(".xpl").count()==1, "wrong answer offers Try again and Explain more")
        await pg.click(".tryb")
        check(await pg.evaluate("document.querySelector('.reveal').hidden"), "Try again hides the answer while you rewrite it")
        # Enter inside the retry box must not skip the card
        defn=await pg.evaluate(f"DB.sets[0].cards.find(x=>x.id==='{cid}').def")
        await pg.fill(".wa2",defn); await pg.press(".wa2","Enter"); await pg.wait_for_timeout(500)
        txt=await pg.inner_text(".fb")
        check("Got it now" in txt and await pg.locator(".fb").count()==1, "Enter checks the retry (doesn't skip the card); exact answer: 'Got it now'")
        check(not await pg.evaluate("document.querySelector('.reveal').hidden"), "the answer shows again after the retry")
        st=await pg.evaluate(f"(()=>{{const c=DB.sets[0].cards.find(x=>x.id==='{cid}');return{{lastG:c.lastG,miss:!!c.miss}}}})()")
        check(st["lastG"]==1 and not st["miss"], f"retry is practice only (still saved as Again) and clears the mistake note: {st}")
        await pg.screenshot(path="/tmp/ai2_retry.png",full_page=True)
        # ---- 2. Explain more
        n0=await pg.evaluate("__calls.length")
        await pg.click(".xpl"); await pg.wait_for_selector(".aix")
        x=await pg.inner_text(".aix")
        check(all(k in x for k in ["In simple words","Think of it like","Example","Why it matters","Remember it"]), "Explain more shows simple words, analogy, example, why, memory hook (and the mix-up)")
        check(await pg.evaluate(f"!!DB.sets[0].cards.find(x=>x.id==='{cid}').ax"), "explanation is saved on the card")
        await pg.screenshot(path="/tmp/ai2_explain.png",full_page=True)
        await pg.keyboard.press("Enter"); await pg.wait_for_timeout(300)
        # ---- 3. mistake memory: answer wrong once, then come back to the same card
        t2=await open_card(); await submit("first wrong try")
        cid2=await pg.evaluate(f"DB.sets[0].cards.find(x=>x.term.trim()==={t2!r}).id")
        check(await pg.evaluate(f"DB.sets[0].cards.find(x=>x.id==='{cid2}').miss?.g")=="first wrong try", "wrong answer is remembered on the card")
        await open_card(t2); await submit("second wrong try")
        txt=await pg.inner_text(".fb")
        check("Last time you said" in txt and "first wrong try" in txt, "next time: 'Last time you said: …'")
        await open_card(t2); await submit("good answer now")
        txt=await pg.inner_text(".fb")
        check("You fixed last time" in txt and not await pg.evaluate(f"!!DB.sets[0].cards.find(x=>x.id==='{cid2}').miss"), "a correct answer says 'You fixed last time’s mistake' and clears it")
        # ---- 4. mix-up
        t3=await open_card(); await submit("mix it up")
        txt=await pg.inner_text(".fb")
        other=await pg.evaluate("__calls[__calls.length-1].others[0][0]")
        cid3=await pg.evaluate(f"DB.sets[0].cards.find(x=>x.term.trim()==={t3!r}).id")
        check("Mix-up:" in txt and other in txt, f"mix-up banner names the other card: {other}")
        await pg.click(".xpl"); await pg.wait_for_selector(".aix")
        mx=await pg.evaluate("__calls[__calls.length-1].mix")
        check(mx and mx[0]==other, f"Explain more is told which card you mixed up: {mx}")
        check(await pg.evaluate(f"Object.values(DB.sets[0].cards.find(x=>x.id==='{cid3}').mix||{{}})[0]")==1, "mix-up is counted on the card")
        await pg.screenshot(path="/tmp/ai2_mix.png",full_page=True)
        await pg.evaluate("location.hash='#/detective'"); await pg.wait_for_timeout(600)
        rep=await pg.inner_text("#app") if await pg.locator("#app").count() else await pg.inner_text("body")
        check("Mixed-up terms" in rep and other in rep and t3 in rep, "Weak spots shows the mixed-up pair")
        await pg.screenshot(path="/tmp/ai2_detective.png",full_page=True)
        # ---- 5. strictness setting in Profile
        await pg.evaluate("location.hash='#/profile'"); await pg.wait_for_timeout(800)
        check(await pg.input_value("#sAiS")=="strict", "Profile shows the strictness setting")
        await pg.select_option("#sAiS","lenient")
        check(await pg.evaluate("DB.settings.aiStrict")=="lenient", "changing it saves")
        # ---- Explain more on a normal (non-AI) wrong answer: Don't know
        await pg.evaluate("DB.sets[0].opts.answer='term'")
        await open_card(); await pg.click(".dk"); await pg.wait_for_selector(".fb .xpl")
        await pg.click(".fb .xpl"); await pg.wait_for_selector(".aix")
        check(True, "Explain more also works after 'Don’t know' on any card")
        # explanation cached: no new call second time without an answer
        n0=await pg.evaluate("__calls.length")
        tt=(await pg.inner_text(".qtxt")).strip()
        await open_card(tt)
        await pg.click(".dk"); await pg.click(".fb .xpl"); await pg.wait_for_selector(".aix")
        check(await pg.evaluate("__calls.length")==n0, "a saved explanation is reused for free")
        check(not errs, f"no JS errors {errs[:2]}")
        await b.close()
    print("\nALL AI TUTOR CHECKS PASSED" if not FAILS else f"\n{len(FAILS)} FAILED")
asyncio.run(main())
