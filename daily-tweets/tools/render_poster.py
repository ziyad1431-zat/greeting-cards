#!/usr/bin/env python3
"""قالب «البوستر» الاحترافي (الإصدار ٣) — مستوحى من أسلوب تصاميم ChatGPT:
خلفية دافية بعمق، رقم بارز مجسّم، مشهد مرسوم بالمجسمات (SVG بتدرجات)، بطاقات نقاط بأيقونات،
صندوق سؤال، وتذييل منحني فيه الصورة والاسم والحساب والجوال.

python3 render_poster.py post.json out.png
post.json:
{
  "track": "marketing" | "family" | "self",
  "label": "تسويق",                   # اختياري
  "stat": "٨٣٪", "stat_caption": "من كل ١٠٠ شخص",   # اختياري (الرقم البارز)
  "headline": "٨٣٪ يثقون بتوصية",      # السطر الأول
  "headline_accent": "صديق أكثر من أي إعلان",   # السطر الثاني بلون الثيم
  "points": [{"icon": "handshake", "text": "..."}, ...],   # ≤٣، الأيقونات تحت ICONS
  "question": "...؟", "source": "المصدر: ...",
  "name": "زياد", "handle": "@...", "phone": "05...", "photo": "path"   # photo اختياري
}
"""
import json, sys, html, os, base64, mimetypes, pathlib, subprocess, tempfile

HERE = pathlib.Path(__file__).resolve().parent

# bg-top, bg-bottom, ink, accent, accent-dark, soft, footer
THEMES = {
    "marketing": ("#FFF6EC", "#FBE7D3", "#2B1A10", "#F26A21", "#C44A0C", "#FDE3CC", "#3A2216"),
    "family":    ("#F3F8F4", "#E2EFE6", "#16312A", "#2E9E78", "#1D6E53", "#D6EDE2", "#163A30"),
    "self":      ("#F4F3FF", "#E6E3FB", "#1D1846", "#6C4CF1", "#4A2FC2", "#E2DCFF", "#221C52"),
}
LIGHT = {"marketing": "#FF9A5C", "family": "#6FD3AE", "self": "#A08CFF"}
LABELS = {"marketing": "تسويق", "family": "تنمية أسرية", "self": "تطوير الذات"}

ICONS = {  # 24x24 stroke icons
    "handshake": '<path d="M2 12l4-4 4 2 3-2 3 1 6 4"/><path d="M6 8l-4 4 6 6 2-2"/><path d="M22 13l-6 6-3-3"/><path d="M10 14l2 2M12 12l2 2M14 10l2 2"/>',
    "chat": '<path d="M21 12a8 8 0 0 1-11.5 7.2L4 20l1-4.6A8 8 0 1 1 21 12z"/><path d="M8.5 11h7M8.5 14h4"/>',
    "share": '<circle cx="18" cy="5" r="2.6"/><circle cx="6" cy="12" r="2.6"/><circle cx="18" cy="19" r="2.6"/><path d="M8.3 10.8l7.4-4.4M8.3 13.2l7.4 4.4"/>',
    "heart": '<path d="M12 20s-7-4.4-9-9a5 5 0 0 1 9-3 5 5 0 0 1 9 3c-2 4.6-9 9-9 9z"/>',
    "book": '<path d="M4 5a2 2 0 0 1 2-2h13v16H6a2 2 0 0 0-2 2z"/><path d="M4 19V5M8 7h7"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "home": '<path d="M3 11l9-7 9 7"/><path d="M5 10v10h14V10"/><path d="M10 20v-6h4v6"/>',
    "target": '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1.5"/>',
    "star": '<path d="M12 3l2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1-4.4-4.3 6.1-.9z"/>',
    "check": '<circle cx="12" cy="12" r="9"/><path d="M8 12.5l2.6 2.6L16 9.5"/>',
    "users": '<circle cx="9" cy="8" r="3.2"/><path d="M3 20a6 6 0 0 1 12 0"/><circle cx="17" cy="9" r="2.6"/><path d="M15.5 14.2A5 5 0 0 1 21 19"/>',
    "trend": '<path d="M3 17l6-6 4 4 8-8"/><path d="M15 7h6v6"/>',
    "bulb": '<path d="M9 18h6M10 21h4"/><path d="M12 3a6 6 0 0 0-3.5 10.9c.6.5 1 1.2 1 2.1h5c0-.9.4-1.6 1-2.1A6 6 0 0 0 12 3z"/>',
    "phone_off": '<rect x="7" y="2" width="10" height="20" rx="2"/><path d="M3 3l18 18"/>',
    "mosque": '<path d="M12 3c-3 2-5 4-5 7h10c0-3-2-5-5-7z"/><path d="M5 21V12h14v9M10 21v-4a2 2 0 0 1 4 0v4"/>',
}


