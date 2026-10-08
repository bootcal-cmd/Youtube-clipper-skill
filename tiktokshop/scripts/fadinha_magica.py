"""Vestido tubinho (plano aberto) — rebobinar VHS + checklist "fit check"
(base: edição dinâmica: câmera lenta, aceleração com rastro, revelação das costas,
tela dividida em 3 e zooms acompanhando o movimento. Frames RGB no stdout; eventos de som em dyn_sfx.json."""
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
import os, sys, math, re, json, random

V = os.path.dirname(os.path.abspath(__file__)); S = os.path.dirname(V)
W, H, FPS = 1080, 1920, 30
NSRC = 264
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
TILES = [(150, 110, 70), (214, 172, 92), (60, 40, 30), (205, 140, 150), (20, 20, 20)]
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



RANSOM = [_ransom("FADINHA", s_, 1180, maxw=900) for s_ in (61, 62, 63)]

# ---------- clima de sonho ----------
def dreamy(img):
    from PIL import ImageEnhance
    im = ImageEnhance.Color(img).enhance(1.06)
    r, g, b = im.split(); r = r.point(lambda v: min(255, int(v * 1.04 + 4))); b = b.point(lambda v: int(v * 0.96))
    im = Image.merge("RGB", (r, g, b))
    small = im.resize((W // 4, H // 4), Image.BILINEAR)
    hi = small.point(lambda v: 0 if v < 190 else min(255, (v - 190) * 4)).filter(ImageFilter.GaussianBlur(10)).resize((W, H), Image.BILINEAR)
    im = ImageChops.screen(im, Image.eval(hi, lambda v: int(v * 0.45)))
    return im

VIG = None
def vignette(img):
    global VIG
    if VIG is None:
        m = Image.new("L", (W // 8, H // 8), 0); ImageDraw.Draw(m).ellipse((-30, -20, W // 8 + 30, H // 8 + 20), fill=255)
        m = m.filter(ImageFilter.GaussianBlur(14)).resize((W, H), Image.BILINEAR)
        VIG = Image.new("RGBA", (W, H), (30, 15, 5, 255)); VIG.putalpha(Image.eval(m, lambda v: int((255 - v) * 0.45)))
    img.alpha_composite(VIG)

# ---------- partículas: pó de fada ----------
def star(d, x, y, r, a, col=(255, 248, 225)):
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

def wand_wipe(a_img, b_img, p):
    """varinha: linha diagonal de brilho revelando a próxima cena"""
    x = int(lerp(-300, W + 300, ease(p)))
    m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).polygon([(0, 0), (x + 200, 0), (x - 200, H), (0, H)], fill=255)
    out = Image.composite(b_img.convert("RGB"), a_img.convert("RGB"), m).convert("RGBA")
    lay = Image.new("RGBA", out.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.line((x + 200, 0, x - 200, H), fill=(255, 245, 220, 230), width=10)
    rr = random.Random(int(p * 50))
    for k in range(40):
        q = rr.random(); px = lerp(x + 200, x - 200, q) + rr.uniform(-40, 40); py = q * H
        star(d, px, py, rr.uniform(6, 20), 255)
    out.alpha_composite(lay.filter(ImageFilter.GaussianBlur(5))); out.alpha_composite(lay); return out

# ---------- CTA: rastro de pó de fada até o link ----------
TRAIL = catmull([(980, 760), (820, 900), (880, 1080), (640, 1180), (440, 1300), (260, 1440)], 30)
def fairy_cta(img, t0):
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    p = min(1.0, t0 / 1.1); n = int(len(TRAIL) * ease(p)); rr = random.Random(5)
    for i in range(max(0, n - 70), n):  # rastro que vai sumindo
        x, y = TRAIL[i]; age = (n - i) / 70
        star(d, x + rr.uniform(-14, 14), y + rr.uniform(-14, 14), 14 * (1 - age) + 3, 255 * (1 - age))
    if n > 0:
        hx, hy = TRAIL[n - 1]; star(d, hx, hy, 34, 255, (255, 255, 255))
    if p >= 1:  # estouro de brilho em cima do link + brilho pulsando
        lt = t0 - 1.1; pulse = 0.5 + 0.5 * math.sin(lt * 7)
        for k in range(14):
            ang = k / 14 * 6.28 + lt; r = 60 + 40 * pulse
            star(d, 260 + math.cos(ang) * r, 1440 + math.sin(ang) * r * .5, 10 + 6 * pulse, 230)
        star(d, 260, 1440, 30 + 10 * pulse, 255, (255, 255, 255))
    img.alpha_composite(lay.filter(ImageFilter.GaussianBlur(7))); img.alpha_composite(lay)

def caption(img, text, t0, t, y=250, size=66):
    if t < t0: return
    rich(img, text, W / 2, y, F(800, size), n=int((t - t0) * 24))

# ---------- linha do tempo ----------
SEGS = []
def seg(dur, fn): SEGS.append((dur, fn))
def A(lt):  # hook: close em câmera lenta + plaquinhas
    img = dreamy(fr(lt * 0.5)).convert("RGBA"); vignette(img)
    base = RANSOM[int(lt * 6) % 3]; k = min(1.0, lt / 0.18)
    if k < 1:
        sc = 0.6 + 0.5 * k if k < .8 else 1.1 - .5 * (k - .8); r = base.resize((int(W * sc), int(H * sc)), Image.LANCZOS); cx, cy = W / 2, 1260
        if sc <= 1: img.alpha_composite(r, (int(cx - cx * sc), int(cy - cy * sc)))
        else: img.alpha_composite(r, (0, 0), (int(cx * sc - cx), int(cy * sc - cy)))
    else: img.alpha_composite(base)
    rich(img, "parece vestido, né? 🤭", W / 2, 1400, F(800, 66), n=int(max(0, lt - .2) * 22)); return img
seg(2.2, A)
def B(lt):  # gira: "mas é macaquinho"
    img = dreamy(fr(1.1 + lt * 1.2)).convert("RGBA"); vignette(img); caption(img, "mas é macaquinho 😌", 0.1, lt); return img
seg(1.8, B)
def Cw(lt):  # varinha revelando as costas
    a_ = dreamy(fr(1.1 + (1.8 + lt) * 1.2)); b_ = dreamy(zoom(fr(3.3), 1.15, .52, .5)); img = wand_wipe(a_, b_, lt / 0.5); vignette(img); return img
seg(0.5, Cw)
def C(lt):  # costas em câmera lenta + zoom
    img = dreamy(zoom(fr(3.3 + lt * 0.55), lerp(1.15, 1.45, ease(lt / 2.0)), .52, .5)).convert("RGBA"); vignette(img)
    pop_text(img, "costas nuas com laço 🎀", 0.3, lt, y=1420, size=62); return img
seg(2.0, C)
def D(lt):  # volta de frente, saia rodando
    img = dreamy(fr(4.4 + lt * 1.0)).convert("RGBA"); vignette(img)
    caption(img, "rodadinho e fresquinho ✨", 0.15, lt); return img
seg(2.4, D)
def E(lt):  # joinha + CTA
    img = dreamy(fr(min(8.8, 6.8 + lt * 0.9))).convert("RGBA"); vignette(img)
    caption(img, "pode sentar, dançar, ventar… 💃", 0.05, lt, size=58)
    if lt > 0.5: fairy_cta(img, lt - 0.5)
    return img
seg(2.6, E)

TOTAL = sum(d for d, _ in SEGS); starts = []; a = 0
for d, _ in SEGS: starts.append(a); a += d
BURSTS += [(starts[1], 540, 900), (starts[3], 560, 950), (starts[4], 540, 1000)]
out = sys.stdout.buffer
for f in range(int(TOTAL * FPS)):
    t = f / FPS; i = max(k for k, s in enumerate(starts) if t >= s - 1e-6); lt = t - starts[i]
    img = SEGS[i][1](lt)
    if i > 0 and lt < 0.12 and i != 3: img = zoom(img.convert("RGB"), 1 + 0.05 * (1 - lt / 0.12)).convert("RGBA")
    particles(img, t)
    out.write(img.convert("RGB").tobytes())
json.dump({"total": TOTAL, "starts": starts}, open(os.path.join(V, "fada_sfx.json"), "w"))
