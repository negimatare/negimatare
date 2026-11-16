"""Add gentle SVG animations (CSS only) on top of the static SVGs from build.py."""
import math
import re

NAMES=('intro','tech-stack','projects-header','stats-header','footer')
TOP='M21 64L21 27.970L44.360 10L348.727 10L372.727 27L928.231 27L936 35.546L936 64'
STACK=TOP+'V156.343L927.343 166H30.657L21 156.343Z'
CSS='''
.motion-petal {animation:petal-drift var(--duration) linear infinite; animation-delay:var(--delay);opacity:0;}
@keyframes petal-drift {
  0% {transform:translate(0px,0px) rotate(-20deg);opacity:0;}
  12% {opacity:.65;}
  50% {transform:translate(-65px,28px) rotate(75deg);opacity:.65;}
  88% {opacity:.55;}
  100% {transform:translate(-135px,65px) rotate(160deg);opacity:0;}
}
.motion-trace {animation:border-travel 9s linear infinite;stroke-dasharray:55 945;stroke-dashoffset:0;}
@keyframes border-travel {to {stroke-dashoffset:-1000;}}
.motion-stripe {animation:stripe-pulse 5s ease-in-out infinite;animation-delay:var(--delay);}
@keyframes stripe-pulse {0%,65%,100% {opacity:1;} 78% {opacity:.5;} 88% {opacity:1;}}
.motion-front {animation:headlight-glint 7s ease-in-out infinite;opacity:.06;}
@keyframes headlight-glint {0%,58%,100% {opacity:.06;} 68% {opacity:.42;} 77% {opacity:.1;}}
.motion-rear {animation:rear-glow 4.5s ease-in-out infinite;opacity:.1;}
@keyframes rear-glow {0%,100% {opacity:.1;} 50% {opacity:.5;}}
.motion-smoke {animation:smoke-drift 6s ease-out infinite;animation-delay:var(--delay);opacity:0;}
@keyframes smoke-drift {0% {transform:translate(0px,0px) scale(.85);opacity:0;} 20% {opacity:.23;} 65% {opacity:.16;} 100% {transform:translate(48px,-15px) scale(1.22);opacity:0;}}
@media (prefers-reduced-motion: reduce) {.motion-petal,.motion-trace,.motion-front,.motion-rear,.motion-smoke{display:none!important;animation:none!important;}.motion-stripe{animation:none!important;opacity:1!important;}}
'''


def petals(snapshot=None):
    # Petals stay in the landscape, away from the portrait and title.
    items=[]
    values=[(570,65,8.5,-1.3,1.0),(600,150,10,-6,0.8),(510,125,9.5,-3.7,0.7),(730,300,11,-7.5,0.9),(490,220,8,-4.7,0.65),(800,330,12,-2,0.7)]
    for x,y,duration,delay,scale in values:
        shape=f'<g transform="scale({scale})"><path d="M-6 0Q-1-5 6-2Q3 4-3 3Z" fill="#f18aba"/><path d="M-3 1L4-1" stroke="#ffd1e4" stroke-width=".65"/></g>'
        if snapshot is None:
            content=f'<g class="motion-petal" style="--duration:{duration}s;--delay:{delay}s">{shape}</g>'
        else:
            phase=((snapshot-delay)/duration)%1
            dx=-135*phase;dy=65*phase;angle=-20+180*phase
            opacity=min(1,phase/.12,(1-phase)/.12)*.65
            content=f'<g transform="translate({dx:.3f} {dy:.3f}) rotate({angle:.3f})" opacity="{opacity:.3f}">{shape}</g>'
        items.append(f'<g transform="translate({x} {y})">{content}</g>')
    return '<defs><clipPath id="petal-landscape"><path d="M355 30H610V200H916V382L355 405Z"/></clipPath></defs><g clip-path="url(#petal-landscape)">'+''.join(items)+'</g>'


def trace(name,snapshot=None):
    path=STACK if name=='tech-stack' else ('M23 28L38 14H919L934 28V628L919 643H38L23 628Z' if name=='intro' else ('M22 24L36 11H920L935 25V288L922 298H34L22 288Z' if name=='footer' else TOP))
    attrs='class="motion-trace"' if snapshot is None else f'stroke-dasharray="55 945" stroke-dashoffset="{-1000*(snapshot%9)/9:.3f}"'
    return f'<path d="{path}" pathLength="1000" fill="none" stroke="#ff557b" stroke-width="2" stroke-linecap="round" opacity=".85" {attrs}/>'


