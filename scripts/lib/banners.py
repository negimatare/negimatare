"""Compose the project-card banners (1240x504, the card's 310x126 at 4x) from sources/projects/."""
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / 'sources/projects'
W, H = 1240, 504


def src(name):
    return (SRC / name).as_uri()


BASE = f'''<!doctype html><meta charset="utf-8"><style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{width:{W}px;height:{H}px;overflow:hidden;position:relative;background:#08090e;font-family:"Segoe UI",Helvetica,Arial,sans-serif}}
.abs{{position:absolute}}
</style>'''


def mochi():
    # The whole 3:1 banner, side margins trimmed (x 50..2150), on its own navy so the
    # grid fades out softly at the top and bottom instead of being cropped.
    x0, x1 = 50, 2150
    k = W / (x1 - x0)
    h = 724 * k
    return BASE + f'''<div class="abs" style="inset:0;background:#021827"></div>
<div class="abs" style="left:0;top:{(H-h)/2}px;width:{W}px;height:{h}px;overflow:hidden;
  -webkit-mask-image:linear-gradient(to bottom,transparent,#000 12%,#000 88%,transparent)">
  <img class="abs" src="{src('mochi-banner.png')}" style="left:{-x0*k}px;top:0;width:{2172*k}px;height:{h}px"></div>'''


def hopshot():
    # Only the box art: art + logo in the middle, the cover's own paw badge and
    # "Fan-made" seal either side, all on the cover's black.
    def piece(box, cx, cy, height):
        x0, y0, x1, y1 = box
        k = height / (y1 - y0)
        w = (x1 - x0) * k
        return (f'<div class="abs" style="left:{cx-w/2}px;top:{cy-height/2}px;width:{w}px;height:{height}px;overflow:hidden">'
                f'<img class="abs" src="{src("hopshot-cover.png")}" style="left:{-x0*k}px;top:{-y0*k}px;width:{1073*k}px"></div>')
    return BASE + f'''<div class="abs" style="inset:0;background:#000"></div>
{piece((52, 70, 1066, 1092), W/2, H/2, 488)}
{piece((76, 1091, 416, 1415), 185, H/2 + 6, 236)}
{piece((748, 1111, 1044, 1397), W - 185, H/2 + 6, 228)}'''


def uikit():
    # Brand gradient + fox logo, with a few mock components to say "UI kit".
    ink = '#2F1E4F'
    return BASE + f'''<style>
.bg{{inset:0;background:linear-gradient(225deg,#fdf7c4 0%,#f9d4b4 28%,#efbcbc 55%,#d8a9be 78%,#a49bb3 100%)}}
.dots{{inset:0;background-image:radial-gradient(rgba(47,30,79,.13) 2px,transparent 2.5px);background-size:28px 28px;
  -webkit-mask-image:linear-gradient(90deg,#000,transparent 60%)}}
.card{{left:768px;top:62px;width:410px;height:380px;border-radius:22px;background:rgba(255,255,255,.62);
  box-shadow:0 18px 40px rgba(47,30,79,.22),inset 0 0 0 1.5px rgba(255,255,255,.8);padding:30px 32px;color:{ink}}}
.row{{display:flex;align-items:center;gap:14px}}
.dot{{width:14px;height:14px;border-radius:50%}}
.label{{font-size:24px;font-weight:600}}
.toggle{{width:66px;height:36px;border-radius:18px;background:{ink};position:relative}}
.toggle::after{{content:"";position:absolute;right:5px;top:5px;width:26px;height:26px;border-radius:50%;background:#fff}}
.input{{height:54px;border-radius:10px;background:#fff;border-bottom:3px solid {ink};font-size:22px;color:#8a7f99;padding:0 18px;display:flex;align-items:center}}
.btn{{height:54px;border-radius:10px;font-size:22px;font-weight:600;display:flex;align-items:center;justify-content:center;padding:0 24px}}
.bar{{height:10px;border-radius:5px;background:rgba(47,30,79,.15);overflow:hidden}}
.bar i{{display:block;width:68%;height:100%;background:linear-gradient(90deg,#e85d6a,{ink})}}
</style>
<div class="abs bg"></div><div class="abs dots"></div>
<img class="abs" src="{src('uikit-logo-full.webp')}" style="left:58px;top:178px;width:620px;filter:drop-shadow(0 6px 14px rgba(47,30,79,.18))">
<div class="abs card">
  <div class="row" style="margin-bottom:28px"><span class="dot" style="background:#e85d6a"></span><span class="dot" style="background:#f4b860"></span><span class="dot" style="background:#9b8fb0"></span></div>
  <div class="row" style="justify-content:space-between;margin-bottom:24px"><span class="label">Dark mode</span><span class="toggle"></span></div>
  <div class="input" style="margin-bottom:24px">Search components…</div>
  <div class="row" style="margin-bottom:28px"><span class="btn" style="background:{ink};color:#fff">Get started</span><span class="btn" style="border:2px solid {ink}">Docs</span></div>
  <div class="bar"><i></i></div>
</div>'''


BANNERS = {'negima-mochi': mochi, 'hopshot': hopshot, 'negima-ui-kit': uikit}


def render(page, out, names):
    """Screenshot each requested banner recipe to out/banner-<name>.png."""
    page.set_viewport_size({'width': W, 'height': H})
    for name in names:
        if name not in BANNERS:
            raise ValueError(f'Unknown banner "{name}"; known: {", ".join(BANNERS)}')
        html = Path(out) / f'banner-{name}.html'
        html.write_text(BANNERS[name](), encoding='utf-8')
        page.goto(html.as_uri(), wait_until='networkidle')
        page.screenshot(path=str(Path(out) / f'banner-{name}.png'))
