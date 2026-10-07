"""Vestido tubinho (plano aberto) — rebobinar VHS + checklist "fit check"
(base: edição dinâmica: câmera lenta, aceleração com rastro, revelação das costas,
tela dividida em 3 e zooms acompanhando o movimento. Frames RGB no stdout; eventos de som em dyn_sfx.json."""
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
import os, sys, math, re, json, random

V = os.path.dirname(os.path.abspath(__file__)); S = os.path.dirname(V)
W, H, FPS = 1080, 1920, 30
NSRC = 271
_c = {}
def fr(t):
    i = min(NSRC, max(1, int(round(t * 30)) + 1))
    if i not in _c:
        if len(_c) > 60: _c.clear()
        _c[i] = Image.open(os.path.join(V, "src/%04d.jpg" % i)).convert("RGB")
    return _c[i]
def blurred(t, speed):
    """rastro de movimento: mistura quadros vizinhos quando acelerado"""
    if speed < 1.6: return fr(t)
    a, b, c = fr(t - 1 / 30), fr(t), fr(t + 1 / 30)
    return Image.blend(Image.blend(a, c, .5), b, .45)
def zoom(img, z, fx=.5, fy=.5):
    if z <= 1.001: return img
    cw, ch = W / z, H / z; cx = min(max(fx * W, cw / 2), W - cw / 2); cy = min(max(fy * H, ch / 2), H - ch / 2)
    return img.crop((int(cx - cw / 2), int(cy - ch / 2), int(cx + cw / 2), int(cy + ch / 2))).resize((W, H), Image.BILINEAR)
def ease(p): p = min(1.0, max(0.0, p)); return p * p * (3 - 2 * p)
def lerp(a, b, p): return a + (b - a) * p

F = lambda w, s: ImageFont.truetype(os.path.join(S, f"mont{w}.ttf"), s)
EMO = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf", 109)
EMO_RE = re.compile(r"([\U0001F300-\U0001FAFF☀-➿\U0001F5A4]️?)")
_ec = {}
def emoji(ch, size):
    if (ch, size) not in _ec:
        im = Image.new("RGBA", (160, 160), (0, 0, 0, 0)); ImageDraw.Draw(im).text((10, 10), ch, font=EMO, embedded_color=True)
        im = im.crop(im.getbbox()); _ec[(ch, size)] = im.resize((max(1, int(im.width * size / im.height)), size), Image.LANCZOS)
    return _ec[(ch, size)]
def rich(img, text, x, y, font, fill="white", stroke=6, sfill="black", n=None):
    parts = [p for p in EMO_RE.split(text) if p]; asc, desc = font.getmetrics(); es = int(asc * .95)
    wid = sum(emoji(p, es).width if EMO_RE.fullmatch(p) else font.getlength(p) for p in parts)
    cx = x - wid / 2; d = ImageDraw.Draw(img); left = 10 ** 6 if n is None else n
    for p in parts:
        if left <= 0: break
        if EMO_RE.fullmatch(p):
            img.alpha_composite(emoji(p, es), (int(cx), int(y + (asc - es) / 2 + 4))); cx += emoji(p, es).width; left -= 1
        else:
            q = p[:left]; left -= len(p); d.text((cx, y), q, font=font, fill=fill, stroke_width=stroke, stroke_fill=sfill); cx += font.getlength(p)
    return wid
def pill(img, text, cx, y, size=50):
    font = F(800, size); lay = Image.new("RGBA", img.size, (0, 0, 0, 0)); tw = rich(Image.new("RGBA", (4, 4)), text, 0, 0, font)
    ImageDraw.Draw(lay).rounded_rectangle((cx - tw / 2 - 30, y, cx + tw / 2 + 30, y + size + 34), 40, fill=(255, 255, 255, 240))
    rich(lay, text, cx, y + 14, font, fill=(20, 20, 20), stroke=0); img.alpha_composite(lay)
