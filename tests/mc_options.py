"""Harder multiple choice: smart wrong options, AI-made wrong options and the 'cards to review' list (AI stubbed)."""
import asyncio, os
from playwright.async_api import async_playwright
FAILS=[]
def check(c,m): print(("ok   " if c else "FAIL ")+m); (None if c else FAILS.append(m))
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LINES="""Bit | The smallest unit of data, a single 0 or 1.
Octet | A group of 8 bits that can hold decimal values 0 to 255.
Subnet mask | A 32-bit value that shows which part of an IP address is the network.
Broadcast address | The last address in a subnet, used to reach every host in it.
A /24 network has 254 usable hosts, and a /30 network has {{c1::2}}. |
The broadcast address of 172.16.0.0/12 is {{c1::172.31.255.255}}. |
A host with a 169.254.x.x address {{c1::could not reach a DHCP server}}. |
The binary octet 11000000 equals {{c1::192}} in decimal. |
An IPv4 address is {{c1::32}} bits long. |"""
STUB = """()=>{window.__calls=[];user={id:'u1',email:'me@x.com'};
  sb={functions:{invoke:async(name,{body})=>{window.__calls.push(body);await new Promise(r=>setTimeout(r,300));
    if(body.ping)return{data:{ok:true,configured:true},error:null};
    if(body.mode!=='distract')return{data:null,error:new Error('x')};
    return{data:{items:body.cards.map((c,i)=>c.kind==='cloze'
      ?{i,wrong:c.answer==='2'?['4','6','30']:['W1','W2','W3'],wrong_terms:[],issue:c.answer==='192'?'Check this: 11000000 is 192, fine, but the blank is unclear.':''}
      :{i,wrong:['Wrong def A','Wrong def B','Wrong def C'],wrong_terms:['Nibble','Byte','Word'],issue:''})},error:null}}}};}"""
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--no-sandbox"])
        ctx=await b.new_context(viewport={"width":1280,"height":900}); pg=await ctx.new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)))
        await pg.goto("file://"+os.path.join(ROOT,"index.html")); await pg.wait_for_timeout(1800); await pg.evaluate("endTour()")
        sid=await pg.evaluate("""(t)=>{const r=parseBulk(t,'|','\\n');const s=newSet({title:'Subnetting'});
          s.cards=r.flatMap(c=>isCloze(c.term)?buildCloze(c.term,c.def):[c]);DB.sets.push(s);save();return s.id}""", LINES)
        # 1. smart options, no AI
        opts=await pg.evaluate("""(sid)=>{const s=getSet(sid),c=s.cards.find(c=>c.def==='2'),q=qa(s,c);return mcOptions(s,c,q)}""", sid)
        check(len(opts)==4 and all(o.strip().lstrip('-').isdigit() for o in opts), f"/30 question gets only numbers: {opts}")
        opts=await pg.evaluate("""(sid)=>{const s=getSet(sid),c=s.cards.find(c=>c.def==='172.31.255.255'),q=qa(s,c);return mcOptions(s,c,q)}""", sid)
        check(len(opts)==4 and all(o.count('.')==3 for o in opts), f"IP question gets only IP addresses: {opts}")
        opts=await pg.evaluate("""(sid)=>{const s=getSet(sid),c=s.cards.find(c=>c.term==='Bit');s.opts.answer='def';const q=qa(s,c);return mcOptions(s,c,q)}""", sid)
        check(len(opts)==4 and len(set(opts))==4, f"definition question gets 4 different options: {[o[:30] for o in opts]}")
        tf=await pg.evaluate("""(sid)=>{const s=getSet(sid),c=s.cards.find(c=>c.def==='32'),q=qa(s,c);return wrongOptions(s,c,q)}""", sid)
        check(all(o.isdigit() for o in tf), f"true/false fakes are the same kind: {tf}")
        # 2. AI check on the set page
        await pg.evaluate(STUB)
        await pg.evaluate(f"location.hash='#/set/{sid}'")
        await pg.wait_for_timeout(150)
        busy=await pg.evaluate("document.querySelector('#aiChk').innerText")
        check("Checking cards" in busy, f"shows checking message: {busy!r}")
        await pg.wait_for_selector(".aichk .okchip", timeout=5000)
        n=await pg.evaluate("window.__calls.filter(c=>c.mode==='distract').length")
        check(n==1, f"one AI call for the whole set: {n}")
        opts=await pg.evaluate("""(sid)=>{const s=getSet(sid),c=s.cards.find(c=>c.def==='2'),q=qa(s,c);return mcOptions(s,c,q).sort()}""", sid)
        check(opts==['2','30','4','6'], f"/30 question now uses AI options: {opts}")
        opts=await pg.evaluate("""(sid)=>{const s=getSet(sid),c=s.cards.find(c=>c.term==='Bit');s.opts.answer='term';const q=qa(s,c);return mcOptions(s,c,q).sort()}""", sid)
        check(opts==['Bit','Byte','Nibble','Word'], f"term question uses AI terms: {opts}")
        iss=await pg.evaluate("document.querySelector('.aiiss')?.innerText||''")
        check("1 card to review" in iss and "unclear" in iss, f"cards to review list: {iss[:80]!r}")
        await pg.click(".aiiss [data-ign]"); await pg.wait_for_timeout(100)
        check(await pg.evaluate("!document.querySelector('.aiiss')"), "Ignore hides the card from the list")
        # 3. revisit: no new call; edit one card: only that card is re-checked
        await pg.evaluate("location.hash='#/library'"); await pg.wait_for_timeout(200)
        await pg.evaluate(f"location.hash='#/set/{sid}'"); await pg.wait_for_timeout(600)
        n=await pg.evaluate("window.__calls.filter(c=>c.mode==='distract').length")
        check(n==1, f"revisiting the set doesn't call the AI again: {n}")
        await pg.evaluate(f"(()=>{{const c=getSet('{sid}').cards.find(c=>c.term==='Bit');c.def='One binary digit, 0 or 1.';save()}})()")
        await pg.evaluate("location.hash='#/library'"); await pg.wait_for_timeout(200)
        await pg.evaluate(f"location.hash='#/set/{sid}'"); await pg.wait_for_selector(".aichk .okchip", timeout=5000)
        last=await pg.evaluate("window.__calls.filter(c=>c.mode==='distract').at(-1).cards.length")
        check(last==1, f"after an edit only the changed card is sent: {last}")
        # 4. Learn and Test still run with MC
        await pg.evaluate(f"location.hash='#/test/{sid}'"); await pg.wait_for_timeout(800)
        await pg.evaluate(f"location.hash='#/learn/{sid}'"); await pg.wait_for_timeout(800)
        check(await pg.evaluate("document.querySelectorAll('.choices button, .choice').length>=2 || !!document.querySelector('.wa')"), "Learn shows a question")
        await pg.screenshot(path="/tmp/learn.png")
        await pg.evaluate(f"location.hash='#/set/{sid}'"); await pg.wait_for_timeout(400); await pg.screenshot(path="/tmp/set.png")
        check(not errs, f"no page errors: {errs}")
        await b.close()
    print("\nALL PASSED" if not FAILS else f"\n{len(FAILS)} FAILED")
asyncio.run(main())
