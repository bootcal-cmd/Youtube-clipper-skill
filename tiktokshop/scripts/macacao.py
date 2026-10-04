"""5 edições do macacão de tule: hook em letras recortadas + máquina de escrever + 5 CTAs animados (sem texto).
uso: python3 macacao.py <n 1-5>  -> gera frames RGBA em mac_ov<n>/"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os, re, random, sys, math

S = os.path.dirname(os.path.abspath(__file__))
W, H, FPS = 1080, 1920, 30
N = int(sys.argv[1])
OUT = os.path.join(S, f"mac_ov{N}"); os.makedirs(OUT, exist_ok=True)
for f in os.listdir(OUT): os.remove(os.path.join(OUT, f))

SERIF_B = "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"
SERIF_BI = "/usr/share/fonts/truetype/liberation/LiberationSerif-BoldItalic.ttf"
DSERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
TYPE = ImageFont.truetype(os.path.join(S, "mont800.ttf"), 70)
TYPE_S = ImageFont.truetype(os.path.join(S, "mont800.ttf"), 58)
EMO = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf", 109)
EMO_RE = re.compile(r"([\U0001F300-\U0001FAFF☀-➿]️?)")
WINE = (122, 22, 44)
TILES = [(122, 22, 44), (168, 52, 76), (88, 14, 30), (238, 214, 214), (205, 140, 150)]

# ---------------- roteiros ----------------
# (palavra recortada, fim do hook, eventos [(ini, fim, linhas, fonte)], cta, início do cta, duração total)
CFG = {
    1: ("COMO ASSIM", 3.2, [(0.15, 3.2, ["esse macacão já vem", "com bojo?"], TYPE),
                            (3.4, 5.6, ["olha as costas 😍"], TYPE_S),
                            (5.7, 7.3, ["tule na medida certa ✨"], TYPE_S)], "doodle", 7.6, 10.6),
    2: ("SOCORRO", 2.5, [(0.15, 2.5, ["achei o look", "da balada 🔥"], TYPE),
                         (2.65, 4.5, ["ombro a ombro 🥹"], TYPE_S),
                         (4.6, 6.0, ["e a calça flare alonga demais ✨"], TYPE_S)], "emoji", 6.1, 8.6),
    3: ("CONFESSO", 2.9, [(0.15, 2.9, ["achei que ia ficar", "transparente demais..."], TYPE),
                          (3.0, 5.6, ["mas o tule é na", "medida certa 🙌"], TYPE_S)], "spot", 5.9, 8.6),
    4: ("GENTE", 2.3, [(0.15, 2.3, ["que macacão chique", "é esse? 🥹"], TYPE),
                       (2.45, 4.6, ["valoriza demais o corpo 🔥"], TYPE_S),
                       (4.75, 6.0, ["e já vem com bojo ✨"], TYPE_S)], "hearts", 6.1, 8.6),
    5: ("ESPERA", 3.0, [(0.15, 3.0, ["olha as costas desse", "macacão 😳"], TYPE),
                        (4.4, 6.2, ["de frente é mais lindo ainda 🥹"], TYPE_S)], "chevrons", 6.3, 8.6),
}
WORD, HOOK_END, EVENTS, CTA, CTA_T, TOTAL = CFG[N]

# ---------------- letras recortadas ----------------
def tile(ch, rnd, h=150):
    font = ImageFont.truetype(rnd.choice([SERIF_B, SERIF_BI, DSERIF]), int(h * rnd.uniform(.80, .95)))
    bg = rnd.choice(TILES)
    fg = rnd.choice([(255, 255, 255), (250, 232, 232)]) if sum(bg) < 520 else rnd.choice([WINE, (60, 8, 20)])
    w = int(font.getlength(ch)) + rnd.randint(12, 24); hh = h + rnd.randint(-14, 10)
    im = Image.new("RGBA", (w + 20, hh + 20), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    j = lambda: rnd.randint(-5, 5)
    d.polygon([(10 + j(), 10 + j()), (w + 10 + j(), 10 + j()), (w + 10 + j(), hh + 10 + j()), (10 + j(), hh + 10 + j())], fill=bg + (255,))
    if rnd.random() < .35:
        for gx in range(10, w + 10, 12): d.line((gx, 10, gx, hh + 10), fill=(255, 255, 255, 60), width=4)
        for gy in range(10, hh + 10, 12): d.line((10, gy, w + 10, gy), fill=(255, 255, 255, 60), width=4)
    d.text(((w + 20) / 2, (hh + 20) / 2), ch, font=font, fill=fg, anchor="mm")
    im = im.rotate(rnd.uniform(-8, 8), resample=Image.BICUBIC, expand=True)
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); sh.putalpha(im.getchannel("A").point(lambda a: a * .45))
    out = Image.new("RGBA", (im.width + 8, im.height + 8), (0, 0, 0, 0))
    out.alpha_composite(sh.filter(ImageFilter.GaussianBlur(4)), (6, 6)); out.alpha_composite(im, (0, 0))
    return out

def ransom(text, seed, y, maxw=1040):
    rnd = random.Random(seed)
    tiles = [None if c == " " else tile(c, rnd) for c in text]
    gap, sp = -16, 30
    total = sum(sp if t is None else t.width + gap for t in tiles)
    scale = min(1.0, maxw / total)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0)); x = (W - total * scale) / 2
    for t in tiles:
        if t is None: x += sp * scale; continue
        t2 = t.resize((int(t.width * scale), int(t.height * scale)), Image.LANCZOS)
        layer.alpha_composite(t2, (int(x), int(y + rnd.randint(-8, 8)))); x += (t.width + gap) * scale
    return layer
RANSOM = [ransom(WORD, s + N * 10, 170) for s in (7, 8, 9)]

# ---------------- máquina de escrever ----------------
_ecache = {}
def emoji(ch, size):
    if (ch, size) not in _ecache:
        im = Image.new("RGBA", (160, 160), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((10, 10), ch, font=EMO, embedded_color=True)
        im = im.crop(im.getbbox()); _ecache[(ch, size)] = im.resize((int(im.width * size / im.height), size), Image.LANCZOS)
    return _ecache[(ch, size)]

def typed(layer, lines, n_chars, y, font, cursor_on):
    d = ImageDraw.Draw(layer); asc, desc = font.getmetrics(); lh = asc + desc - 4
    left = n_chars; es = int(asc * .95)
    for li, line in enumerate(lines):
        if left <= 0 and li > 0: break
        parts = [p for p in EMO_RE.split(line) if p]
        shown, cnt = [], 0
        for p in parts:
            if EMO_RE.fullmatch(p):
                if cnt < left: shown.append(p); cnt += 1
            else:
                take = max(0, min(len(p), left - cnt)); shown.append(p[:take]); cnt += take
        left -= sum(1 if EMO_RE.fullmatch(p) else len(p) for p in parts)
        full_w = sum(emoji(p, es).width if EMO_RE.fullmatch(p) else font.getlength(p) for p in parts)
        x = (W - full_w) / 2; yy = y + li * lh
        for p in shown:
            if EMO_RE.fullmatch(p):
                e = emoji(p, es); layer.alpha_composite(e, (int(x), int(yy + (asc - es) / 2 + 6))); x += e.width
            elif p:
                d.text((x + 3, yy + 4), p, font=font, fill=(0, 0, 0, 110), stroke_width=4, stroke_fill=(0, 0, 0, 110))
                d.text((x, yy), p, font=font, fill="white", stroke_width=4, stroke_fill="black"); x += font.getlength(p)
        if (li == len(lines) - 1 or left <= 0) and cursor_on:
            d.rectangle((x + 6, yy + 6, x + 6 + int(asc * .42), yy + asc + desc - 6), fill="white", outline="black", width=3)
            break

# ---------------- utilidades de traço ----------------
def catmull(pts, n=24):
    out = []; P = [pts[0]] + pts + [pts[-1]]
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(n):
            t = k / n; t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2
                                    + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in (0, 1)))
    out.append(pts[-1]); return out
def stroke(d, pts, w, color):
    if len(pts) > 1: d.line(pts, fill=color, width=w, joint="curve")
    for x, y in (pts[0], pts[-1]): d.ellipse((x - w / 2, y - w / 2, x + w / 2, y + w / 2), fill=color)
def marker(layer, items, a=255):
    """traço de caneta branca com contorno vinho e sombra"""
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ds = ImageDraw.Draw(sh)
    for it in items: stroke(ds, [(x + 4, y + 6) for x, y in it], 26, (0, 0, 0, int(80 * a / 255)))
    layer.alpha_composite(sh.filter(ImageFilter.GaussianBlur(4)))
    d = ImageDraw.Draw(layer)
    for it in items: stroke(d, it, 24, WINE + (a,))
    for it in items: stroke(d, it, 13, (255, 255, 255, a))
def heart_pts(cx, cy, s, n=60):
    pts = []
    for k in range(n):
        a = 2 * math.pi * k / (n - 1)
        x = 16 * math.sin(a) ** 3; y = -(13 * math.cos(a) - 5 * math.cos(2 * a) - 2 * math.cos(3 * a) - math.cos(4 * a))
        pts.append((cx + x * s, cy + y * s))
    return pts
def sparkle(d, cx, cy, r, a):
    for dx, dy in ((r, 0), (0, r)):
        d.line((cx - dx, cy - dy, cx + dx, cy + dy), fill=WINE + (a,), width=12)
        d.line((cx - dx, cy - dy, cx + dx, cy + dy), fill=(255, 255, 255, a), width=6)

# O link da loja fica entre y≈1520 e y≈1740 (depende do texto embaixo), à esquerda (x≈35–840).
# Todos os CTAs terminam acima de y≈1500 para nunca cobrir o link.

# 1) seta rabiscada com laço + coração
_r = random.Random(3)
PATH = [(x + _r.uniform(-3, 3), y + _r.uniform(-3, 3)) for x, y in catmull(
    [(760, 1120), (640, 1215), (520, 1250), (440, 1210), (430, 1130), (500, 1085), (575, 1130), (570, 1230), (480, 1340), (345, 1425), (220, 1482)])]
def cta_doodle(layer, t0):
    DRAW = 0.9; k = 1 - (1 - min(1.0, t0 / DRAW)) ** 2
    items = [PATH[:max(2, int(len(PATH) * k))]]
    if k >= 1:
        nud = 7 * max(0, math.sin(2 * math.pi * 1.3 * (t0 - DRAW)))
        tip = (PATH[-1][0] - nud * .8, PATH[-1][1] + nud); prev = PATH[-6]
        ang = math.atan2(tip[1] - prev[1], tip[0] - prev[0]); L = 70
        items.append([(tip[0] - L * math.cos(ang - .55), tip[1] - L * math.sin(ang - .55)), tip,
                      (tip[0] - L * math.cos(ang + .55), tip[1] - L * math.sin(ang + .55))])
    hk = min(1.0, max(0.0, (t0 - DRAW - 0.1) / 0.5))
    if hk > 0:
        hp = heart_pts(780, 1290, 3.4); items.append(hp[:max(2, int(len(hp) * hk))])
    marker(layer, items)
    if t0 > DRAW + 0.3:
        d = ImageDraw.Draw(layer)
        for i, (cx, cy, r) in enumerate([(120, 1390, 24), (360, 1470, 16), (880, 1210, 20)]):
            a = 0.5 + 0.5 * math.sin(2 * math.pi * 1.1 * (t0 - DRAW) + i * 2.1)
            sparkle(d, cx, cy, r * (0.6 + 0.6 * a), int(255 * (0.4 + 0.6 * a)))

# 2) emojis 👇 batendo para baixo, alternados
def cta_emoji(layer, t0):
    for i, (x, y, sz) in enumerate([(60, 1290, 175), (260, 1320, 150)]):
        tt = t0 - i * 0.15
        if tt < 0: continue
        k = min(1.0, tt / 0.25)
        s = sz * (0.4 + 0.75 * k if k < .8 else 1.0 + .15 * (1 - k) / .2)  # pop
        bob = 28 * abs(math.sin(math.pi * 1.6 * tt + i * math.pi / 2))
        e = emoji("👇", max(10, int(s)))
        sh = Image.new("RGBA", e.size, (0, 0, 0, 0)); sh.putalpha(e.getchannel("A").point(lambda v: v * .35))
        layer.alpha_composite(sh.filter(ImageFilter.GaussianBlur(5)), (int(x + 6), int(y + bob + 10)))
        layer.alpha_composite(e, (int(x + (sz - e.width) / 2), int(y + bob + (sz - e.height))))

# 3) holofote: escurece levemente a tela e ilumina a área do link
_yy, _xx = None, None
def cta_spot(layer, t0):
    k = min(1.0, t0 / 0.5)
    pulse = 0.5 + 0.5 * math.sin(2 * math.pi * 0.9 * t0)
    m = Image.new("L", (W // 4, H // 4), 0); dm = ImageDraw.Draw(m)
    # elipse "clara" sobre a região do link (cobre as duas alturas possíveis)
    rx, ry = 520 / 4 * (1 + .05 * pulse), 260 / 4 * (1 + .05 * pulse); cx, cy = 400 / 4, 1625 / 4
    dm.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=255)
    m = m.filter(ImageFilter.GaussianBlur(28)).resize((W, H), Image.BILINEAR)
    dark = Image.new("RGBA", (W, H), (20, 0, 8, 255))
    dark.putalpha(Image.eval(m, lambda v: int((255 - v) / 255 * 165 * k)))
    layer.alpha_composite(dark)
    if t0 > 0.4:
        d = ImageDraw.Draw(layer)
        for i, (cx2, cy2, r) in enumerate([(70, 1460, 34), (880, 1480, 28), (480, 1430, 22), (950, 1780, 26), (640, 1460, 18)]):
            a = 0.5 + 0.5 * math.sin(2 * math.pi * 1.2 * t0 + i * 1.7)
            sparkle(d, cx2, cy2, r * (0.6 + 0.6 * a), int(255 * (0.3 + 0.7 * a)))

# 4) coraçõezinhos descendo até o link
_hr = random.Random(11)
HEARTS = [(_hr.uniform(80, 560), _hr.uniform(0, 2.4), _hr.uniform(2.6, 4.0), _hr.uniform(-1, 1)) for _ in range(9)]
def cta_hearts(layer, t0):
    items_by_alpha = []
    for x0, st, sc, ph in HEARTS:
        tt = t0 - st * 0.6
        if tt < 0: continue
        p = (tt % 1.4) / 1.4                       # cada coração cai em 1,4s e recomeça
        y = 1020 + p * 430; x = x0 + 30 * math.sin(2 * math.pi * p + ph)
        a = int(255 * min(1, p / .15) * min(1, (1 - p) / .25))
        items_by_alpha.append(([*heart_pts(x, y, sc, 30)], a))
    for pts, a in items_by_alpha:
        marker(layer, [pts], a)

# 5) setinhas ˅ desenhadas acendendo em cascata
def chev(cx, cy, w=92, h=44):
    return [(cx - w, cy - h + 2), (cx - w / 2, cy - h / 3), (cx, cy + h), (cx + w / 2, cy - h / 3 - 2), (cx + w, cy - h)]
def cta_chevrons(layer, t0):
    for col, cx in enumerate((190,)):
        for i in range(4):
            cy = 1180 + i * 90
            ph = (t0 * 1.6 - i * 0.22) % 1.0
            a = 0.45 + 0.55 * max(0, 1 - abs(ph - 0.15) / 0.3)
            k = min(1.0, max(0.0, (t0 - i * 0.1) / 0.25))
            if k <= 0: continue
            pts = catmull(chev(cx, cy + (1 - k) * -30), 6)
            marker(layer, [pts], int(255 * a * k))

CTAS = {"doodle": cta_doodle, "emoji": cta_emoji, "spot": cta_spot, "hearts": cta_hearts, "chevrons": cta_chevrons}

for f in range(int(round(TOTAL * FPS))):
    t = f / FPS
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if t >= CTA_T and CTA == "spot": cta_spot(layer, t - CTA_T)
    if t < HOOK_END:
        base = RANSOM[(f // 5) % 3]; k = min(1.0, t / 0.18)
        if k < 1:
            s = 0.6 + 0.5 * k if k < .8 else 1.1 - .5 * (k - .8)
            r = base.resize((int(W * s), int(H * s)), Image.LANCZOS); cx, cy = W / 2, 250
            if s <= 1: layer.alpha_composite(r, (int(cx - cx * s), int(cy - cy * s)))
            else: layer.alpha_composite(r, (0, 0), (int(cx * s - cx), int(cy * s - cy)))
        else:
            layer.alpha_composite(base)
    for i, (st, en, lines, font) in enumerate(EVENTS):
        if st <= t < en:
            n = int((t - st) * (24 if i == 0 else 30))
            total_chars = sum(len(EMO_RE.sub("x", l)) for l in lines)
            typed(layer, lines, n, 335 if i == 0 else 330, font, n < total_chars or int(t * 2.5) % 2 == 0)
    if t >= CTA_T and CTA != "spot": CTAS[CTA](layer, t - CTA_T)
    layer.save(os.path.join(OUT, f"{f:04d}.png"), compress_level=1)
print(N, "frames:", f + 1)
