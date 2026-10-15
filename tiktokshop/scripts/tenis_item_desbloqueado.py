"""Vestido tubinho (plano aberto) — rebobinar VHS + checklist "fit check"
(base: edição dinâmica: câmera lenta, aceleração com rastro, revelação das costas,
tela dividida em 3 e zooms acompanhando o movimento. Frames RGB no stdout; eventos de som em dyn_sfx.json."""
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
import os, sys, math, re, json, random

V = os.path.dirname(os.path.abspath(__file__)); S = os.path.dirname(V)
W, H, FPS = 1080, 1920, 30
NSRC = 300
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
TILES = [(245, 190, 200), (170, 170, 178), (255, 255, 255), (230, 120, 150), (60, 60, 70)]
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




RANSOM = [_ransom("ACHADINHO", s_, 1150, maxw=960) for s_ in (101, 102, 103)]
PINK = (240, 120, 160)
# ---------- partículas: pó de fada ----------
def star(d, x, y, r, a, col=(255, 240, 248)):
    if r < 1 or a <= 0: return
    c = col + (int(a),)
    d.polygon([(x, y - r), (x + r * .22, y - r * .22), (x + r, y), (x + r * .22, y + r * .22), (x, y + r), (x - r * .22, y + r * .22), (x - r, y), (x - r * .22, y - r * .22)], fill=c)
    d.ellipse((x - r * .25, y - r * .25, x + r * .25, y + r * .25), fill=(255, 255, 255, int(a)))
_pr = random.Random(7)
AMBIENT = [(_pr.uniform(0, W), _pr.uniform(0, H), _pr.uniform(10, 24), _pr.uniform(0, 6.28), _pr.uniform(20, 60)) for _ in range(34)]
BURSTS = []   # (t0, x, y)
def particles(img, t):
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for x, y, r, ph, sp in AMBIENT:  # brilhinhos flutuando
        yy = (y - sp * t) % H; xx = x + 20 * math.sin(t * 1.3 + ph)
        a = 120 + 120 * math.sin(t * 4 + ph); star(d, xx, yy, r * (0.6 + 0.4 * math.sin(t * 3 + ph)), max(0, a))
    for t0, bx, by in BURSTS:  # explosões de brilho nas trocas
        lt = t - t0
        if 0 <= lt < 0.9:
            rr = random.Random(int(t0 * 100))
            for k in range(26):
                ang = rr.uniform(0, 6.28); spd = rr.uniform(250, 700); x = bx + math.cos(ang) * spd * lt; y = by + math.sin(ang) * spd * lt + 300 * lt * lt
                star(d, x, y, rr.uniform(8, 22) * (1 - lt), 255 * (1 - lt / .9), (255, 236, 190) if k % 3 else (255, 255, 255))
    glow = lay.filter(ImageFilter.GaussianBlur(6)); img.alpha_composite(glow); img.alpha_composite(lay)


def caption(img, text, t0, t, y=250, size=66):
    if t < t0: return
    rich(img, text, W / 2, y, F(800, size), n=int((t - t0) * 24))



