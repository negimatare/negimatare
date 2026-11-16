"""Draw the static profile SVGs from profile.json. generate.py drives this module."""
import base64
import html
import mimetypes
import re
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / 'sources'
OUT = None      # work folder, set by generate.py
ART = []        # concept slices as (data URI, x, y, w, h), see load_art()
# Only these two slices of the original 954x1648 concept are drawn; each file is that
# exact crop, placed back at its original coordinates.
ART_PIECES = {'concept-header.png': (0, 0, 954, 655), 'concept-footer.png': (25, 1348, 906, 258)}
W, H = 954, 1648
INK = '#08090e'
FONT = 'Arial, Helvetica, sans-serif'
TITLE_FONT = 'Arial, sans-serif'  # same face as the ABOUT ME heading
STACK_NAMES = {'csharp':'C#','typescript':'TypeScript','javascript':'JavaScript','react':'React','redux':'Redux','tailwindcss':'Tailwind CSS','nodejs':'Node.js','dotnet':'.NET','python':'Python','azure':'Azure','amazonwebservices':'AWS','docker':'Docker','playwright':'Playwright'}
STACK_STATIC_MAX = 10  # more icons than this turn the tech stack into a carousel


def esc(value):
    return html.escape(str(value), quote=True)


def uri(path):
    path = Path(path)
    mime = mimetypes.guess_type(path.name)[0] or 'application/octet-stream'
    return f'data:{mime};base64,' + base64.b64encode(path.read_bytes()).decode()


def local_file(value):
    path = (SRC / value).resolve()
    if not path.is_relative_to(SRC):
        raise ValueError('Asset paths must stay inside scripts/sources/.')
    if not path.is_file():
        raise ValueError(f'Missing image: {value}')
    return path


def image(href, x, y, width, height, fit='xMidYMid slice'):
    return f'<image href="{href}" x="{x}" y="{y}" width="{width}" height="{height}" preserveAspectRatio="{fit}"/>'


def text(x, y, value, size=22, fill='#e9e8ed', weight='400', extra=''):
    return f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" font-weight="{weight}" fill="{fill}" {extra}>{esc(value)}</text>'


def svg(width, height, body, title):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img"><title>{esc(title)}</title>{body}</svg>'


def load_art():
    global ART
    ART = [(uri(SRC / name), *box) for name, box in ART_PIECES.items()]


def art_region(x, y, width, height, dx=0, dy=0, dw=None, dh=None):
    dw, dh = dw or width, dh or height
    piece = next((p for p in ART if p[1] <= x and p[2] <= y and x + width <= p[1] + p[3] and y + height <= p[2] + p[4]), None)
    if piece is None:
        raise ValueError(f'No concept slice in ART_PIECES covers {x},{y} {width}x{height}.')
    cid='crop_'+re.sub(r'[^a-zA-Z0-9_]','_',f'{x}_{y}_{dx}_{dy}_{dw}_{dh}')
    return f'<defs><clipPath id="{cid}"><rect x="{dx}" y="{dy}" width="{dw}" height="{dh}"/></clipPath></defs><g clip-path="url(#{cid})"><svg x="{dx}" y="{dy}" width="{dw}" height="{dh}" viewBox="{x} {y} {width} {height}" overflow="hidden" preserveAspectRatio="xMidYMid slice">{image(*piece)}</svg></g>'


def frame_title(label):
    body = ('<rect width="954" height="64" fill="#08090e"/>'
            '<path d="M17 64V26L43 6H350L374 23H930L940 34V64" fill="none" stroke="#d8d4d9" stroke-width="1.5"/>'
            '<path d="M21.000 64.000L21.000 27.970L44.360 10.000L348.727 10.000L372.727 27.000L928.231 27.000L936.000 35.546L936.000 64.000" fill="none" stroke="#b52040" stroke-width="1.5"/>'
            '<path d="M32 52L55 19H68L45 52ZM52 52L75 19H85L62 52ZM69 52L92 19H99L76 52Z" fill="#ed0028"/>'
            f'<text x="112" y="45" font-family="{TITLE_FONT}" font-weight="900" font-style="italic" font-size="28" fill="#f8f7f6">{esc(label)}</text>')
    return svg(W,64,body,label)