def data_uri(p):
    if not p:
        return ""
    if str(p).startswith(("http", "data:")):
        return p
    return f"data:{mimetypes.guess_type(p)[0] or 'image/png'};base64," + base64.b64encode(open(p, "rb").read()).decode()


def pawn(x, y, s, top, side, shade, key):
    """شخصية خشبية مجسّمة (رأس + جسم) بتدرج إضاءة."""
    return f'''
<defs><radialGradient id="h{key}" cx=".35" cy=".3" r=".8"><stop offset="0" stop-color="{top}"/><stop offset="1" stop-color="{side}"/></radialGradient>
<linearGradient id="b{key}" x1="0" x2="1"><stop offset="0" stop-color="{top}"/><stop offset=".6" stop-color="{side}"/><stop offset="1" stop-color="{shade}"/></linearGradient></defs>
<ellipse cx="{x}" cy="{y+2}" rx="{38*s}" ry="{8*s}" fill="#000" opacity=".10"/>
<path d="M{x-34*s},{y} C{x-34*s},{y-50*s} {x-22*s},{y-70*s} {x},{y-70*s} C{x+22*s},{y-70*s} {x+34*s},{y-50*s} {x+34*s},{y} Z" fill="url(#b{key})"/>
<circle cx="{x}" cy="{y-92*s}" r="{24*s}" fill="url(#h{key})"/>'''


def scene(track, acc, accd, soft):
    """مشهد المجسمات حسب المسار."""
    wood = ("#F7E6D0", "#E3C6A3", "#C9A57E")
    hi = (LIGHT.get(track, "#FF9A5C"), acc, accd)
    if track == "family":
        figs = [(150, 330, 1.25, *hi, "a"), (255, 330, 1.15, *wood, "b"), (90, 340, .8, *wood, "c"), (330, 342, .75, *hi, "d")]
        prop = f'''<g transform="translate(250,95)">
<defs><linearGradient id="roof" x1="0" x2="1"><stop offset="0" stop-color="{acc}"/><stop offset="1" stop-color="{accd}"/></linearGradient></defs>
<path d="M-70 60 L0 0 L70 60 Z" fill="url(#roof)"/><rect x="-55" y="58" width="110" height="80" rx="6" fill="#FFF8EE"/>
<rect x="-18" y="92" width="36" height="46" rx="4" fill="{soft}"/><circle cx="0" cy="40" r="10" fill="#FFF8EE"/></g>'''
    elif track == "self":
        figs = [(140, 335, 1.2, *hi, "a"), (250, 340, .9, *wood, "b")]
        prop = f'''<g transform="translate(260,30)">
<path d="M-120 300 L20 60 L160 300 Z" fill="{soft}"/><path d="M20 60 L60 130 L35 120 L20 140 L5 118 L-18 128 Z" fill="#fff" opacity=".85"/>
<path d="M20 60 V-10" stroke="#5a4a3a" stroke-width="5" stroke-linecap="round"/><path d="M20 -10 L75 6 L20 22 Z" fill="{acc}"/></g>'''
    else:  # marketing
        figs = [(120, 335, .95, *wood, "a"), (210, 330, 1.25, *hi, "b"), (300, 338, .9, *wood, "c"), (170, 350, .7, *wood, "d"), (255, 352, .7, *wood, "e")]
        prop = f'''<g transform="translate(40,70) rotate(-16)">
<defs><linearGradient id="mg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffffff"/><stop offset="1" stop-color="#EDE4DA"/></linearGradient>
<linearGradient id="mr" x1="0" x2="1"><stop offset="0" stop-color="{accd}"/><stop offset="1" stop-color="{acc}"/></linearGradient></defs>
<rect x="0" y="40" width="46" height="56" rx="10" fill="url(#mr)"/>
<path d="M44 44 L170 0 L170 136 L44 92 Z" fill="url(#mg)"/>
<ellipse cx="170" cy="68" rx="22" ry="68" fill="url(#mr)"/><ellipse cx="172" cy="68" rx="12" ry="48" fill="#fff"/>
<path d="M58 96 L76 150 L98 146 L84 98" fill="#5a3b28"/>
<g stroke="#FFC14D" stroke-width="7" stroke-linecap="round"><path d="M210 20 L240 0"/><path d="M216 68 L252 68"/><path d="M210 116 L240 136"/></g></g>'''
    body = prop + "".join(pawn(*f) for f in figs)
    return f'<svg viewBox="0 0 420 380" xmlns="http://www.w3.org/2000/svg" direction="ltr">{body}</svg>'


