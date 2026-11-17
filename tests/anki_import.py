"""Import real Anki .apkg files (modern zstd format and legacy) through the UI and check the result."""
import asyncio
from playwright.async_api import async_playwright
URL = "file://" + __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.dirname(__import__("os").path.abspath(__file__))), "index.html")
LIB = {
    "fflate@0.8.3/umd/index.js": "/home/claude/libs/fflate-0.8.3/package/umd/index.js",
    "fzstd@0.1.1/umd/index.js": "/home/claude/libs/fzstd-0.1.1/package/umd/index.js",
    "sql.js@1.16.0/dist/sql-wasm.js": "/home/claude/libs/sql.js-1.16.0/package/dist/sql-wasm.js",
    "sql.js@1.16.0/dist/sql-wasm.wasm": "/home/claude/libs/sql.js-1.16.0/package/dist/sql-wasm.wasm",
}
FAILS = []
def check(c, m): print(("ok   " if c else "FAIL ") + m); (None if c else FAILS.append(m))

async def serve(route):
    u = route.request.url
    for k, path in LIB.items():
        if u.endswith(k):
            ct = "application/wasm" if k.endswith(".wasm") else "text/javascript"
            return await route.fulfill(status=200, body=open(path, "rb").read(), headers={"content-type": ct, "access-control-allow-origin": "*"})
    await route.abort()

async def run(b, fname, mobile):
    ctx = await b.new_context(**({"viewport": {"width": 390, "height": 844}, "is_mobile": True, "has_touch": True, "device_scale_factor": 2} if mobile else {"viewport": {"width": 1280, "height": 900}}))
    await ctx.route("https://cdn.jsdelivr.net/**", serve)
    pg = await ctx.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
    tag = f"[{fname} {'phone' if mobile else 'desktop'}]"
    await pg.goto(URL); await pg.wait_for_timeout(2300); await pg.evaluate("endTour()"); await pg.wait_for_timeout(300)
    await pg.evaluate("location.hash='#/import'"); await pg.wait_for_selector("#iApkg", state="attached")
    await pg.set_input_files("#iApkg", __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "fixtures", fname))
    await pg.wait_for_selector("#aiGo", timeout=20000)
    decks = await pg.evaluate("[...document.querySelectorAll('[data-did]')].map(x=>x.closest('.opt').innerText.replace(/\\s+/g,' '))")
    check(len(decks) == 3, f"{tag} deck picker lists 3 decks: {decks}")
    await pg.screenshot(path=f"/tmp/anki_picker_{fname}_{'m' if mobile else 'd'}.png")
    await (pg.locator("#aiGo").tap() if mobile else pg.locator("#aiGo").click())
    for _ in range(60):
        if await pg.evaluate("$('#modal').hidden"): break
        await pg.wait_for_timeout(250)
    sets = await pg.evaluate("""DB.sets.filter(s=>s.desc==='Imported from Anki').map(s=>({t:s.title,cards:s.cards.map(c=>({k:c.kind||'basic',term:c.term,def:c.def,mid:!!c.mid,reps:c.reps||0,s:c.s,due:c.due,masks:(c.masks||[]).length,mk:c.masks?c.masks.find(m=>m.id===c.mk):null}))}))""")
    titles = sorted(s["t"] for s in sets)
    check(set(titles) == {"Anatomy › Heart", fname.replace(".apkg", ""), "Networking"}, f"{tag} sets created: {titles}")
    H = next((s for s in sets if s["t"] == "Anatomy › Heart"), {"cards": []})["cards"]
    kinds = [c["k"] for c in H]
    check(kinds.count("basic") == 3 and kinds.count("cloze") == 3, f"{tag} heart deck: 3 basic (reversed note counted once) + 3 cloze: {kinds}")
    hr = next((c for c in H if c["term"] == "Normal resting heart rate"), None)
    check(hr and hr["def"] == "60–100 beats per minute\nin adults", f"{tag} HTML cleaned: entities decoded, <b> removed, <br> kept as a line break: {hr and hr['def']!r}")
    pic = next((c for c in H if c["term"] == "Which chamber is shown?"), None)
    check(pic and pic["mid"] and pic["def"] == "Left ventricle", f"{tag} picture card keeps its image (image store) and text: {pic and (pic['def'], pic['mid'])}")
    cz = [c for c in H if c["k"] == "cloze"]
    check(any(c["term"] == "The [...] pumps blood to the lungs." and c["def"] == "right ventricle" for c in cz) and any(c["term"] == "The right ventricle pumps blood to the [organ]." and c["def"] == "lungs" for c in cz), f"{tag} cloze with hint becomes '[organ]': {[c['term'] for c in cz]}")
    IO = next((s for s in sets if s["t"] == fname.replace(".apkg", "")), {"cards": []})["cards"]
    check(len(IO) == 3 and all(c["k"] == "occ" and c["mid"] and c["masks"] == 3 for c in IO), f"{tag} image occlusion note → 3 tape cards on the picture: {[(c['k'], c['masks']) for c in IO]}")
    m0 = IO[0]["mk"] if IO else None
    check(m0 and abs(m0["x"] - .0444) < 1e-3 and abs(m0["y"] - .2333) < 1e-3, f"{tag} tape positions match Anki's shapes: {m0}")
    N = next((s for s in sets if s["t"] == "Networking"), {"cards": []})["cards"]
    studied = [c for c in N if c["reps"]]
    check(len(N) == 3 and len(studied) == 3 and all(c["s"] and c["due"] for c in studied), f"{tag} Anki review progress kept (3 studied cards with stability + due): {[(c['reps'], round(c['s'] or 0, 2)) for c in N]}")
    # images render from the image store
    sid = await pg.evaluate("DB.sets.find(s=>s.title==='Anatomy › Heart').id")
    await pg.evaluate(f"location.hash='#/set/{sid}'"); await pg.wait_for_timeout(800)
    ok_img = await pg.evaluate("[...document.querySelectorAll('#terms img')].filter(i=>i.complete&&i.naturalWidth>0).length")
    check(ok_img >= 1, f"{tag} imported picture displays on the set page ({ok_img})")
    await pg.screenshot(path=f"/tmp/anki_set_{fname}_{'m' if mobile else 'd'}.png", full_page=True)
    ioid = await pg.evaluate(f"DB.sets.find(s=>s.title==='{fname.replace('.apkg','')}').id")
    await pg.evaluate(f"location.hash='#/flash/{ioid}'"); await pg.wait_for_selector("#fc"); await pg.wait_for_timeout(600)
    shown = await pg.evaluate("document.querySelector('#fc .occimg')?.naturalWidth||0")
    check(shown > 0, f"{tag} image-occlusion flashcard shows the picture with tapes ({shown}px wide)")
    await pg.screenshot(path=f"/tmp/anki_io_{fname}_{'m' if mobile else 'd'}.png")
    # study an imported cloze card in Learn end-to-end
    await pg.evaluate(f"location.hash='#/learn/{sid}'"); await pg.wait_for_timeout(500)
    check(await pg.locator(".qcard").count() == 1, f"{tag} imported deck opens in Learn")
    check(not errs, f"{tag} no JavaScript errors {errs[:2]}")
    await ctx.close()

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
        for f in ["modern.apkg", "legacy.apkg"]:
            await run(b, f, mobile=(f == "modern.apkg"))
        await b.close()
    print("\nALL ANKI IMPORT CHECKS PASSED" if not FAILS else f"\n{len(FAILS)} FAILED")
asyncio.run(main())