CARD_W, CARD_H = 310, 248
ARIAL = '/System/Library/Fonts/Supplemental/Arial.ttf'
ARIAL_BOLD = '/System/Library/Fonts/Supplemental/Arial Bold.ttf'


def text_width(value, size, spacing=0, bold=True):
    """Width of Arial text in SVG units (falls back to an estimate without the font)."""
    try:
        from PIL import ImageFont
        width = ImageFont.truetype(ARIAL_BOLD if bold else ARIAL, 100).getlength(value) * size / 100
    except (ImportError, OSError):
        width = len(value) * size * (.68 if bold else .55)
    return width + spacing * len(value)


def wrap_width(value, size, max_width, bold=False):
    """Greedy word wrap by rendered width rather than character count."""
    lines = []
    for word in value.split():
        if lines and text_width(lines[-1] + ' ' + word, size, bold=bold) <= max_width:
            lines[-1] += ' ' + word
        else:
            lines.append(word)
    return lines


def chips(tags, x, y, max_x):
    out = ''
    for tag in tags:
        label = tag.upper()
        w = text_width(label, 9, .6) + 16
        if x + w > max_x:
            raise ValueError('Project tags must fit on one row; use fewer or shorter tags.')
        out += (f'<rect x="{x}" y="{y}" width="{w:.1f}" height="18" rx="9" fill="#1c0b13" stroke="#b52040" stroke-width="1"/>'
                f'<text x="{x+8}" y="{y+12.4}" font-family="{FONT}" font-size="9" font-weight="700" letter-spacing=".6" fill="#f3c6d2">{esc(label)}</text>')
        x += w + 6
    return out


def card(project, i):
    width, height = CARD_W, CARD_H
    body = f'<defs><clipPath id="card"><rect x="1" y="1" width="308" height="{height-2}" rx="12"/></clipPath></defs>'
    body += f'<g clip-path="url(#card)"><rect width="310" height="{height}" fill="#08090f"/>'
    if project.get('banner'):
        body += image(uri(OUT / f"banner-{project['banner']}.png"),0,0,310,126)
    elif project.get('image'):
        body += image(uri(local_file(project['image'])),0,0,310,126)
    else:
        raise ValueError(f'Project "{project["title"]}" needs a "banner" (lib/banners.py) or an "image" (sources/).')
    body += '<rect y="125" width="310" height="2" fill="#7c7481"/>'
    # Title in the section-title face; description matches the About text size on screen
    # (cards show at 31% of the profile width, so 13.5 here reads like the About's 13).
    title_lines = wrap_width(project['title'],19,276,bold=True) or ['Untitled project']
    if len(title_lines)>2:
        raise ValueError('Project titles must fit on two lines.')
    y = 153
    for line in title_lines:
        body += (f'<text x="17" y="{y}" font-family="{TITLE_FONT}" font-size="19" font-weight="900" '
                 f'font-style="italic" fill="#f8f7f6">{esc(line)}</text>')
        y += 21
    desc = wrap_width(project.get('description',''),13.5,276)
    max_desc_lines=3 if len(title_lines)==1 else 2
    if len(desc)>max_desc_lines:
        raise ValueError(f'This project description must fit on {max_desc_lines} lines; shorten its title or description.')
    y += 1
    for line in desc:
        body += text(17,y,line,13.5,fill='#d5d4da')
        y += 16.5
    meta = []
    if project.get('stars') is not None:
        meta.append('★ '+str(project['stars']))
    if project.get('forks') is not None:
        meta.append('Forks '+str(project['forks']))
    meta_text = '   '.join(meta)
    if meta_text:
        body += f'<text x="293" y="{height-21.6}" text-anchor="end" font-family="{FONT}" font-size="11" font-weight="700" fill="#f6be36">{esc(meta_text)}</text>'
    body += chips(project.get('tags',[]),17,height-34,293-(text_width(meta_text,11)+8 if meta_text else 0))
    body += f'</g><rect x="1" y="1" width="308" height="{height-2}" rx="12" fill="none" stroke="#d3d0d9" stroke-width="1.5"/>'
    return svg(width,height,body,project['title'])