def pop_text(img, text, t0, t, y=820, size=110):
    k = ease((t - t0) / 0.18)
    if k <= 0: return
    lay = Image.new("RGBA", (W, 400), (0, 0, 0, 0)); rich(lay, text, W / 2, 120, F(900, size), stroke=10)
    s = 1.6 - 0.6 * k; lay = lay.resize((int(W * s), int(400 * s)), Image.BILINEAR).rotate(-4, resample=Image.BICUBIC)
    img.alpha_composite(lay, (int((W - lay.width) / 2), int(y - lay.height / 2)))

# rabisco (seta com laço + coração) — CTA
def catmull(pts, n=24):
    out = []; P = [pts[0]] + pts + [pts[-1]]
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(n):
            t = k / n; t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2 + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in (0, 1)))
    return out + [pts[-1]]
_r = random.Random(3)
PATH = [(x + _r.uniform(-3, 3), y + _r.uniform(-3, 3)) for x, y in catmull([(760, 1120), (640, 1215), (520, 1250), (440, 1210), (430, 1130), (500, 1085), (575, 1130), (570, 1230), (480, 1340), (345, 1425), (220, 1482)])]
def stroke(d, pts, w, c):
    if len(pts) > 1: d.line(pts, fill=c, width=w, joint="curve")
    for x, y in (pts[0], pts[-1]): d.ellipse((x - w / 2, y - w / 2, x + w / 2, y + w / 2), fill=c)
def heart(cx, cy, s):
    return [(cx + 16 * math.sin(a) ** 3 * s, cy - (13 * math.cos(a) - 5 * math.cos(2 * a) - 2 * math.cos(3 * a) - math.cos(4 * a)) * s) for a in [2 * math.pi * k / 59 for k in range(60)]]
def cta(img, t0):
    k = 1 - (1 - min(1.0, t0 / 0.9)) ** 2; items = [PATH[:max(2, int(len(PATH) * k))]]
    if k >= 1:
        tip = PATH[-1]; prev = PATH[-6]; a = math.atan2(tip[1] - prev[1], tip[0] - prev[0])
        items.append([(tip[0] - 70 * math.cos(a - .55), tip[1] - 70 * math.sin(a - .55)), tip, (tip[0] - 70 * math.cos(a + .55), tip[1] - 70 * math.sin(a + .55))])
        hp = heart(780, 1290, 3.4); items.append(hp[:max(2, int(len(hp) * min(1, (t0 - .9) / .5)))])
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0)); ds = ImageDraw.Draw(sh)
    for it in items: stroke(ds, [(x + 4, y + 6) for x, y in it], 26, (0, 0, 0, 80))
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(4))); d = ImageDraw.Draw(img)
    for it in items: stroke(d, it, 24, (60, 60, 60))
    for it in items: stroke(d, it, 13, (255, 255, 255))


# plaquinhas (letras recortadas) do hook
SERIFS = ["/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf", "/usr/share/fonts/truetype/liberation/LiberationSerif-BoldItalic.ttf",
          "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"]
TILES = [(18, 18, 18), (214, 172, 92), (236, 205, 200), (245, 240, 232), (120, 90, 60)]
def _tile(ch, rnd, h=150):
    font = ImageFont.truetype(rnd.choice(SERIFS), int(h * rnd.uniform(.80, .95))); bg = rnd.choice(TILES)
    fg = rnd.choice([(255, 255, 255), (245, 225, 180)]) if sum(bg) < 520 else rnd.choice([(18, 18, 18), (90, 60, 30)])
    w = int(font.getlength(ch)) + rnd.randint(12, 24); hh = h + rnd.randint(-14, 10)
    im = Image.new("RGBA", (w + 20, hh + 20), (0, 0, 0, 0)); d = ImageDraw.Draw(im); j = lambda: rnd.randint(-5, 5)
    d.polygon([(10 + j(), 10 + j()), (w + 10 + j(), 10 + j()), (w + 10 + j(), hh + 10 + j()), (10 + j(), hh + 10 + j())], fill=bg + (255,))
    if rnd.random() < .35:
        for gx in range(10, w + 10, 12): d.line((gx, 10, gx, hh + 10), fill=(255, 255, 255, 60), width=4)
        for gy in range(10, hh + 10, 12): d.line((10, gy, w + 10, gy), fill=(255, 255, 255, 60), width=4)
    d.text(((w + 20) / 2, (hh + 20) / 2), ch, font=font, fill=fg, anchor="mm")
    im = im.rotate(rnd.uniform(-8, 8), resample=Image.BICUBIC, expand=True)
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); sh.putalpha(im.getchannel("A").point(lambda a: a * .45))
    out = Image.new("RGBA", (im.width + 8, im.height + 8), (0, 0, 0, 0))
    out.alpha_composite(sh.filter(ImageFilter.GaussianBlur(4)), (6, 6)); out.alpha_composite(im, (0, 0)); return out
