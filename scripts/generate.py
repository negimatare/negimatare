#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["playwright>=1.45,<2", "Pillow>=10,<13"]
# ///
"""Generate the GitHub profile into the repo root: assets/ and README.md.

    uv run scripts/generate.py

Content lives in scripts/profile.json. The stats/snake block in the root README,
between the STATS markers, is kept as is (--reset-stats replaces it).
Renders with the installed Google Chrome; without it, run once:
    uv run --with playwright playwright install chromium
"""
import argparse
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

from playwright.sync_api import sync_playwright

GEN = Path(__file__).resolve().parent
REPO = GEN.parent
ASSETS = REPO / 'assets'
sys.path.insert(0, str(GEN / 'lib'))
import animate  # noqa: E402
import banners  # noqa: E402
import build  # noqa: E402

STATS = re.compile(r'<!-- STATS:START -->\n(.*?)\n<!-- STATS:END -->', re.S)


def asset(name):
    """README path of a section: animated SVG where there is motion, PNG otherwise."""
    return f'assets/{name}-animated.svg' if name in animate.NAMES else f'assets/{name}.png'


def launch(p):
    try:
        return p.chromium.launch(channel='chrome')
    except Exception:
        return p.chromium.launch()


def to_png(page, svg_text, path):
    width, height = map(int, re.search(r'width="(\d+)" height="(\d+)"', svg_text).groups())
    page.set_viewport_size({'width': width, 'height': height})
    page.set_content('<style>html,body{margin:0;padding:0}svg{display:block}</style>' + svg_text)
    page.evaluate('Promise.all(Array.from(document.querySelectorAll("image")).map(e => {const i=new Image();i.src=e.href.baseVal;return i.decode()}))')
    page.screenshot(path=str(path), omit_background=True)


def sections(cfg, stats):
    """The profile top to bottom, as (kind, payload) pairs."""
    cards = []
    for i, p in enumerate(cfg['projects']):
        cards.append((f'project-{i+1}', p['title'] + ': ' + p.get('description', ''), p.get('url')))
    return [
        ('img', ('intro', cfg['about_alt'])),
        ('img', ('tech-stack', ', '.join(build.STACK_NAMES.get(k, k) for k in cfg['stack']))),
        ('img', ('projects-header', 'Projects')),
        ('cards', cards),
        ('img', ('stats-header', 'GitHub Stats')),
        ('stats', stats),
        ('img', ('section-bottom', '')),
        ('link', (cfg['linkedin_url'], 'footer', "Let's connect on LinkedIn. Create. Improve. Repeat.")),
    ]


def readme(cfg, stats):
    esc = build.esc
    img = lambda name, alt, width='100%': f'<img src="{asset(name)}" width="{width}" alt="{esc(alt)}" />'
    out = []
    for kind, data in sections(cfg, stats):
        if kind == 'img':
            out.append(img(*data))
        elif kind == 'cards':
            items = [f'<a href="{esc(url)}">{img(n, alt, "31%")}</a>' if url else img(n, alt, '31%') for n, alt, url in data]
            out.append('<p align="center">' + '&nbsp;&nbsp;'.join(items) + '</p>')
        elif kind == 'stats':
            out.append('<!-- STATS:START -->\n' + data + '\n<!-- STATS:END -->')
        elif kind == 'link':
            url, name, alt = data
            out.append(f'<a href="{esc(url)}">{img(name, alt)}</a>')
    return '\n\n'.join(out) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--reset-stats', action='store_true', help='Replace the STATS block with the configured stats_image or an empty slot.')
    args = parser.parse_args()
    cfg = json.loads((GEN / 'profile.json').read_text())
    scale = int(cfg.get('export_scale', 2))
    if scale not in (1, 2, 3, 4):
        raise ValueError('export_scale must be 1, 2, 3 or 4.')

    old = REPO / 'README.md'
    match = None if args.reset_stats or not old.exists() else STATS.search(old.read_text())
    stats_name = 'stats-content' if cfg.get('stats_image') else 'stats-empty'
    stats = match.group(1) if match else f'<img src="{asset(stats_name)}" width="100%" alt="GitHub statistics" />'
    pngs = ['project-1', 'project-2', 'project-3', 'section-bottom'] + ([] if match else [stats_name])

    with tempfile.TemporaryDirectory() as tmp, sync_playwright() as p:
        work = Path(tmp)
        browser = launch(p)
        banners.render(browser.new_page(), work, [x['banner'] for x in cfg['projects'] if x.get('banner')])
        build.OUT = work
        build.load_art()
        static = build.make_assets(cfg)
        page = browser.new_page(device_scale_factor=scale)
        for name in pngs:
            to_png(page, static[name], work / f'{name}.png')
        browser.close()

        ASSETS.mkdir(exist_ok=True)
        for name in animate.NAMES:
            (ASSETS / f'{name}-animated.svg').write_text(animate.animated(name, static[name]), encoding='utf-8')
        for name in pngs:
            shutil.copy2(work / f'{name}.png', ASSETS / f'{name}.png')
    old.write_text(readme(cfg, stats), encoding='utf-8')
    print(f'Wrote README.md and {len(animate.NAMES) + len(pngs)} files to assets/.')


if __name__ == '__main__':
    main()
