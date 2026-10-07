"""Vestido tubinho: 'lupa de detalhes' — congela o vídeo e passeia uma lente de aumento pelos detalhes,
com etiquetas ligadas por linha. Escreve frames RGB no stdout."""
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import os, sys, math, re, json

V = os.path.dirname(os.path.abspath(__file__)); S = os.path.dirname(V)
W, H, FPS = 1080, 1920, 30
GOLD = (214, 172, 92)
_cache = {}
def src(t):
    i = min(284, max(1, int(round(t * 30)) + 1))
    if i not in _cache:
        if len(_cache) > 40: _cache.clear()
        _cache[i] = Image.open(os.path.join(V, "src/%04d.jpg" % i)).convert("RGB")
    return _cache[i]

# linha do tempo: (duração na saída, tipo, parâmetros)
# play: (ini, fim) do original;  freeze: instante congelado + roteiro da lupa
FRONT = [  # (x, y do detalhe, zoom, texto, lado da etiqueta)
    (520, 600, 1.6, "gola alta ✨", "r"),
    (520, 1000, 1.55, "decote drapeado 🖤", "l"),
    (330, 1270, 1.6, "justinho, em suplex", "r"),
]
BACK = [
    (540, 860, 1.4, "costas nuas 🔥", "r"),
    (560, 1015, 1.7, "tirinha atrás ✨", "l"),
]
TL = [
    (1.0, "play", (0.0, 1.0)),
    (3.3, "freeze", (1.0, FRONT)),
    (1.5, "play", (1.0, 3.1)),
    (0.9, "play", (3.1, 4.0)),
    (2.4, "freeze", (4.0, BACK)),
    (4.38, "play", (4.0, 9.47)),
    (0.5, "freeze", (9.45, [])),
]
TOTAL = sum(d for d, _, _ in TL)
STARTS = []; acc = 0
for d, _, _ in TL: STARTS.append(acc); acc += d
CTA_T = STARTS[5] + (7.5 - 4.0) / 1.25   # quando ela começa a apontar

F = lambda w, s: ImageFont.truetype(os.path.join(S, f"mont{w}.ttf"), s)
EMO = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf", 109)
EMO_RE = re.compile(r"([\U0001F300-\U0001FAFF☀-➿\U0001F5A4]️?)")
_ec = {}
def emoji(ch, size):
    if (ch, size) not in _ec:
        im = Image.new("RGBA", (160, 160), (0, 0, 0, 0)); ImageDraw.Draw(im).text((10, 10), ch, font=EMO, embedded_color=True)
        im = im.crop(im.getbbox()); _ec[(ch, size)] = im.resize((max(1, int(im.width * size / im.height)), size), Image.LANCZOS)
    return _ec[(ch, size)]

def rich(img, text, x, y, font, fill="white", stroke=5, sfill="black", anchor_center=True, n=None):
    """texto com emoji colorido; x é o centro se anchor_center"""
    parts = [p for p in EMO_RE.split(text) if p]; asc, desc = font.getmetrics(); es = int(asc * .95)
    wid = sum(emoji(p, es).width if EMO_RE.fullmatch(p) else font.getlength(p) for p in parts)
    cx = x - wid / 2 if anchor_center else x; d = ImageDraw.Draw(img); left = 10 ** 6 if n is None else n
    for p in parts:
        if left <= 0: break
        if EMO_RE.fullmatch(p):
            img.alpha_composite(emoji(p, es), (int(cx), int(y + (asc - es) / 2 + 4))); cx += emoji(p, es).width; left -= 1
        else:
            q = p[:left]; left -= len(p)
            d.text((cx, y), q, font=font, fill=fill, stroke_width=stroke, stroke_fill=sfill); cx += font.getlength(p)
    return wid

def ease(p): return p * p * (3 - 2 * p)

R = 200  # raio da lente
def loupe(img, base, x, y, zoom, k):
    """lente circular em (x,y) ampliando base; k = 0..1 escala de entrada"""
    r = int(R * (0.3 + 0.7 * k)) if k < 1 else R
    if r < 10: return
    cw = int(2 * r / zoom); box = (int(x - cw / 2), int(y - cw / 2), int(x + cw / 2), int(y + cw / 2))
    lens = base.crop(box).resize((2 * r, 2 * r), Image.LANCZOS).convert("RGBA")
    lens = ImageEnhance.Sharpness(lens).enhance(1.4)
    m = Image.new("L", (2 * r, 2 * r), 0); ImageDraw.Draw(m).ellipse((0, 0, 2 * r - 1, 2 * r - 1), fill=255); lens.putalpha(m)
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse((x - r + 6, y - r + 14, x + r + 6, y + r + 14), fill=(0, 0, 0, 120))
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14)))
    img.alpha_composite(lens, (int(x - r), int(y - r)))
    d = ImageDraw.Draw(img)
    d.ellipse((x - r, y - r, x + r, y + r), outline=(255, 255, 255), width=10)
    d.ellipse((x - r - 5, y - r - 5, x + r + 5, y + r + 5), outline=GOLD, width=4)
    # cabinho da lupa
    a = math.radians(135); hx, hy = x + (r + 6) * math.cos(a), y + (r + 6) * math.sin(a)
    d.line((hx, hy, hx + 70 * math.cos(a), hy + 70 * math.sin(a)), fill=(255, 255, 255), width=22)
    d.line((hx, hy, hx + 70 * math.cos(a), hy + 70 * math.sin(a)), fill=GOLD, width=10)