def stripes(source,snapshot=None):
    # Split the existing compound path, so the real stripes pulse in sequence.
    def replace(match):
        pieces=re.findall(r'M[^M]+',match.group(1))
        result=[]
        for i,path in enumerate(pieces):
            attr=f'class="motion-stripe" style="--delay:{i*.3}s"'
            if snapshot is not None:
                phase=(snapshot-i*.3)%5/5
                opacity=1-.45*max(0,1-abs(phase-.78)/.13)
                attr=f'opacity="{opacity:.3f}"'
            result.append(f'<path d="{path}" fill="#ed0028" {attr}/>')
        return ''.join(result)
    return re.sub(r'<path d="([^"]+)" fill="#ed0028"/>',replace,source)


def headlights(snapshot=None):
    attr='class="motion-front"' if snapshot is None else 'opacity=".32"'
    return '<defs><radialGradient id="warm-glint"><stop stop-color="#fffbe2" stop-opacity=".9"/><stop offset="1" stop-color="#ffd788" stop-opacity="0"/></radialGradient><clipPath id="lamp-glint"><path d="M455 250L492 248L491 269L455 270ZM619 243L664 240L663 265L619 267Z"/></clipPath></defs><g '+attr+'><ellipse cx="474" cy="259" rx="38" ry="20" fill="url(#warm-glint)"/><ellipse cx="642" cy="253" rx="42" ry="21" fill="url(#warm-glint)"/><g clip-path="url(#lamp-glint)"><path d="M452 273L477 246H482L457 275ZM616 269L643 239H649L622 271Z" fill="#fffce6"/></g></g>'


def rear_lights(snapshot=None):
    attr='class="motion-rear"' if snapshot is None else 'opacity=".4"'
    return '<defs><radialGradient id="tail-glow"><stop stop-color="#ff473f" stop-opacity=".95"/><stop offset="1" stop-color="#ff2946" stop-opacity="0"/></radialGradient></defs><g '+attr+'><ellipse cx="592" cy="132" rx="39" ry="18" fill="url(#tail-glow)"/><ellipse cx="729" cy="142" rx="27" ry="16" fill="url(#tail-glow)"/></g>'


def smoke(snapshot=None):
    result=['<defs><clipPath id="smoke-zone"><path d="M752 199Q788 165 805 151Q861 117 934 110V207L785 222L752 214Z"/></clipPath><filter id="smoke-soft" x="-30%" y="-50%" width="170%" height="200%"><feGaussianBlur stdDeviation="1.2"/></filter></defs><g clip-path="url(#smoke-zone)">']
    cloud='<path d="M-33 10C-51 2-39-11-25-9C-30-27-4-33 7-20C16-40 45-30 43-12C68-21 77 6 54 13C29 22-12 23-33 10Z" fill="#e4ccee"/><path d="M-28 9Q-41-2-24-6M10-14Q22-25 36-14" fill="none" stroke="#b39bc7" stroke-width="1.5"/>'
    for i,(x,y,scale) in enumerate([(792,199,.52),(833,180,.7),(880,164,.82)]):
        delay=-i*2
        attr=f'class="motion-smoke" style="--delay:{delay}s"'
        if snapshot is not None:
            phase=(snapshot-delay)%6/6
            attr=f'transform="translate({48*phase} {-15*phase}) scale({.85+.37*phase})" opacity="{.23*math.sin(math.pi*phase):.3f}"'
        result.append(f'<g transform="translate({x} {y}) scale({scale})"><g {attr} filter="url(#smoke-soft)">{cloud}</g></g>')
    return ''.join(result)+'</g>'


CAROUSEL_SPEED=35  # px per second


def carousel(source,snapshot=None):
    # Scroll the doubled icon strip from build.py by one strip width, forever.
    match=re.search(r'<g class="stack-strip" data-strip="(\d+)">',source)
    if not match:return source,''
    strip=int(match.group(1));duration=strip/CAROUSEL_SPEED
    if snapshot is not None:
        offset=-strip*(snapshot%duration)/duration
        return source.replace(match.group(0),f'<g transform="translate({offset:.3f} 0)">'),''
    css=(f'.motion-carousel {{animation:stack-scroll {duration:.2f}s linear infinite;}}'
         f'@keyframes stack-scroll {{to {{transform:translateX(-{strip}px);}}}}'
         '@media (prefers-reduced-motion: reduce) {.motion-carousel{animation:none!important;}}')
    return source.replace(match.group(0),'<g class="stack-strip motion-carousel">'),css


def animated(name,static_svg,snapshot=None):
    """static_svg: the build.py output for this section; snapshot: freeze at t seconds."""
    source=stripes(static_svg,snapshot)
    source,extra_css=carousel(source,snapshot)
    overlay=trace(name,snapshot)
    if name=='intro':overlay+=petals(snapshot)+headlights(snapshot)
    if name=='footer':overlay+=smoke(snapshot)+rear_lights(snapshot)
    style='<style>'+CSS+extra_css+'</style>' if snapshot is None else ''
    return source.rsplit('</svg>',1)[0]+style+overlay+'</svg>\n'