def shock(img, cx, cy, lt):
    """onda de impacto no chão quando o pé pisa"""
    if lt < 0 or lt > 0.6: return
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for j in range(3):
        p = (lt - j * 0.08) / 0.5
        if p <= 0 or p > 1: continue
        r = 80 + 420 * ease(p); a = int(230 * (1 - p))
        d.ellipse((cx - r, cy - r * .22, cx + r, cy + r * .22), outline=(255, 255, 255, a), width=10)
        d.ellipse((cx - r - 6, cy - r * .22 - 3, cx + r + 6, cy + r * .22 + 3), outline=PINK + (a // 2,), width=6)
    img.alpha_composite(lay.filter(ImageFilter.GaussianBlur(2)))

def plat_bracket(img, x0, x1, y0, y1, lt, label):
    """chave lateral marcando a altura da plataforma"""
    k = ease(lt / 0.35); d = ImageDraw.Draw(img); xm = x1 + 40
    yt = lerp((y0 + y1) / 2, y0, k); yb = lerp((y0 + y1) / 2, y1, k)
    for w, c in ((14, (0, 0, 0, 90)), (8, (255, 255, 255, 255))):
        d.line((xm, yt, xm, yb), fill=c, width=w); d.line((xm - 26, yt, xm + 6, yt), fill=c, width=w); d.line((xm - 26, yb, xm + 6, yb), fill=c, width=w)
    if k > .9:
        pill(img, label, xm - 60, int(y0 - 210), 46); dd = ImageDraw.Draw(img); dd.line((xm, y0 - 120, xm, yt), fill="white", width=6)

# CTA: pegadas caminhando até o link
FOOT = [(840, 520), (760, 720), (680, 900), (560, 1080), (430, 1250), (300, 1420)]
def footprint(lay, x, y, ang, left, a):
    d = ImageDraw.Draw(lay); s = 1.0
    shoe = Image.new("RGBA", (130, 230), (0, 0, 0, 0)); ds = ImageDraw.Draw(shoe)
    ds.polygon([(30, 30), (65, 6), (100, 30), (112, 95), (98, 140), (92, 175), (95, 210), (65, 224), (36, 210), (40, 175), (34, 140), (20, 95)],
               fill=PINK + (a,), outline=(255, 255, 255, a), width=7)
    shoe = shoe.rotate(-math.degrees(ang) - 90 + (8 if left else -8), resample=Image.BICUBIC, expand=True)
    off = 46 if left else -46; nx, ny = -math.sin(ang) * off, math.cos(ang) * off
    lay.alpha_composite(shoe, (int(x + nx - shoe.width / 2), int(y + ny - shoe.height / 2)))
def cta_steps(img, t0):
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0)); pts = FOOT; n = len(pts)
    for i in range(1, n):
        ti = i * 0.22
        if t0 < ti: break
        a = int(255 * min(1, (t0 - ti) / .1)); x0, y0 = pts[i - 1]; x1, y1 = pts[i]; ang = math.atan2(y1 - y0, x1 - x0)
        footprint(lay, x1, y1, ang, i % 2 == 0, a)
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0)); sh.putalpha(lay.getchannel("A").point(lambda v: v * .5))
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(6)), (4, 6)); img.alpha_composite(lay)
    if t0 > n * 0.22:  # brilho em cima do link
        lt = t0 - n * .22; d = ImageDraw.Draw(img); pulse = .5 + .5 * math.sin(lt * 7)
        for k in range(10):
            ang = k / 10 * 6.28 + lt; r = 70 + 30 * pulse
            star(d, 250 + math.cos(ang) * r, 1460 + math.sin(ang) * r * .45, 9 + 6 * pulse, 230)


CYAN = (60, 230, 255); GOLD = (255, 200, 60)
MONO = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 58)
def scan(img, lt, y0=900, y1=1500):
    """linha de scanner holográfico varrendo o tênis + grade"""
    p = (lt % 1.1) / 1.1; y = lerp(y0, y1, p)
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rectangle((60, y0, W - 60, y), fill=CYAN + (35,))
    for gy in range(int(y0), int(y), 30): d.line((60, gy, W - 60, gy), fill=CYAN + (90,), width=3)
    for gx in range(60, W - 60, 30): d.line((gx, y0, gx, y), fill=CYAN + (70,), width=3)
    d.rectangle((60, y - 4, W - 60, y + 4), fill=CYAN + (255,))
    img.alpha_composite(lay.filter(ImageFilter.GaussianBlur(1)))
    g = Image.new("RGBA", img.size, (0, 0, 0, 0)); ImageDraw.Draw(g).rectangle((60, y - 30, W - 60, y + 30), fill=CYAN + (110,))
    img.alpha_composite(g.filter(ImageFilter.GaussianBlur(18)))
    d2 = ImageDraw.Draw(img); pct = min(100, int(lt / 2.2 * 100))
    d2.text((90, y0 - 110), f"ESCANEANDO… {pct}%", font=MONO, fill=CYAN, stroke_width=4, stroke_fill="black")
def banner(img, lt, text="NOVO ITEM DESBLOQUEADO"):
    k = ease(lt / .25); y = int(lerp(-160, 170, k))
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle((60, y, W - 60, y + 130), 26, fill=(20, 16, 40, 235), outline=GOLD + (255,), width=6)
    f = F(900, 50); tw = f.getlength(text); d.text(((W - tw) / 2, y + 16), text, font=f, fill=GOLD)
    rich(lay, "👟 raridade: lendária", W / 2, y + 74, F(700, 34), stroke=0)
    g = lay.filter(ImageFilter.GaussianBlur(12)); img.alpha_composite(g); img.alpha_composite(lay)