def label(img, x, y, side, text, k):
    """etiqueta com linha saindo da borda da lente"""
    if k <= 0: return
    font = F(800, 46); d = ImageDraw.Draw(img)
    sx = x + (R if side == "r" else -R) * 0.92; sy = y - R * 0.35
    ex = sx + (90 if side == "r" else -90) * min(1, k * 2); ey = sy - 70 * min(1, k * 2)
    d.line((sx, sy, ex, ey), fill="white", width=5); d.ellipse((sx - 8, sy - 8, sx + 8, sy + 8), fill="white")
    if k < 0.5: return
    a = int(255 * min(1, (k - .5) * 3))
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
    tw = rich(Image.new("RGBA", (10, 10)), text, 0, 0, font)
    px = ex - (0 if side == "r" else tw + 44); px = min(max(px, 20), W - tw - 64); py = ey - 40
    dl.rounded_rectangle((px, py, px + tw + 44, py + 78), 39, fill=(255, 255, 255, 240))
    rich(lay, text, px + 22, py + 12, font, fill=(20, 20, 20), stroke=0, anchor_center=False)
    lay.putalpha(lay.getchannel("A").point(lambda v: v * a // 255)); img.alpha_composite(lay)

def top_text(img, text, t0, t, y=190, size=64):
    if t < t0: return
    font = F(800, size); n = int((t - t0) * 26)
    rich(img, text, W / 2, y, font, n=n)

def cta(img, t0):
    """lupinha desenhada 'tocando' em direção ao link, com ondas"""
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay); cx, cy = 300, 1330
    bob = 18 * abs(math.sin(math.pi * 1.6 * t0))
    x, y = cx + bob * .6, cy + bob
    for i in range(3):  # ondas indo para o link
        p = ((t0 * 1.2) - i * 0.33) % 1.0; r = 30 + 110 * p; a = int(220 * (1 - p))
        d.arc((160 - r, 1480 - r * .45, 160 + r, 1480 + r * .45), 200, 340, fill=(255, 255, 255, a), width=6)
    k = min(1.0, t0 / 0.25); r = int(58 * (0.4 + 0.6 * k))
    d.ellipse((x - r, y - r, x + r, y + r), outline=(255, 255, 255), width=12)
    d.ellipse((x - r - 4, y - r - 4, x + r + 4, y + r + 4), outline=GOLD, width=4)
    a = math.radians(225); hx, hy = x + r * math.cos(a), y + r * math.sin(a)
    # cabo apontando para baixo-esquerda (na direção do link)
    a2 = math.radians(135); hx, hy = x + r * math.cos(a2), y + r * math.sin(a2)
    d.line((hx, hy, hx + 60 * math.cos(a2), hy + 60 * math.sin(a2)), fill=(255, 255, 255), width=18)
    d.line((hx, hy, hx + 60 * math.cos(a2), hy + 60 * math.sin(a2)), fill=GOLD, width=8)
    for i, (sx, sy) in enumerate([(420, 1260), (120, 1240), (470, 1420)]):
        aa = 0.5 + 0.5 * math.sin(2 * math.pi * 1.3 * t0 + i * 2)
        rr = 14 + 10 * aa
        for dx, dy in ((rr, 0), (0, rr)):
            d.line((sx - dx, sy - dy, sx + dx, sy + dy), fill=(255, 255, 255, int(255 * (0.3 + 0.7 * aa))), width=6)
    img.alpha_composite(lay)

out = sys.stdout.buffer
for f in range(int(TOTAL * FPS)):
    t = f / FPS
    si = max(i for i, s0 in enumerate(STARTS) if t >= s0 - 1e-6); d_, kind, par = TL[si]; lt = t - STARTS[si]
    if kind == "play":
        a, b = par; st = a + (b - a) * lt / d_; base = src(st)
    else:
        base = src(par[0])
    img = base.convert("RGBA")
    if kind == "freeze" and par[1]:
        spots = par[1]; seg = d_ / len(spots)
        # foco: escurece e desfoca levemente o fundo
        fk = min(1.0, lt / 0.25) * min(1.0, (d_ - lt) / 0.2)
        dim = Image.new("RGBA", img.size, (0, 0, 0, int(120 * fk))); img.alpha_composite(dim)
        if lt < 0.08: img.alpha_composite(Image.new("RGBA", img.size, (255, 255, 255, int(200 * (1 - lt / .08)))))  # flash
        i = min(len(spots) - 1, int(lt / seg)); p = (lt - i * seg) / seg
        x, y, z, txt, side = spots[i]
        if i > 0 and p < 0.25:  # desliza da posição anterior
            q = ease(p / 0.25); px_, py_, pz, _, _ = spots[i - 1]
            x, y, z = px_ + (x - px_) * q, py_ + (y - py_) * q, pz + (z - pz) * q
        k_in = min(1.0, lt / 0.2) * min(1.0, (d_ - lt) / 0.15)
        loupe(img, base, x, y, z, k_in)
        if p > 0.25 or i == 0: label(img, x, y, side, txt, min(1.0, (p - (0.25 if i else 0.1)) / 0.3) * k_in)
        top_text(img, "zoom nos detalhes 🔍" if si == 1 else "o segredo 🤫", STARTS[si] + 0.1, t, y=150, size=56)
    if si == 0:
        top_text(img, "esse vestido tem", 0.1, t, y=190, size=66)
        top_text(img, "um segredo 🤫", 0.1 + 16 / 26, t, y=275, size=66)
    if si == 2:
        top_text(img, "agora olha as costas 👀", STARTS[2] + 0.05, t, y=210, size=62)
    if t >= CTA_T: cta(img, t - CTA_T)
    out.write(img.convert("RGB").tobytes())
print(json.dumps({"total": TOTAL, "cta": CTA_T}), file=sys.stderr)