def make_assets(cfg):
    if len(cfg['projects'])!=3:
        raise ValueError('This layout expects exactly three project cards.')
    result = {}
    def put(name, content):
        # Preserve artwork inside the outer stroke; alpha outside it.
        top='M17 64V26L43 6H350L374 23H930L940 34V64'
        outlines={
            'intro':'M17 26L35 8H922L940 26V631L922 649H35L17 631Z',
            'footer':'M17 22L33 6H923L940 22V291L925 303H31L17 291Z',
            'tech-stack':top+'V158L929 170H29L17 158Z',
            'projects-header':top+'Z',
            'stats-header':top+'Z',
            'section-bottom':'M17 0V4L28 14H929L940 4V0Z',
            'stats-empty':'M17 0H940V122H17Z'
        }
        if name in outlines:
            head,tail=content.split('</title>',1)
            content=head+'</title><defs><mask id="outer-alpha" maskUnits="userSpaceOnUse" x="0" y="0" width="954" height="700"><path d="'+outlines[name]+'" fill="white" stroke="white" stroke-width="1.5" stroke-linejoin="miter"/></mask></defs><g mask="url(#outer-alpha)">'+tail.rsplit('</svg>',1)[0]+'</g></svg>'
        (OUT/(name+'.svg')).write_text(content,encoding='utf-8')
        result[name] = content
    # Keep the slanted hero/About boundary inside ONE image.
    intro=art_region(0,0,W,655)
    intro += '<path d="M17 445L421 427L337 649H17Z" fill="#08090e"/>'
    intro += '<path d="M17 445L421 427L337 649H17Z" fill="none" stroke="#d6d4da" stroke-width="1.5"/>'
    intro += '<path d="M17 435L940 397" stroke="#08090e" stroke-width="13"/><path d="M17 435L940 397" stroke="#ddd9df" stroke-width="2"/>'
    intro += '<path d="M35 475L52 451H62L45 475ZM53 475L70 451H78L61 475Z" fill="#ed0028"/>'
    intro += '<text x="94" y="472" font-family="Arial, sans-serif" font-style="italic" font-size="27" font-weight="900" fill="white">ABOUT ME</text>'
    lines=cfg['about_lines']
    if len(lines)>10:
        raise ValueError('About supports at most 10 lines in this layout.')
    for i,line in enumerate(lines):
        intro += text(34,493+i*cfg.get('about_line_height',15.2),line,cfg.get('about_font_size',13))
    outer='M17 26L35 8H922L940 26V631L922 649H35L17 631Z'
    inner='M23 28L38 14H919L934 28V628L919 643H38L23 628Z'
    intro='<rect width="954" height="655" fill="#08090e"/><defs><clipPath id="intro-edge"><path d="'+inner+'"/></clipPath></defs><g clip-path="url(#intro-edge)">'+intro+'</g>'
    intro+='<path d="'+outer+'" fill="none" stroke="#d6d4da" stroke-width="1.5"/><path d="'+inner+'" fill="none" stroke="#b52040" stroke-width="1"/>' 
    put('intro',svg(W,655,intro,cfg['about_alt']))
    stack = '<rect width="954" height="110" fill="#08090e"/>'
    stack += '<path d="M17 0V94L29 106H929L940 94V0" fill="none" stroke="#d8d4d9" stroke-width="1.5"/>'
    stack += '<path d="M21 0V92.343L30.657 102H927.343L936 92.556V0" fill="none" stroke="#b52040" stroke-width="1"/>'
    if not cfg['stack']:
        raise ValueError('Stack must contain at least one icon.')
    if len(cfg['stack'])<=STACK_STATIC_MAX:
        for i,key in enumerate(cfg['stack']):
            cx=64+(i+.5)*(826/len(cfg['stack']))
            stack += image(uri(local_file('icons/'+key+'.svg')),cx-31,18,62,62,'xMidYMid meet')
    else:
        # Carousel: the strip is drawn twice side by side, so scrolling it by
        # exactly one strip width (data-strip) loops seamlessly. animate.py adds the motion.
        slot=90
        strip=len(cfg['stack'])*slot
        icons=''.join(image(uri(local_file('icons/'+key+'.svg')),i*slot+(slot-62)/2,18,62,62,'xMidYMid meet') for i,key in enumerate(cfg['stack']))
        stack += ('<defs><clipPath id="stack-window"><rect x="24" y="0" width="909" height="90"/></clipPath>'
                  '<linearGradient id="stack-fade-l"><stop stop-color="#08090e"/><stop offset="1" stop-color="#08090e" stop-opacity="0"/></linearGradient>'
                  '<linearGradient id="stack-fade-r" x1="1" x2="0"><stop stop-color="#08090e"/><stop offset="1" stop-color="#08090e" stop-opacity="0"/></linearGradient></defs>')
        stack += f'<g clip-path="url(#stack-window)"><g transform="translate(24 0)"><g class="stack-strip" data-strip="{strip}">{icons}<g transform="translate({strip} 0)">{icons}</g></g></g></g>'
        stack += '<rect x="24" y="0" width="70" height="90" fill="url(#stack-fade-l)"/><rect x="863" y="0" width="70" height="90" fill="url(#stack-fade-r)"/>'
    put('tech-stack',svg(W,174,frame_title('TECH STACK').split('</title>',1)[1].rsplit('</svg>',1)[0]+'<g transform="translate(0 64)">'+stack+'</g>',', '.join(STACK_NAMES.get(k,k) for k in cfg['stack'])))
    put('projects-header',frame_title('PROJECTS'))
    for i,p in enumerate(cfg['projects']):
        if p.get('url') and not p['url'].startswith(('https://','http://')):
            raise ValueError('Project links must be HTTP(S) URLs.')
        put('project-'+str(i+1),card(p,i))
    put('stats-header',frame_title('GitHub Stats'))
    put('stats-empty',svg(W,122,'<rect width="954" height="122" fill="#08090e"/><path d="M17 0V122M940 0V122" stroke="#d8d4d9" stroke-width="1.5"/>','Space reserved for your own statistics.'))
    put('section-bottom',svg(W,18,'<rect width="954" height="18" fill="#08090e"/><path d="M17 0V4L28 14H929L940 4V0" fill="none" stroke="#d8d4d9" stroke-width="1.5"/><path d="M22 0V2L31 10H925L936 2V0" fill="none" stroke="#b52040"/>','Section closing border'))
    footer = '<rect width="954" height="311" fill="#08090e"/><defs><clipPath id="footer-edge"><path d="M22 24L36 11H920L935 25V288L922 298H34L22 288Z"/></clipPath></defs><g clip-path="url(#footer-edge)">'+art_region(25,1348,906,258,22,11,913,287).replace('preserveAspectRatio="xMidYMid slice"', 'preserveAspectRatio="none"')+'</g>' 
    footer += '<path d="M17 22L33 6H923L940 22V291L925 303H31L17 291Z" fill="none" stroke="#d6d4da" stroke-width="1.5"/><path d="M22 24L36 11H920L935 25V288L922 298H34L22 288Z" fill="none" stroke="#b52040"/>' 
    # Replace the raster button with precise vector geometry.
    footer += '<rect x="47" y="118" width="257" height="103" rx="22" fill="#000000"/>'
    footer += '<rect x="53" y="145" width="224" height="77" rx="15" fill="#030406" stroke="#d6d4da" stroke-width="1.4"/>'
    footer += '<rect x="69" y="160" width="46" height="46" rx="6" fill="#0a86df"/>'
    footer += '<text x="74" y="197" font-family="Arial, Helvetica, sans-serif" font-size="40" font-weight="900" fill="#030406">in</text>'
    footer += '<text x="132" y="193" font-family="Arial, Helvetica, sans-serif" font-size="28" font-weight="600" fill="#f5f5f7">LinkedIn</text>'
    put('footer',svg(W,311,footer,"Let's connect. LinkedIn. Create. Improve. Repeat."))
    if cfg.get('stats_image'):
        from PIL import Image
        path=local_file(cfg['stats_image'])
        with Image.open(path) as im:
            iw,ih=im.size
        h=max(110,round(ih*908/iw)+32)
        body='<rect width="954" height="'+str(h)+'" fill="#08090e"/>'
        body+=image(uri(path),23,16,908,h-32,'xMidYMid meet')
        body+='<path d="M17 0V'+str(h)+'M940 0V'+str(h)+'" stroke="#d8d4d9"/>'
        put('stats-content',svg(W,h,body,'Personal GitHub statistics supplied by Samuel.'))
    return result
