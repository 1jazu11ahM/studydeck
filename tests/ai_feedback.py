"""AI feedback on typed answers, with a stand-in for the Supabase function (no real AI calls)."""
import asyncio
from playwright.async_api import async_playwright
FAILS=[]
def check(c,m): print(("ok   " if c else "FAIL ")+m); (None if c else FAILS.append(m))
STUB = """(mode)=>{window.__calls=[];user={id:'u1',email:'me@x.com'};
  const resp=(status,obj)=>{const e=new Error('Edge Function returned a non-2xx status code');e.name='FunctionsHttpError';e.context=new Response(JSON.stringify(obj),{status});return{data:null,error:e}};
  sb={functions:{invoke:async(name,{body})=>{window.__calls.push({name,body});await new Promise(r=>setTimeout(r,300));
    if(mode==='missing')return resp(404,{error:'not found'});
    if(mode==='unconfigured')return body.ping?{data:{ok:true,configured:false},error:null}:resp(503,{error:'not_configured'});
    if(mode==='down')return resp(502,{error:'upstream'});
    if(body.ping)return{data:{ok:true,configured:true},error:null};
    const g=body.given.toLowerCase();
    if(g.includes('right'))return{data:{verdict:'correct',score:9,right:'You explained the core idea.',missing:'',better:'Reviewing at longer and longer gaps, each just before you would forget.'},error:null};
    if(g.includes('half'))return{data:{verdict:'partial',score:6,right:'You mentioned reviewing again.',missing:'You left out that the gaps grow longer.',better:'Reviewing at longer and longer gaps.'},error:null};
    return{data:{verdict:'wrong',score:1,right:'',missing:'<b>That</b> describes cramming, not spacing.',better:'Reviewing at longer and longer gaps.'},error:null};}}};}"""
async def fresh(b, mode, mobile=False):
    ctx=await b.new_context(**({"viewport":{"width":390,"height":844},"is_mobile":True,"has_touch":True} if mobile else {"viewport":{"width":1280,"height":900}}))
    pg=await ctx.new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)))
    await pg.goto("file://" + __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.dirname(__import__("os").path.abspath(__file__))), "index.html") + ""); await pg.wait_for_timeout(1800); await pg.evaluate("endTour()")
    if mode: await pg.evaluate(STUB, mode)
    sid=await pg.evaluate("DB.sets[0].id")
    await pg.evaluate(f"DB.sets[0].opts.answer='def'")
    return ctx,pg,errs,sid