STATS = [("estilo", 5), ("combina com tudo", 5), ("plataforma", 4), ("vibe casual", 5)]
def stats(img, lt):
    k = ease(lt / .3); x0 = int(lerp(-560, 60, k)); y0 = 330; w = 560; h = 90 + 92 * len(STATS)
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle((x0, y0, x0 + w, y0 + h), 26, fill=(20, 16, 40, 225), outline=CYAN + (255,), width=5)
    d.text((x0 + 30, y0 + 20), "ATRIBUTOS", font=F(900, 40), fill=CYAN)
    for i, (name, lvl) in enumerate(STATS):
        yy = y0 + 86 + i * 92; d.text((x0 + 30, yy), name, font=F(700, 34), fill=(255, 255, 255))
        for b in range(5):
            on = lt > 0.5 + i * 0.35 + b * 0.06 and b < lvl
            bx = x0 + 30 + b * 64; d.rectangle((bx, yy + 46, bx + 54, yy + 70), fill=(GOLD if on else (70, 70, 90)) + (255,))
    img.alpha_composite(lay)
def pixel_arrow(img, t0):
    """seta pixelada estilo videogame quicando até o link"""
    px = 26; shape = ["....##....", "....##....", "....##....", "....##....", "....##....", "##########", ".########.", "..######..", "...####...", "....##...."]
    bob = 22 * abs(math.sin(math.pi * 1.8 * t0)); k = ease(t0 / .3)
    cx, cy = 260, int(lerp(900, 1300, k) + bob)
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for r, row in enumerate(shape):
        for c, ch in enumerate(row):
            if ch == "#":
                x = cx - 5 * px + c * px; y = cy - 10 * px + r * px
                d.rectangle((x, y, x + px - 1, y + px - 1), fill=GOLD + (255,), outline=(120, 70, 0, 255))
    g = lay.filter(ImageFilter.GaussianBlur(10)); img.alpha_composite(g); img.alpha_composite(lay)
    d2 = ImageDraw.Draw(img)
    if t0 > .3:
        for i in range(8):
            ang = i / 8 * 6.28 + t0 * 2; r = 120 + 15 * math.sin(t0 * 6)
            star(d2, 260 + math.cos(ang) * r, 1450 + math.sin(ang) * r * .4, 16, 240, (255, 230, 140))

SEGS = []
def seg(d, fn): SEGS.append((d, fn))
def A(lt):
    img = fr(lt * 0.6).convert("RGBA"); base = RANSOM[int(lt * 6) % 3]; k = min(1.0, lt / .18)
    if k < 1:
        sc = 0.6 + 0.5 * k if k < .8 else 1.1 - .5 * (k - .8); r = base.resize((int(W * sc), int(H * sc)), Image.LANCZOS); cx, cy = W / 2, 1230
        if sc <= 1: img.alpha_composite(r, (int(cx - cx * sc), int(cy - cy * sc)))
        else: img.alpha_composite(r, (0, 0), (int(cx * sc - cx), int(cy * sc - cy)))
    else: img.alpha_composite(base)
    rich(img, "o tênis que eu tava procurando 👟", W / 2, 1380, F(800, 56), n=int(max(0, lt - .2) * 26)); return img
seg(2.2, A)
def B(lt): return blurred(1.3 + lt * 2.0, 2).convert("RGBA")
seg(0.8, B)
def C(lt):
    img = fr(3.3 + lt * 0.35).convert("RGBA")
    if lt < 2.2: scan(img, lt, 980, 1460)
    else: banner(img, lt - 2.2)
    return img
seg(3.0, C)
def Dd(lt):
    img = fr(5.4 + lt * 0.8).convert("RGBA"); banner(img, 1.0); stats(img, lt); return img
seg(3.0, Dd)
def E(lt):
    img = fr(min(9.95, 8.4 + lt * .65)).convert("RGBA")
    if lt > 0.15: pixel_arrow(img, lt - .15)
    return img
seg(2.5, E)

TOTAL = sum(d for d, _ in SEGS); STARTS = []; a = 0
for d, _ in SEGS: STARTS.append(a); a += d
out = sys.stdout.buffer
for f in range(int(TOTAL * FPS)):
    t = f / FPS; i = max(k for k, s in enumerate(STARTS) if t >= s - 1e-6); lt = t - STARTS[i]
    img = SEGS[i][1](lt)
    if i > 0 and lt < .12: img = zoom(img.convert("RGB"), 1 + .05 * (1 - lt / .12)).convert("RGBA")
    if i == 2 and 2.2 <= lt < 2.3: img.alpha_composite(Image.new("RGBA", img.size, (255, 255, 255, int(220 * (1 - (lt - 2.2) / .1)))))
    if i in (0, 4): particles(img, t)
    out.write(img.convert("RGB").tobytes())
json.dump({"total": TOTAL, "starts": STARTS}, open(os.path.join(V, "t2.json"), "w"))
