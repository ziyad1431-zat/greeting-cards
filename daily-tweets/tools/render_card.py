#!/usr/bin/env python3
"""مولّد بطاقات التغريدة اليومية — هوية «حبر هادئ».

الاستخدام:
    python3 render_card.py card.json out.png
card.json:
    {
      "text": "نص التغريدة (الإيموجي والوسوم تنحذف تلقائياً من البطاقة)",
      "theme": "productivity",      # أحد مفاتيح THEMES تحت
      "date": "2026-11-05",         # اختياري
      "signature": "زياد",           # اختياري
      "handle": "@handle"           # اختياري
    }
المقاس 1080×1350 (4:5) وهو أكبر مساحة يعرضها X كاملة في الخط الزمني.
"""
import json, re, sys, html, datetime, pathlib
import subprocess

HERE = pathlib.Path(__file__).resolve().parent

THEMES = {
    # key: (label, bg, ink, accent, pattern opacity, serif?)
    "self":         ("تطوير الذات", "#F4EEE3", "#1F3B3A", "#B5763A", .07, False),
    "tech":         ("تقنية",       "#0F1B2B", "#E9EEF4", "#5EC4C9", .09, False),
    "productivity": ("إنتاجية",     "#F2EBDD", "#2A2420", "#C0532F", .07, False),
    "reflection":   ("تأمل",        "#1C1B19", "#EDE6D6", "#C9A45C", .08, True),
    "spiritual":    ("جمعة مباركة", "#10302A", "#F1EAD8", "#CFAE63", .10, True),
    "trivia":       ("معلومة",      "#F5F3EE", "#1E2550", "#D2633A", .06, False),
    "weekly":       ("وقفة الأسبوع", "#2B1E33", "#F2E9EF", "#E0A458", .09, False),
    "leadership":   ("إدارة وقيادة", "#EDE9E1", "#14213D", "#A4161A", .07, False),
    "teamwork":     ("عمل جماعي",   "#E8EFEA", "#173A2E", "#D08C2E", .07, False),
    "marketing":    ("تسويق",       "#FBF4EC", "#2C1A12", "#E2552F", .07, False),
}

AR_DIGITS = str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")
EMOJI_RE = re.compile(
    "[\U0001F000-\U0001FAFF☀-➿⬀-⯿️‍⏩-⏺⌚⌛]+")


def clean(text: str) -> list[str]:
    text = EMOJI_RE.sub("", text)
    text = re.sub(r"(^|\s)#\S+", "", text)          # الوسوم
    text = re.sub(r"https?://\S+", "", text)         # الروابط
    paras = [re.sub(r"[ \t]+", " ", p).strip() for p in re.split(r"\n\s*\n|\n", text)]
    return [p for p in paras if p]


def pattern_svg(color: str, opacity: float) -> str:
    """نجمة ثمانية متكررة بخط رفيع — زخرفة هندسية هادئة في الزاوية."""
    star = ('<g fill="none" stroke="{c}" stroke-width="1.4">'
            '<rect x="-60" y="-60" width="120" height="120"/>'
            '<rect x="-60" y="-60" width="120" height="120" transform="rotate(45)"/>'
            '<circle r="34"/><circle r="85"/></g>').format(c=color)
    cells = []
    for i in range(-1, 5):
        for j in range(-1, 5):
            cells.append(f'<g transform="translate({i*170},{j*170})">{star}</g>')
    return (f'<svg class="pattern" width="760" height="760" viewBox="0 0 760 760" '
            f'style="opacity:{opacity}">{"".join(cells)}</svg>')