def _ransom(text, seed, y, maxw=960):
    rnd = random.Random(seed); tiles = [None if c == " " else _tile(c, rnd) for c in text]
    gap, sp = -16, 60; total = sum(sp if t is None else t.width + gap for t in tiles); sc = min(1.7, maxw / total)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0)); x = (W - total * sc) / 2
    for t in tiles:
        if t is None: x += sp * sc; continue
        t2 = t.resize((int(t.width * sc), int(t.height * sc)), Image.LANCZOS)
        layer.alpha_composite(t2, (int(x), int(y + rnd.randint(-8, 8)))); x += (t.width + gap) * sc
    return layer
RANSOM = [_ransom("ESPERA", s_, 1080) for s_ in (41, 42, 43)]


RANSOM = [_ransom("OLHA", s_, 1170, maxw=760) for s_ in (51, 52, 53)]

def vhs(img, t, strength=1.0):
    """efeito fita VHS: canais deslocados, linhas, faixa de ruído e marcação ◀◀"""
    r, g, b = img.convert("RGB").split(); off = int(10 * strength)
    r = ImageChops.offset(r, off, 0); b = ImageChops.offset(b, -off, 0)
    im = Image.merge("RGB", (r, g, b)).convert("RGBA")
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for y in range(0, H, 6): d.line((0, y, W, y), fill=(0, 0, 0, 55))
    by = int((t * 1400) % H); d.rectangle((0, by, W, by + 60), fill=(255, 255, 255, 40))
    rnd = random.Random(int(t * 30))
    for _ in range(40):
        x = rnd.randint(0, W); y = rnd.randint(by, by + 60); d.line((x, y, x + rnd.randint(20, 120), y), fill=(255, 255, 255, 90), width=2)
    im.alpha_composite(lay)
    mono = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 64)
    d2 = ImageDraw.Draw(im)
    d2.text((70, 140), "◀◀ REBOBINANDO", font=mono, fill="white", stroke_width=4, stroke_fill="black")
    d2.text((W - 330, 230), "00:0%d:%02d" % (int(t) % 10, int(t * 30) % 60), font=mono, fill="white", stroke_width=4, stroke_fill="black")
    return im

# cartão "fit check" com checklist
ITEMS = ["gola alta", "costas nuas", "justinho", "tecido suplex"]
def check_mark(d, x, y, k, s=1.0):
    pts = [(x, y + 18 * s), (x + 16 * s, y + 36 * s), (x + 48 * s, y - 4 * s)]
    seg1 = min(1.0, k * 2); seg2 = max(0.0, k * 2 - 1)
    if seg1 > 0: d.line((pts[0], (pts[0][0] + (pts[1][0] - pts[0][0]) * seg1, pts[0][1] + (pts[1][1] - pts[0][1]) * seg1)), fill=(40, 170, 90), width=int(9 * s))
    if seg2 > 0: d.line((pts[1], (pts[1][0] + (pts[2][0] - pts[1][0]) * seg2, pts[1][1] + (pts[2][1] - pts[1][1]) * seg2)), fill=(40, 170, 90), width=int(9 * s))