def build(c):
    t = c.get("track", "marketing")
    bg1, bg2, ink, acc, accd, soft, foot = THEMES.get(t, THEMES["marketing"])
    e = html.escape
    label = c.get("label") or LABELS.get(t, "")
    pts = "".join(
        f'<div class="pt"><span class="ic"><svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="1.8" '
        f'stroke-linecap="round" stroke-linejoin="round">{ICONS.get(p.get("icon", "check"), ICONS["check"])}</svg></span>'
        f'<span class="tx">{e(p["text"])}</span></div>' for p in c.get("points", []))
    photo = data_uri(c.get("photo"))
    avatar = f'<img class="av" src="{photo}">' if photo else f'<div class="av ph">{e((c.get("name") or "ز")[0])}</div>'
    stat = ""
    if c.get("stat"):
        stat = f'''<div class="stat"><div class="num">{e(c["stat"])}</div>
<div class="cap">{e(c.get("stat_caption",""))}</div></div>'''
    q = (f'<div class="q"><svg viewBox="0 0 24 24" fill="none" stroke="{acc}" stroke-width="1.8" stroke-linecap="round">'
         f'{ICONS["bulb"]}</svg><span>{e(c["question"])}</span></div>') if c.get("question") else ""
    src = f'<div class="src">{e(c["source"])}</div>' if c.get("source") else ""
    fonts = (HERE / "fonts" / "fonts.css").read_text().replace("url('", f"url('file://{HERE}/fonts/")
    phone = (f'<div class="phone"><svg viewBox="0 0 24 24" fill="none" stroke="{acc}" stroke-width="1.8"><path d="M20.5 3.5A11 11 0 0 0 3.6 17.2L2.5 21.5l4.4-1.1A11 11 0 1 0 20.5 3.5Z"/>'
             f'<path d="M8.5 7.5c.3-.6.6-.6 1-.6h.6c.2 0 .5 0 .7.5l.9 2.1c.1.3 0 .6-.2.8l-.6.7c-.2.2-.2.4 0 .7.7 1.2 1.7 2.1 2.9 2.8.3.2.5.1.7-.1l.8-.9c.2-.3.5-.3.8-.2l2 1c.3.1.5.3.5.6 0 .9-.6 2-1.6 2.2-1 .2-2.6.1-4.8-1.2-2.4-1.5-3.8-3.7-4.2-4.7-.5-1.1-.3-2.6.5-3.3Z"/></svg>'
             f'<span>{e(c["phone"])}</span></div>') if c.get("phone") else ""
    return f"""<!doctype html><html lang="ar"><head><meta charset="utf-8"><style>
{fonts}
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:1080px;height:1350px;overflow:hidden}}
.st{{position:absolute;inset:0;direction:rtl;overflow:hidden;font-family:'IBM Plex Sans Arabic';color:{ink};
 background:radial-gradient(900px 600px at 85% 8%,#fff 0,transparent 60%),linear-gradient(180deg,{bg1},{bg2})}}
.blob{{position:absolute;border-radius:50%;filter:blur(2px)}}
.b1{{width:520px;height:520px;left:-160px;top:420px;background:{soft};opacity:.8}}
.b2{{width:300px;height:300px;right:-90px;top:-80px;background:{soft};opacity:.7}}
.dots{{position:absolute;width:140px;height:100px;background-image:radial-gradient({acc}55 2.4px,transparent 2.6px);background-size:22px 22px}}
.d1{{right:40px;top:470px}} .d2{{left:30px;top:40px}}
/* top: label + stat (right) / scene (left) */
.label{{position:absolute;top:60px;right:64px;display:flex;align-items:center;gap:12px;background:#fff;border-radius:40px;
 padding:10px 26px 10px 18px;font-family:'Noto Kufi Arabic';font-weight:600;font-size:26px;color:{accd};box-shadow:0 8px 24px {accd}22}}
.label i{{width:14px;height:14px;border-radius:50%;background:{acc}}}
.stat{{position:absolute;top:140px;right:64px;width:470px;text-align:center}}
.num{{font-weight:700;font-size:210px;line-height:1;color:{acc};direction:ltr;
 text-shadow:0 2px 0 {accd},0 4px 0 {accd},0 6px 0 {accd},0 8px 0 {accd},0 10px 0 {accd},0 22px 30px {accd}55;letter-spacing:-4px}}
.cap{{display:inline-block;margin-top:26px;background:#fff;border:2.5px dashed {acc}88;border-radius:22px;padding:8px 34px;font-size:34px;font-weight:500}}
.scene{{position:absolute;top:70px;left:30px;width:500px;height:452px}}
.scene svg{{width:100%;height:100%}}
/* headline card */
.main{{position:absolute;top:530px;bottom:158px;right:56px;left:56px;display:flex;flex-direction:column;justify-content:space-between;gap:16px}}
.card{{background:rgba(255,255,255,.88);border-radius:42px;padding:24px 40px 26px;
 text-align:center;box-shadow:0 20px 50px {accd}1f, inset 0 0 0 1.5px #fff}}
.h1{{font-weight:700;font-size:54px;line-height:1.3}}
.h2{{font-weight:700;font-size:64px;line-height:1.35;color:{acc}}}
.sw{{display:block;margin:14px auto 0;width:300px;height:14px}}
/* points */
.pts{{display:flex;flex-direction:column;gap:14px}}
.pt{{display:flex;align-items:center;gap:22px;background:#fff;border:2px solid {soft};border-radius:60px;padding:6px 8px 6px 28px;
 box-shadow:0 8px 22px {accd}14}}
.ic{{flex:none;width:64px;height:64px;border-radius:50%;background:linear-gradient(145deg,{acc},{accd});display:flex;align-items:center;justify-content:center;
 box-shadow:0 6px 14px {accd}55, inset 0 2px 0 #ffffff55}}
.ic svg{{width:36px;height:36px}}
.tx{{font-size:34px;font-weight:500}}
/* question */
.q{{align-self:center;display:flex;align-items:center;justify-content:center;gap:16px;
 border:2.5px solid {acc}66;background:#fff;border-radius:30px;padding:10px 30px;font-size:32px;font-weight:700;color:{accd}}}
.q svg{{width:46px;height:46px;flex:none}}
.src{{text-align:center;margin-top:-6px;font-size:19px;opacity:.55}}
/* footer */
.ft{{position:absolute;left:0;right:0;bottom:0;height:150px}}
.ft svg.wave{{position:absolute;inset:0;width:100%;height:100%}}
.fi{{position:absolute;inset:0;display:flex;align-items:center;padding:30px 64px 0;gap:22px;color:#fff}}
.av{{width:118px;height:118px;border-radius:50%;object-fit:cover;border:5px solid {acc};background:#fff;flex:none;margin-top:-30px;box-shadow:0 8px 20px #0003}}
.ph{{display:flex;align-items:center;justify-content:center;font-family:'Amiri';font-weight:700;font-size:62px;color:{ink}}}
.nm{{font-family:'Amiri';font-weight:700;font-size:40px}}
.sep{{width:2px;height:44px;background:#ffffff55}}
.hd{{font-size:24px;opacity:.8;direction:ltr}}
.sp{{flex:1}}
.phone{{display:flex;align-items:center;gap:12px;font-size:34px;font-weight:700;direction:ltr;letter-spacing:1px}}
.phone svg{{width:40px;height:40px}}
</style></head><body><div class="st">
<div class="blob b1"></div><div class="blob b2"></div><div class="dots d1"></div><div class="dots d2"></div>
<div class="scene">{scene(t, acc, accd, soft)}</div>
<div class="label"><i></i>{e(label)}</div>
{stat}
<div class="main"><div class="card"><div class="h1">{e(c["headline"])}</div><div class="h2">{e(c.get("headline_accent",""))}</div>
<svg class="sw" viewBox="0 0 300 14"><path d="M4 10 Q150 -4 296 10" stroke="#FFB23F" stroke-width="6" fill="none" stroke-linecap="round"/></svg></div>
<div class="pts">{pts}</div>
{q}{src}</div>
<div class="ft"><svg class="wave" viewBox="0 0 1080 150" preserveAspectRatio="none"><path d="M0 40 Q540 -30 1080 40 V150 H0Z" fill="{foot}"/></svg>
<div class="fi">{avatar}<span class="nm">{e(c.get("name","زياد"))}</span><span class="sep"></span><span class="hd">{e(c.get("handle",""))}</span><span class="sp"></span>{phone}</div></div>
</div></body></html>"""


NODE = r"""
const {chromium}=require('playwright');
(async()=>{const [src,out]=process.argv.slice(2);
const b=await chromium.launch();const pg=await b.newPage({viewport:{width:1080,height:1350},deviceScaleFactor:1});
await pg.goto('file://'+src);await pg.evaluate(()=>document.fonts.ready);await pg.waitForTimeout(400);
// shrink headline / points if they overflow their boxes
for(let i=0;i<10;i++){const o=await pg.evaluate(()=>{const c=document.querySelector('.card');const p=document.querySelector('.pts');
 const m=document.querySelector('.main');return m.scrollHeight>m.clientHeight+2});
 if(!o)break;await pg.evaluate(()=>{for(const el of document.querySelectorAll('.h1,.h2,.tx,.q')){const s=parseFloat(getComputedStyle(el).fontSize);el.style.fontSize=(s*0.97)+'px'}})}
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
    if c.get("photo") and not str(c["photo"]).startswith(("http", "data:", "/")):
        c["photo"] = str(base / c["photo"])
    render(c, sys.argv[2])
    print(sys.argv[2])
