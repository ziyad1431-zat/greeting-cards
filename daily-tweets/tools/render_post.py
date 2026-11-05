#!/usr/bin/env python3
"""قالب «البوست الاحترافي» للتغريدة: رسمة أعلى + نص + شريط تعريف (صورة، اسم، حساب، جوال).

python3 render_post.py post.json out.png
post.json:
{
  "theme": "family",                 # family | marketing | self (أو أي ثيم من render_card.THEMES)
  "label": "تنمية أسرية",             # اختياري
  "headline": "العنوان الكبير",
  "points": ["نقطة ١", "نقطة ٢"],      # اختياري
  "question": "سؤال الختام؟",         # اختياري
  "source": "المصدر: منظمة الصحة العالمية",  # اختياري (سطر صغير)
  "illustration": "path/or/url.png",  # اختياري: رسمة الذكاء الاصطناعي (بدون نص)
  "photo": "path/to/photo.jpg",       # اختياري: صورة صاحب الحساب (دائرة في الزاوية)
  "name": "زياد", "handle": "@...", "phone": "0560502200"
}
المقاس 1080×1350.
"""
import json, sys, html, os, base64, mimetypes, pathlib, subprocess, tempfile

HERE = pathlib.Path(__file__).resolve().parent

THEMES = {
    # bg, ink, accent, soft
    "family":    ("#F6EFE4", "#1F3B3A", "#C0662F", "#E9DCC8"),
    "marketing": ("#FBF4EC", "#2C1A12", "#E2552F", "#F1E1D2"),
    "self":      ("#F2EEE6", "#14213D", "#B5763A", "#E3DCCD"),
    "spiritual": ("#10302A", "#F1EAD8", "#CFAE63", "#1B4038"),
    "tech":      ("#0F1B2B", "#E9EEF4", "#5EC4C9", "#1A2A40"),
}
LABELS = {"family": "تنمية أسرية", "marketing": "تسويق", "self": "تطوير الذات",
          "spiritual": "جمعة مباركة", "tech": "تقنية"}


def data_uri(p):
    if not p:
        return ""
    if str(p).startswith(("http://", "https://", "data:")):
        return p
    mt = mimetypes.guess_type(p)[0] or "image/png"
    return f"data:{mt};base64," + base64.b64encode(open(p, "rb").read()).decode()