def checklist(img, lt):
    k = ease(lt / 0.3); x0 = int(lerp(-460, 36, k)); y0 = 230; w, h = 400, 120 + 92 * len(ITEMS)
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle((x0 + 6, y0 + 10, x0 + w + 6, y0 + h + 10), 30, fill=(0, 0, 0, 70))
    d.rounded_rectangle((x0, y0, x0 + w, y0 + h), 30, fill=(255, 255, 255, 240))
    rich(lay, "fit check ✅", x0 + w / 2, y0 + 22, F(900, 50), fill=(20, 20, 20), stroke=0)
    for i, it in enumerate(ITEMS):
        yy = y0 + 110 + i * 92; ti = 0.45 + i * 0.4
        d.rounded_rectangle((x0 + 26, yy, x0 + 76, yy + 50), 10, outline=(40, 40, 40), width=4)
        d.text((x0 + 96, yy + 4), it, font=F(700, 40), fill=(30, 30, 30))
        if lt > ti: check_mark(d, x0 + 30, yy + 4, min(1.0, (lt - ti) / 0.25))
    img.alpha_composite(lay)

SEGS = []
def seg(dur, fn): SEGS.append((dur, fn))
def A(lt):  # hook com plaquinhas
    img = zoom(fr(lt), 1.12, .5, .45).convert("RGBA")
    base = RANSOM[int(lt * 6) % 3]; k = min(1.0, lt / 0.18)
    if k < 1:
        sc = 0.6 + 0.5 * k if k < .8 else 1.1 - .5 * (k - .8); r = base.resize((int(W * sc), int(H * sc)), Image.LANCZOS); cx, cy = W / 2, 1300
        if sc <= 1: img.alpha_composite(r, (int(cx - cx * sc), int(cy - cy * sc)))
        else: img.alpha_composite(r, (0, 0), (int(cx * sc - cx), int(cy * sc - cy)))
    else: img.alpha_composite(base)
    rich(img, "quando ela virar 👀", W / 2, 1420, F(800, 70), n=int(max(0, lt - .15) * 22)); return img
seg(2.0, A)
def B(lt):  # vai até as costas, acelerado
    st = 2.0 + lt * 1.5; return zoom(blurred(st, 1.5), 1.12, .5, .45).convert("RGBA")
seg(2.0, B)
def C(lt):  # REBOBINA: volta rápido com efeito VHS
    st = 5.0 - (5.0 - 3.3) * ease(lt / 0.9); return vhs(zoom(fr(st), 1.12, .5, .45), lt)
seg(0.9, C)
def Dr(lt):  # repete a revelação em câmera lenta com zoom nas costas
    st = 3.3 + lt * 0.75; img = zoom(fr(st), lerp(1.12, 1.7, ease(lt / 1.2)), .52, .42).convert("RGBA")
    if lt < 0.1: img.alpha_composite(Image.new("RGBA", img.size, (255, 255, 255, int(220 * (1 - lt / .1)))))
    pop_text(img, "COSTAS NUAS 🔥", 0.5, lt, y=1330); return img
seg(2.2, Dr)
def E(lt):  # volta de frente + checklist marcando
    st = 5.2 + lt * 1.0; img = zoom(fr(st), 1.12, .5, .45).convert("RGBA"); checklist(img, lt); return img
seg(2.4, E)
def Fn(lt):  # vem andando e aponta + CTA
    st = min(9.0, 7.6 + lt * 0.9); img = zoom(fr(st), 1.12, .5, .45).convert("RGBA")
    if lt > 0.3: cta(img, lt - 0.3)
    return img
seg(2.2, Fn)

TOTAL = sum(d for d, _ in SEGS); starts = []; a = 0
for d, _ in SEGS: starts.append(a); a += d
out = sys.stdout.buffer
for f in range(int(TOTAL * FPS)):
    t = f / FPS; i = max(k for k, s in enumerate(starts) if t >= s - 1e-6); lt = t - starts[i]
    img = SEGS[i][1](lt)
    if i > 0 and lt < 0.12: img = zoom(img.convert("RGB"), 1 + 0.06 * (1 - lt / 0.12)).convert("RGBA")
    out.write(img.convert("RGB").tobytes())
json.dump({"total": TOTAL, "starts": starts}, open(os.path.join(V, "chk_sfx.json"), "w"))
