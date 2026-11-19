"""Learning Insight: AI insights grounded in cards, cache, save, next, fallback (stand-in AI)."""
import asyncio
from playwright.async_api import async_playwright
FAILS=[]
def check(c,m): print(("ok   " if c else "FAIL ")+m); (None if c else FAILS.append(m))
STUB = """(mode)=>{window.__calls=[];user={id:'u1',email:'me@x.com'};let k=0;
  sb={functions:{invoke:async(name,{body})=>{window.__calls.push(body);await new Promise(r=>setTimeout(r,250));
    if(mode==='down'){const e=new Error('x');e.name='FunctionsHttpError';e.context=new Response('{"error":"upstream"}',{status:502});return{data:null,error:e}}
    if(body.mode!=='insight')return{data:{ok:true,configured:true},error:null};
    const t=body.cards&&body.cards[0]?body.cards[0][0]:null;
    return{data:{items:[
      {category:t?'cards':'science',title:'Insight '+(++k),text:'Linking ideas helps memory.',terms:t?[t]:[]},
      {category:'science',title:'Insight '+(++k),text:'Sleep helps.',terms:[]},
      {category:'general',title:'Insight '+(++k),text:'Octopuses have three hearts.',terms:[]}]},error:null};}}};}"""
async def page(b,mode,clear=False):
    ctx=await b.new_context(viewport={"width":1440,"height":900});pg=await ctx.new_page();errs=[];pg.on("pageerror",lambda e:errs.append(str(e)))
    await pg.goto("file://" + __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.dirname(__import__("os").path.abspath(__file__))), "index.html") + "");await pg.wait_for_timeout(1500);await pg.evaluate("endTour()")
    if clear: await pg.evaluate("DB.sets=[];save()")
    if mode: await pg.evaluate(STUB,mode)
    await pg.evaluate("location.hash='#/library'");await pg.wait_for_timeout(150);await pg.evaluate("location.hash='#/'")
    return ctx,pg,errs
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--no-sandbox"])
        # signed out: built-in study tip, no AI badge
        ctx,pg,errs=await page(b,None)
        await pg.wait_for_selector(".ins-t")
        t=await pg.inner_text("#insight")
        check("Study tip" in t and "Learning science" in t, "signed out: shows a built-in study tip")
        check(await pg.locator("#insight .ins-ai .lu").count()==0, "built-in tips don't show the AI sparkle")
        await ctx.close()
        # signed in with AI
        ctx,pg,errs=await page(b,"ok")
        await pg.wait_for_selector(".ins-t")
        t=await pg.inner_text("#insight"); call=await pg.evaluate("__calls[0]")
        check(call["mode"]=="insight" and len(call["cards"])>=2 and call["want"][0]=="cards", f"asks for card-based insights first, sending {len(call['cards'])} of your cards")
        check("Learning Insight" in t and "From your cards" in t and "Insight 1" in t, "shows an AI insight labelled 'From your cards'")
        rel=await pg.evaluate("document.querySelector('.ins-r a')?.getAttribute('href')||''")
        check(rel.startswith("#/set/"), f"names the card it's about, linked to its set: {rel}")
        await pg.screenshot(path="/tmp/ins_ai.png")
        # next uses the queue without calling again
        await pg.click("#insNext");await pg.wait_for_timeout(200)
        check("Insight 2" in await pg.inner_text("#insight") and await pg.evaluate("__calls.length")==1, "Next shows the next insight from the batch (no new AI call)")
        # save
        await pg.click("#insSave");await pg.wait_for_timeout(200)
        check(await pg.evaluate("DB.settings.insSaved.length")==1 and await pg.get_attribute("#insSave","aria-pressed")=="true", "Save stores it and shows it as saved")
        check("Saved (1)" in await pg.inner_text("#insight"), "a 'Saved (1)' link appears")
        await pg.click("#insAll");await pg.wait_for_selector(".ins-item")
        check("Insight 2" in await pg.inner_text(".ins-list"), "Saved list shows it")
        await pg.click("[data-rm='0']");await pg.wait_for_timeout(200)
        check(await pg.evaluate("DB.settings.insSaved.length")==0, "remove from the saved list")
        await pg.click("#mC");await pg.wait_for_timeout(300)
        # third then a fresh batch
        await pg.click("#insNext");await pg.wait_for_timeout(200)
        await pg.click("#insNext");await pg.wait_for_selector(".ins-t");await pg.wait_for_timeout(600)
        c2=await pg.evaluate("__calls.length"); av=await pg.evaluate("__calls[__calls.length-1].avoid")
        check(c2==2 and "Insight 1" in av, f"after 3 insights it asks for a new batch, telling the AI which titles to avoid ({len(av)} sent)")
        # cached across visits
        n=await pg.evaluate("__calls.length"); cur=await pg.inner_text(".ins-t")
        await pg.reload();await pg.wait_for_timeout(1500);await pg.evaluate(STUB,"ok");await pg.evaluate("location.hash='#/library'");await pg.wait_for_timeout(150);await pg.evaluate("location.hash='#/'");await pg.wait_for_selector(".ins-t")
        check(await pg.inner_text(".ins-t")==cur and await pg.evaluate("__calls.length")==0, "reopening the dashboard reuses the cached insight (no AI call)")
        check(not errs, f"no JS errors {errs[:2]}"); await ctx.close()
        # AI failure -> study tip
        ctx,pg,errs=await page(b,"down")
        await pg.wait_for_selector(".ins-t")
        check("Study tip" in await pg.inner_text("#insight"), "if the AI fails, a study tip shows instead")
        await ctx.close()
        # empty library
        ctx,pg,errs=await page(b,"ok",clear=True)
        await pg.wait_for_selector(".ins-t")
        call=await pg.evaluate("__calls[0]")
        check(call["want"][0]=="science" and not call["cards"], f"empty library: asks for learning science and general facts only: {call['want']}")
        t=await pg.inner_text("#app")
        check("Create your first set" in t and "Daily goal" not in t, "empty library: Start says 'Create your first set' and no goal card")
        await pg.screenshot(path="/tmp/ins_empty.png")
        check(not errs, f"no JS errors {errs[:2]}"); await ctx.close()
        await b.close()
    print("\nALL INSIGHT CHECKS PASSED" if not FAILS else f"\n{len(FAILS)} FAILED")
asyncio.run(main())