def build(c):
    bg, ink, acc, soft = THEMES.get(c.get("theme", "family"), THEMES["family"])
    label = c.get("label") or LABELS.get(c.get("theme"), "")
    e = html.escape
    pts = "".join(f'<li><span class="d"></span><span>{e(p)}</span></li>' for p in c.get("points", []))
    q = f'<p class="q">{e(c["question"])}</p>' if c.get("question") else ""
    src = f'<p class="src">{e(c["source"])}</p>' if c.get("source") else ""
    ill = data_uri(c.get("illustration"))
    photo = data_uri(c.get("photo"))
    hl = c["headline"]
    hs = 66 if len(hl) < 40 else 58 if len(hl) < 70 else 50
    hero = c.get("hero_svg", "")
    ill_h = 560 if ill else (520 if hero else 0)
    avatar = (f'<img class="av" src="{photo}">' if photo else
              f'<div class="av ph">{e((c.get("name") or "ز")[0])}</div>')
    fonts = (HERE / "fonts" / "fonts.css").read_text().replace("url('", f"url('file://{HERE}/fonts/")
    return f"""<!doctype html><html lang="ar"><head><meta charset="utf-8"><style>
{fonts}
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:1080px;height:1350px;overflow:hidden;background:{bg}}}
.stage{{position:absolute;inset:0;direction:rtl;color:{ink};font-family:'IBM Plex Sans Arabic';overflow:hidden}}
.ill{{position:absolute;top:0;left:0;right:0;height:{ill_h}px;background:url('{ill}') center/cover}}
.ill::after{{content:"";position:absolute;inset:0;background:linear-gradient(to bottom,transparent 55%,{bg} 100%)}}
.hero{{position:absolute;top:70px;left:0;right:0;height:{ill_h-70}px;display:flex;align-items:center;justify-content:center}}
.hero svg{{height:100%;width:auto}}
.body{{position:absolute;top:{ill_h + (40 if ill_h else 150)}px;right:96px;left:96px;bottom:230px;display:flex;flex-direction:column;justify-content:{'flex-start' if ill_h else 'center'};gap:22px}}
.label{{display:inline-flex;align-self:flex-start;align-items:center;gap:12px;font-family:'Noto Kufi Arabic';font-weight:600;font-size:24px;color:{acc}}}
.label::before{{content:"";width:40px;height:4px;background:{acc};border-radius:2px}}
h1{{font-weight:700;font-size:{hs}px;line-height:1.45;text-wrap:balance}}
ul{{list-style:none;display:flex;flex-direction:column;gap:10px;margin-top:4px}}
li{{display:flex;gap:18px;align-items:baseline;font-size:34px;font-weight:500;line-height:1.5}}
.d{{flex:none;width:12px;height:12px;background:{acc};transform:translateY(-6px) rotate(45deg)}}
.q{{font-size:32px;font-weight:500;color:{acc};margin-top:6px}}
.src{{font-size:20px;font-weight:300;opacity:.6}}
.bar{{position:absolute;left:0;right:0;bottom:0;height:190px;background:{ink};color:{bg};display:flex;align-items:center;padding:0 96px;gap:28px}}
.av{{width:128px;height:128px;border-radius:50%;object-fit:cover;border:5px solid {acc};flex:none;margin-top:-70px;background:{soft}}}
.ph{{display:flex;align-items:center;justify-content:center;font-family:'Amiri';font-weight:700;font-size:64px;color:{ink}}}
.who{{display:flex;flex-direction:column;gap:2px}}
.nm{{font-family:'Amiri';font-weight:700;font-size:40px;line-height:1.2}}
.hd{{font-size:24px;font-weight:300;opacity:.75;direction:ltr;text-align:right}}
.sp{{flex:1}}
.ph-n{{display:flex;align-items:center;gap:14px;font-size:30px;font-weight:500;direction:ltr;letter-spacing:1px}}
.ph-n svg{{width:34px;height:34px}}
</style></head><body><div class="stage">
{f'<div class="ill"></div>' if ill else (f'<div class="hero">{hero}</div>' if hero else '')}
<div class="body"><span class="label">{e(label)}</span><h1>{e(hl)}</h1><ul>{pts}</ul>{q}{src}</div>
<div class="bar">{avatar}<div class="who"><span class="nm">{e(c.get('name','زياد'))}</span><span class="hd">{e(c.get('handle',''))}</span></div>
<span class="sp"></span>
{f'<span class="ph-n"><svg viewBox="0 0 24 24" fill="none" stroke="{acc}" stroke-width="1.8"><path d="M20.5 3.5A11 11 0 0 0 3.6 17.2L2.5 21.5l4.4-1.1A11 11 0 1 0 20.5 3.5Z"/><path d="M8.5 7.5c.3-.6.6-.6 1-.6h.6c.2 0 .5 0 .7.5l.9 2.1c.1.3 0 .6-.2.8l-.6.7c-.2.2-.2.4 0 .7.7 1.2 1.7 2.1 2.9 2.8.3.2.5.1.7-.1l.8-.9c.2-.3.5-.3.8-.2l2 1c.3.1.5.3.5.6 0 .9-.6 2-1.6 2.2-1 .2-2.6.1-4.8-1.2-2.4-1.5-3.8-3.7-4.2-4.7-.5-1.1-.3-2.6.5-3.3Z"/></svg>{e(c["phone"])}</span>' if c.get("phone") else ''}
</div></div></body></html>"""


NODE = r"""
const {chromium}=require('playwright');
(async()=>{const [src,out]=process.argv.slice(2);
const b=await chromium.launch();const pg=await b.newPage({viewport:{width:1080,height:1350},deviceScaleFactor:1});
await pg.goto('file://'+src);await pg.evaluate(()=>document.fonts.ready);await pg.waitForTimeout(400);
for(let i=0;i<10;i++){const over=await pg.evaluate(()=>{const m=document.querySelector('.body');return m.scrollHeight>m.clientHeight+2});
 if(!over)break;await pg.evaluate(()=>{for(const el of document.querySelectorAll('.body h1,.body li,.body .q')){
 const s=parseFloat(getComputedStyle(el).fontSize);el.style.fontSize=(s*0.93)+'px'}})}
await pg.screenshot({path:out,type:'png'});await b.close();})().catch(e=>{console.error(e);process.exit(1)});
"""


def render(c, out):
    d = tempfile.mkdtemp()
    src, js = os.path.join(d, "p.html"), os.path.join(d, "s.js")
    open(src, "w", encoding="utf-8").write(build(c))
    open(js, "w").write(NODE)
    subprocess.run(["node", js, src, os.path.abspath(out)], check=True)


if __name__ == "__main__":
    c = json.load(open(sys.argv[1], encoding="utf-8"))
    base = pathlib.Path(sys.argv[1]).resolve().parent
    for k in ("illustration", "photo"):
        if c.get(k) and not str(c[k]).startswith(("http", "data:", "/")):
            c[k] = str(base / c[k])
    render(c, sys.argv[2])
    print(sys.argv[2])