def build_html(card: dict) -> str:
    key = card.get("theme", "self")
    label, bg, ink, accent, pop, serif = THEMES.get(key, THEMES["self"])
    label = card.get("label") or label
    paras = clean(card["text"])
    if not paras:
        raise SystemExit("النص فاضي بعد التنظيف")

    head, rest = paras[0], paras[1:]
    question = rest.pop() if rest and rest[-1].endswith("؟") else None
    total = len(" ".join(paras))

    # مقاس الخط حسب الطول — المهم يبقى العنوان هو البطل
    if total < 70:   hs, bs = 84, 40
    elif total < 120: hs, bs = 70, 38
    elif total < 180: hs, bs = 60, 36
    else:            hs, bs = 52, 33

    def para_html(p):
        if re.match(r"^\s*([◆•\-–]|[١٢٣٤٥٦٧٨٩0-9][\.\)\-])\s*", p):
            p = re.sub(r"^\s*([◆•\-–]|[١٢٣٤٥٦٧٨٩0-9][\.\)\-])\s*", "", p)
            return f'<p class="item"><span class="dot"></span>{html.escape(p)}</p>'
        return f'<p>{html.escape(p)}</p>'

    body = "".join(para_html(p) for p in rest)
    q = f'<p class="q">{html.escape(question)}</p>' if question else ""

    d = card.get("date") or datetime.date.today().isoformat()
    dd = datetime.date.fromisoformat(d)
    date_s = f"{dd.day:02d} / {dd.month:02d} / {dd.year}".translate(AR_DIGITS)

    sig = html.escape(card.get("signature", "زياد"))
    handle = html.escape(card.get("handle", ""))
    head_font = "'Amiri', serif" if serif else "'IBM Plex Sans Arabic', sans-serif"
    head_w = 700 if serif else 700
    fonts_css = (HERE / "fonts" / "fonts.css").read_text().replace(
        "url('", f"url('file://{HERE}/fonts/")

    return f"""<!doctype html><html lang="ar"><head><meta charset="utf-8">
<style>
{fonts_css}
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:1080px;height:1350px;overflow:hidden}}
.stage{{position:absolute;inset:0;overflow:hidden;direction:rtl}}
body{{background:{bg};color:{ink};font-family:'IBM Plex Sans Arabic',sans-serif;
 position:relative;overflow:hidden;-webkit-font-smoothing:antialiased}}
.grain{{position:absolute;inset:0;opacity:.35;mix-blend-mode:multiply;pointer-events:none}}
.pattern{{position:absolute;top:-300px;left:-300px;-webkit-mask-image:radial-gradient(circle at 300px 300px,#000 0,#000 30%,transparent 70%);mask-image:radial-gradient(circle at 300px 300px,#000 0,#000 30%,transparent 70%)}}
.frame{{position:absolute;inset:48px;border:1.5px solid {ink}22}}
.top{{position:absolute;top:104px;right:120px;left:120px;display:flex;align-items:center;gap:22px}}
.label{{font-family:'Noto Kufi Arabic';font-weight:600;font-size:26px;color:{accent};letter-spacing:0}}
.rule{{flex:1;height:1.5px;background:{ink}33}}
.date{{font-weight:300;font-size:24px;opacity:.6}}
.main{{position:absolute;top:230px;bottom:250px;right:120px;left:120px;display:flex;
 flex-direction:column;justify-content:center;gap:26px}}
h1{{font-family:{head_font};font-weight:{head_w};font-size:{hs}px;line-height:1.55;text-wrap:balance}}
h1::before{{content:"";display:block;width:84px;height:6px;background:{accent};margin-bottom:46px;border-radius:3px}}
p{{font-weight:300;font-size:{bs}px;line-height:1.85;opacity:.88;text-wrap:pretty}}
p.item{{display:flex;gap:24px;align-items:baseline;line-height:1.6}}
.dot{{flex:none;width:12px;height:12px;background:{accent};transform:translateY(-8px) rotate(45deg)}}
p.q{{font-weight:500;color:{accent};opacity:1;margin-top:8px}}
.foot{{position:absolute;bottom:104px;right:120px;left:120px;display:flex;align-items:center;gap:22px}}
.sig{{font-family:'Amiri';font-weight:700;font-size:38px}}
.handle{{font-weight:300;font-size:24px;opacity:.6;direction:ltr}}
.mark{{width:18px;height:18px;border:2px solid {accent};transform:rotate(45deg)}}
</style></head><body><div class="stage">
<svg class="grain" width="1080" height="1350"><filter id="n"><feTurbulence type="fractalNoise"
 baseFrequency=".85" numOctaves="3" stitchTiles="stitch"/><feColorMatrix values="0 0 0 0 .5 0 0 0 0 .45 0 0 0 0 .4 0 0 0 .18 0"/></filter>
 <rect width="100%" height="100%" filter="url(#n)"/></svg>
{pattern_svg(ink, pop)}
<div class="frame"></div>
<div class="top"><span class="label">{html.escape(label)}</span><span class="rule"></span><span class="date">{date_s}</span></div>
<div class="main"><h1>{html.escape(head)}</h1>{body}{q}</div>
<div class="foot"><span class="mark"></span><span class="sig">{sig}</span><span class="rule"></span><span class="handle">{handle}</span></div>
</div></body></html>"""


NODE_SHOT = r"""
const {chromium}=require('playwright');
(async()=>{const [src,out]=process.argv.slice(2);
const b=await chromium.launch();const pg=await b.newPage({viewport:{width:1080,height:1350},deviceScaleFactor:1});
await pg.goto('file://'+src);await pg.evaluate(()=>document.fonts.ready);await pg.waitForTimeout(300);
for(let i=0;i<8;i++){const over=await pg.evaluate(()=>{const m=document.querySelector('.main');return m.scrollHeight>m.clientHeight+2});
 if(!over)break;await pg.evaluate(()=>{for(const el of document.querySelectorAll('.main h1,.main p')){
 const s=parseFloat(getComputedStyle(el).fontSize);el.style.fontSize=(s*0.92)+'px'}})}
await pg.screenshot({path:out,type:'png'});await b.close();})().catch(e=>{console.error(e);process.exit(1)});
"""


def render(card: dict, out: str):
    """يبني HTML ويصوّره بـ Playwright (نسخة Node المثبّتة مسبقاً في الحاوية)."""
    import tempfile, os
    d = tempfile.mkdtemp()
    src = os.path.join(d, "card.html"); js = os.path.join(d, "shot.js")
    open(src, "w", encoding="utf-8").write(build_html(card))
    open(js, "w").write(NODE_SHOT)
    subprocess.run(["node", js, src, os.path.abspath(out)], check=True)


if __name__ == "__main__":
    card = json.load(open(sys.argv[1], encoding="utf-8"))
    render(card, sys.argv[2])
    print(sys.argv[2])
