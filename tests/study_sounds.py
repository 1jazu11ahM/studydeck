"""Study sounds: real recordings load, loop, mix, presets apply, mixes save/delete, fades, offline fallback."""
import asyncio, subprocess, time
from playwright.async_api import async_playwright
FAILS = []
def check(c, m): print(("ok   " if c else "FAIL ") + m); (None if c else FAILS.append(m))

LEVEL = """async()=>{const G=AMB.G;if(!G.an){G.an=AMB.ctx.createAnalyser();G.an.fftSize=4096;G.master.connect(G.an);await new Promise(r=>setTimeout(r,400))}
  const d=new Float32Array(G.an.fftSize);G.an.getFloatTimeDomainData(d);let s=0;for(const v of d)s+=v*v;return 20*Math.log10(Math.sqrt(s/d.length)+1e-9)}"""

async def run(b, mobile, offline_rain=False):
    ctx = await b.new_context(**({"viewport": {"width": 390, "height": 844}, "is_mobile": True, "has_touch": True} if mobile else {"viewport": {"width": 1280, "height": 900}}))
    if offline_rain:
        await ctx.route("**/sounds/rain.mp3", lambda r: r.abort())
    pg = await ctx.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
    tag = "[phone]" if mobile else "[desktop]"
    if offline_rain: tag = "[offline rain]"
    tap = (lambda sel: pg.locator(sel).first.tap()) if mobile else (lambda sel: pg.locator(sel).first.click())
    await pg.goto("http://localhost:8765/index.html"); await pg.wait_for_timeout(2000); await pg.evaluate("endTour()")
    d = await pg.evaluate("({...DB.settings.amb})")
    check(d["rain"] == .6 and d["fire"] == 0 and d["cafe"] == 0 and d["thunder"] == .3 and d["hum"] == 0 and d["on"] is False, f"{tag} new users: sound off, gentle rain-only mix saved: {d}")
    await tap("#ambBtn"); await pg.wait_for_selector("#ambPanel:not([hidden])")
    names = await pg.evaluate("[...document.querySelectorAll('#ambPanel [data-pre]')].map(b=>b.textContent)")
    check(names == ["Rainy night", "Fireside", "Coffee shop", "Cozy café", "Deep focus"], f"{tag} five presets shown: {names}")
    await tap("#ambPanel [data-pre='3']")  # Cozy café
    for _ in range(40):
        st = await pg.evaluate("Object.fromEntries(Object.entries(SOUNDS).map(([k,S])=>[k,S.state]))")
        if all(v in ("ready", "error") for v in st.values()): break
        await pg.wait_for_timeout(250)
    if offline_rain:
        check(st["rain"] == "error" and st["fire"] == "ready" and st["cafe"] == "ready", f"{tag} rain fails, others load: {st}")
        msg = await pg.evaluate("document.querySelector('[data-st=rain]').textContent")
        check("generated rain" in msg, f"{tag} panel explains the fallback: {msg!r}")
        await pg.wait_for_timeout(1500)
        hits = await pg.evaluate("performance.getEntriesByName(location.origin+'/sounds/rain.mp3').length")
        check(hits <= 2, f"{tag} no endless retries ({hits} attempts)")
        g = await pg.evaluate("AMB.G.rain.gain.value")
        check(g > .1, f"{tag} generated rain takes over ({g:.2f})")
        lv = await pg.evaluate(LEVEL)
        check(lv > -45, f"{tag} still audible: {lv:.1f} dBFS")
        check(not errs, f"{tag} no JS errors {errs[:2]}"); await ctx.close(); return
    check(st == {"rain": "ready", "fire": "ready", "cafe": "ready"}, f"{tag} three recordings loaded: {st}")
    info = await pg.evaluate("Object.fromEntries(Object.entries(SOUNDS).map(([k,S])=>[k,[+S.src.buffer.duration.toFixed(2),S.src.loop,+S.src.loopStart.toFixed(2),+S.src.loopEnd.toFixed(2)]]))")
    check(all(v[1] and abs(v[3] - v[2] - SOUNDS_LEN[k]) < .01 and v[0] >= v[3] for k, v in info.items()), f"{tag} each recording loops over its seamless section: {info}")
    check(await pg.evaluate("DB.settings.amb.on===true&&AMB.on"), f"{tag} tapping a preset starts the sound")
    await pg.wait_for_timeout(2500)
    lv = await pg.evaluate(LEVEL)
    check(-40 < lv < -6, f"{tag} audible, not clipping: {lv:.1f} dBFS")
    gains = await pg.evaluate("Object.fromEntries(Object.entries(SOUNDS).map(([k,S])=>[k,+S.g.gain.value.toFixed(3)]))")
    exp = {"rain": 3 * .4 * .4, "fire": 1.4 * .35 * .35, "cafe": 2 * .55 * .55}
    check(all(abs(gains[k] - exp[k]) < .03 for k in exp), f"{tag} mix levels match the preset: {gains} vs {exp}")
    check(await pg.evaluate("AMB.G.rain.gain.value") < .01, f"{tag} generated rain stays silent when the recording plays")
    on = await pg.evaluate("[...document.querySelectorAll('#ambPanel [data-pre].on')].map(b=>b.textContent)")
    check(on == ["Cozy café"], f"{tag} active preset highlighted: {on}")
    # move a slider: preset no longer matches
    await pg.evaluate("const r=document.querySelector('[data-amb=fire]');r.value=.9;r.dispatchEvent(new Event('input'))")
    on = await pg.evaluate("[...document.querySelectorAll('#ambPanel [data-pre].on')].length")
    check(on == 0, f"{tag} changing a slider clears the highlight")
    # save a mix
    await tap("#ambSave"); await pg.fill("#ambName", "Library night"); await tap("#ambNameOk")
    mine = await pg.evaluate("DB.settings.amb.mine")
    check(len(mine) == 1 and mine[0]["name"] == "Library night" and mine[0]["mix"]["fire"] == .9, f"{tag} mix saved: {mine}")
    on = await pg.evaluate("[...document.querySelectorAll('#ambPanel [data-pre].on')].map(b=>b.textContent.replace('×',''))")
    check(on == ["Library night"], f"{tag} saved mix shows as a chip and is active: {on}")
    await pg.screenshot(path=f"/tmp/sound_{'m' if mobile else 'd'}.png")
    # switch to Coffee shop, then back to my mix
    await tap("#ambPanel [data-pre='2']"); await pg.wait_for_timeout(4000)
    g = await pg.evaluate("[SOUNDS.rain.g.gain.value,SOUNDS.fire.g.gain.value,SOUNDS.cafe.g.gain.value]")
    check(g[0] < .02 and g[1] < .02 and g[2] > 1, f"{tag} Coffee shop fades the others out: {[round(x,3) for x in g]}")
    await tap("#ambPanel [data-pre='mine']"); await pg.wait_for_timeout(300)
    check(await pg.evaluate("DB.settings.amb.fire") == .9, f"{tag} tapping a saved mix restores it")
    # pause: fade, then suspend
    await tap("#ambToggle"); await pg.wait_for_timeout(250)
    mid = await pg.evaluate("AMB.G.master.gain.value")
    await pg.wait_for_timeout(900)
    state = await pg.evaluate("[AMB.ctx.state,AMB.G.master.gain.value,DB.settings.amb.on]")
    check(0 <= mid < 1 and state[0] == "suspended" and state[1] < .01 and state[2] is False, f"{tag} pause fades out then stops: mid {mid:.2f}, after {state}")
    await tap("#ambToggle"); await pg.wait_for_timeout(1500)
    lv = await pg.evaluate(LEVEL)
    check(await pg.evaluate("AMB.ctx.state") == "running" and lv > -40, f"{tag} play fades back in: {lv:.1f} dBFS")
    # delete saved mix
    await tap("#ambPanel [data-del='0']")
    check(await pg.evaluate("DB.settings.amb.mine.length") == 0, f"{tag} saved mix deleted")
    # settings persist across reload
    await pg.evaluate("saveNow()"); await pg.reload(); await pg.wait_for_timeout(1500)
    a = await pg.evaluate("[DB.settings.amb.fire,DB.settings.amb.on]")
    check(a[0] == .9 and a[1] is True, f"{tag} mix and on/off survive a reload: {a}")
    check(not errs, f"{tag} no JS errors {errs[:2]}")
    await ctx.close()

SOUNDS_LEN = {"rain": 46, "fire": 70, "cafe": 55.5}
async def main():
    srv = subprocess.Popen(["python3", "-m", "http.server", "8765", "-d", __import__("os").path.dirname(__import__("os").path.dirname(__import__("os").path.abspath(__file__)))], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
    try:
        async with async_playwright() as p:
            b = await p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox", "--autoplay-policy=no-user-gesture-required"])
            await run(b, True); await run(b, False); await run(b, False, offline_rain=True)
            await b.close()
    finally: srv.terminate()
    print("\nALL SOUND CHECKS PASSED" if not FAILS else f"\n{len(FAILS)} FAILED")
asyncio.run(main())