async def write_one(pg,sid,given):
    await pg.evaluate("location.hash='#/home'"); await pg.wait_for_timeout(200)
    await pg.evaluate(f"location.hash='#/write/{sid}'"); await pg.wait_for_selector(".wa")
    card=await pg.evaluate("(()=>{const q=document.querySelector('.qtxt').innerText.trim();const c=DB.sets[0].cards.find(x=>x.term.trim()===q);return c&&{id:c.id,reps:c.reps||0,lastG:c.lastG??null}})()")
    await pg.fill(".wa", given); await pg.click(".wform button")
    return card
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--no-sandbox"])
        ctx,pg,errs,sid=await fresh(b,"ok")
        check(await pg.evaluate("aiOn()"), "AI is on when signed in and switched on")
        # 1. correct in own words
        card=await write_one(pg,sid,"you review it right before forgetting, with gaps that get longer")
        check(card is not None, f"Write asks with the term and wants the definition: {card}")
        wait=await pg.evaluate("document.querySelector('.fbx.aiwait')?.innerText||''")
        check("Checking your answer" in wait, f"shows a checking message while the AI thinks: {wait!r}")
        await pg.wait_for_selector(".aifb")
        txt=await pg.inner_text(".fb")
        check("✓ Correct" in txt and "9/10" in txt and "What you got right" in txt and "A full answer" in txt and "The card says" in txt, "correct: verdict, score, what was right, full answer and card answer shown")
        check(await pg.locator(".ovr").count()==0, "correct: no override button")
        c=await pg.evaluate(f"(()=>{{const c=DB.sets[0].cards.find(x=>x.id==='{card['id']}');return{{reps:c.reps,lastG:c.lastG}}}})()")
        check(c["reps"]==card["reps"]+1 and c["lastG"]==3, f"correct counts as Good for the schedule: {c}")
        sv=await pg.inner_text(".saved"); print("   shown:",sv)
        check(sv.startswith("Saved as Good"), f"correct shows 'Saved as Good': {sv!r}")
        call=await pg.evaluate("__calls[__calls.length-1].body")
        check(call["shownSide"]=="term" and call["reference"] and call["prompt"] and call["given"].startswith("you review"), f"sends the prompt, the card answer and your answer: {list(call)}")
        await pg.screenshot(path="/tmp/ai_correct.png",full_page=True)
        # 2. partial
        card=await write_one(pg,sid,"you review it again later, half remembered"); await pg.wait_for_selector(".aifb")
        txt=await pg.inner_text(".fb")
        check("Partly right" in txt and "What’s missing" in txt and "Count it as fully right" in txt, "partial: shows what is missing and an override")
        c=await pg.evaluate(f"DB.sets[0].cards.find(x=>x.id==='{card['id']}').lastG")
        check(c==2, f"partial counts as Hard: lastG {c}")
        sv=await pg.inner_text(".saved"); print("   shown:",sv)
        check(sv.startswith("Saved as Hard"), f"partial shows 'Saved as Hard': {sv!r}")
        await pg.screenshot(path="/tmp/ai_partial.png")
        await pg.click(".ovr"); await pg.wait_for_timeout(300)
        c=await pg.evaluate(f"DB.sets[0].cards.find(x=>x.id==='{card['id']}').lastG")
        check(c==3, f"override turns it into Good: lastG {c}")
        # 3. wrong, with HTML in the AI text (must be escaped)
        card=await write_one(pg,sid,"cram everything the night before"); await pg.wait_for_selector(".aifb")
        txt=await pg.inner_text(".fb"); html=await pg.inner_html(".aifb")
        check("Not quite" in txt and "What went wrong" in txt and "I disagree: I was right" in txt, "wrong: shows what went wrong and an 'I disagree' button")
        check("&lt;b&gt;That&lt;/b&gt;" in html, "AI text is shown as plain text, never as HTML")
        c=await pg.evaluate(f"DB.sets[0].cards.find(x=>x.id==='{card['id']}').lastG")
        check(c==1, f"wrong counts as Again: lastG {c}")
        sv=await pg.inner_text(".saved"); print("   shown:",sv)
        check(sv.startswith("Saved as Again") and "due again now" in sv, f"wrong shows 'Saved as Again': {sv!r}")
        await pg.screenshot(path="/tmp/ai_wrong.png",full_page=True)
        await pg.keyboard.press("Enter"); await pg.wait_for_timeout(400)
        check(await pg.locator(".aifb").count()==0, "Enter continues to the next card")
        # 4. exact answer: no AI call
        n0=await pg.evaluate("__calls.length")
        await pg.evaluate("location.hash='#/home'"); await pg.wait_for_timeout(200)
        await pg.evaluate(f"location.hash='#/write/{sid}'"); await pg.wait_for_selector(".wa")
        exact=await pg.evaluate("(()=>{const q=document.querySelector('.qtxt').innerText.trim();return DB.sets[0].cards.find(x=>x.term.trim()===q).def})()")
        await pg.fill(".wa",exact); await pg.click(".wform button"); await pg.wait_for_timeout(700)
        check(await pg.evaluate("__calls.length")==n0, "exact answers are graded instantly without the AI")
        # 5. answering with the term (single word): no AI
        await pg.evaluate("DB.sets[0].opts.answer='term'")
        n0=await pg.evaluate("__calls.length")
        await write_one(pg,sid,"totally wrong word"); await pg.wait_for_timeout(700)
        check(await pg.evaluate("__calls.length")==n0 and await pg.locator(".aifb").count()==0, "short term answers keep the normal check (no AI)")
        # 6. setting off
        await pg.evaluate("DB.settings.ai=false;DB.sets[0].opts.answer='def'")
        n0=await pg.evaluate("__calls.length")
        await write_one(pg,sid,"cram everything"); await pg.wait_for_timeout(700)
        check(await pg.evaluate("__calls.length")==n0, "switching AI feedback off in Profile stops the calls")
        await pg.evaluate("DB.settings.ai=true")
        # 7. profile status
        await pg.evaluate("location.hash='#/profile'"); await pg.wait_for_timeout(1200)
        check(await pg.inner_text("#sAiV")=="Ready", f"Profile shows Ready: {await pg.inner_text('#sAiV')!r}")
        await pg.screenshot(path="/tmp/ai_profile.png",full_page=True)
        check(not errs, f"no JS errors {errs[:2]}"); await ctx.close()
        for mode,label in [("unconfigured","Not set up yet"),("missing","Not set up yet")]:
            ctx,pg,errs,sid=await fresh(b,mode)
            await write_one(pg,sid,"cram everything the night before"); await pg.wait_for_selector(".fbx.bad",timeout=5000)
            txt=await pg.inner_text(".fb")
            check(await pg.locator(".aifb").count()==0 and "Correct answer" in txt, f"[{mode}] falls back to the normal check: {txt[:60]!r}")
            check(await pg.evaluate("AI.state")=="missing" and not await pg.evaluate("aiOn()"), f"[{mode}] stops asking for the rest of the session")
            await pg.evaluate("location.hash='#/profile'"); await pg.wait_for_timeout(1200)
            check(await pg.inner_text("#sAiV")==label, f"[{mode}] Profile says: {await pg.inner_text('#sAiV')!r}")
            check(not errs, f"[{mode}] no JS errors {errs[:2]}"); await ctx.close()
        ctx,pg,errs,sid=await fresh(b,"down")
        await write_one(pg,sid,"cram everything"); await pg.wait_for_selector(".fbx.bad",timeout=5000)
        check(await pg.evaluate("AI.state")!="missing" and await pg.evaluate("aiOn()"), "[AI down] normal check used, will try again next time")
        await ctx.close()
        ctx,pg,errs,sid=await fresh(b,None)
        check(not await pg.evaluate("aiOn()"), "[signed out] AI is not used")
        await pg.evaluate("location.hash='#/profile'"); await pg.wait_for_timeout(800)
        check(await pg.inner_text("#sAiV")=="Sign in to use it", f"[signed out] Profile says: {await pg.inner_text('#sAiV')!r}")
        await ctx.close()
        ctx,pg,errs,sid=await fresh(b,"ok",mobile=True)
        await write_one(pg,sid,"cram everything the night before"); await pg.wait_for_selector(".aifb")
        await pg.screenshot(path="/tmp/ai_wrong_m.png",full_page=True); await ctx.close()
        await b.close()
    print("\nALL AI CHECKS PASSED" if not FAILS else f"\n{len(FAILS)} FAILED")
asyncio.run(main())
