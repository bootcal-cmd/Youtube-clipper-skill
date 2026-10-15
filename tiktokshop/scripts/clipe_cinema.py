"""Edição estilo clipe: tempo original preservado (lip sync), grade de cinema, letterbox, granulação,
vazamento de luz nos cortes, push-in lento e créditos. Frames RGB no stdout."""
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageChops
import os, sys, math, random
import numpy as np

D = os.path.dirname(os.path.abspath(__file__)); S = os.path.dirname(D)
W, H, FPS, N = 1080, 1920, 30, 442
CUTS = [0.0, 1.883, 7.033, N / FPS]
BAR = 150  # tarjas de cinema

def ease(p): p = min(1.0, max(0.0, p)); return p * p * (3 - 2 * p)
def lerp(a, b, p): return a + (b - a) * p

# grade de filme: sombras levemente frias, altas quentes, contraste em S suave
x = np.arange(256) / 255.0
curve = np.clip(0.5 + (x - 0.5) * 1.12 + 0.04 * np.sin((x - 0.5) * np.pi * 2) * 0, 0, 1)
s_curve = np.clip(x + 0.10 * np.sin(2 * np.pi * (x - 0.25)) * (x * (1 - x)) * 4, 0, 1)
R = np.clip(s_curve * 1.03 + 0.01, 0, 1); G = s_curve; B = np.clip(s_curve * 0.94 + 0.035 * (1 - x), 0, 1)
LUT = (np.concatenate([R, G, B]) * 255).astype(np.uint8).tolist()

rng = np.random.default_rng(1)
GRAINS = [Image.fromarray((rng.normal(128, 18, (H // 2, W // 2))).clip(0, 255).astype(np.uint8)).resize((W, H), Image.BILINEAR) for _ in range(6)]
VIG = Image.new("L", (W // 8, H // 8), 0); ImageDraw.Draw(VIG).ellipse((-40, -30, W // 8 + 40, H // 8 + 30), fill=255)
VIG = VIG.filter(ImageFilter.GaussianBlur(16)).resize((W, H), Image.BILINEAR)

def leak(img, p, side):
    """vazamento de luz quente atravessando a tela"""
    if p <= 0 or p >= 1: return img
    lay = Image.new("RGB", (W // 4, H // 4), (0, 0, 0)); d = ImageDraw.Draw(lay)
    cx = lerp(-80, W // 4 + 80, p) if side else lerp(W // 4 + 80, -80, p)
    a = math.sin(math.pi * p)
    d.ellipse((cx - 90, -40, cx + 90, H // 4 + 40), fill=(int(255 * a), int(140 * a), int(50 * a)))
    d.ellipse((cx - 40, H // 8 - 120, cx + 40, H // 8 + 120), fill=(int(255 * a), int(220 * a), int(170 * a)))
    lay = lay.filter(ImageFilter.GaussianBlur(28)).resize((W, H), Image.BILINEAR)
    return ImageChops.screen(img, lay)

SERIF = ImageFont.truetype(os.path.join(S, "vibes.ttf"), 120)
SANS = ImageFont.truetype(os.path.join(S, "mont500.ttf"), 30)
SANS_B = ImageFont.truetype(os.path.join(S, "mont700.ttf"), 34)
def spaced(d, text, cx, y, font, fill, sp=10):
    w = sum(font.getlength(c) + sp for c in text) - sp; x = cx - w / 2
    for c in text: d.text((x, y), c, font=font, fill=fill); x += font.getlength(c) + sp

def credits_open(img, t):
    if t > 3.2: return
    a = min(1, t / .8) * min(1, (3.2 - t) / .7)
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay); A = int(255 * a)
    spaced(d, "UMA HOMENAGEM", W / 2, H - BAR - 300, SANS_B, (255, 236, 205, A), 14)
    d.line((W / 2 - 120, H - BAR - 245, W / 2 + 120, H - BAR - 245), fill=(214, 172, 92, A), width=2)
    img.alpha_composite(lay)
def credits_close(img, t, T):
    lt = t - (T - 2.6)
    if lt < 0: return
    a = min(1, lt / .7)
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay); A = int(255 * a)
    tw = SERIF.getlength("com amor"); d.text(((W - tw) / 2, H - BAR - 330), "com amor", font=SERIF, fill=(255, 232, 200, A))
    spaced(d, "HOMENAGEM", W / 2, H - BAR - 150, SANS, (255, 236, 205, int(A * .85)), 16)
    img.alpha_composite(lay)

T = N / FPS
out = sys.stdout.buffer
for f in range(N):
    t = f / FPS
    img = Image.open(os.path.join(D, "src/%04d.jpg" % (f + 1))).convert("RGB")
    ci = max(i for i, c in enumerate(CUTS) if t >= c - 1e-6); lt = t - CUTS[ci]
    z = 1.0 + 0.045 * lt / max(0.1, CUTS[min(ci + 1, len(CUTS) - 1)] - CUTS[ci])   # push-in lento por plano
    if z > 1.001:
        cw, ch = W / z, H / z; img = img.crop((int((W - cw) / 2), int((H - ch) / 2), int((W + cw) / 2), int((H + ch) / 2))).resize((W, H), Image.BICUBIC)
    img = img.point(LUT)
    img = ImageEnhance.Color(img).enhance(0.9)
    # glow suave nas altas
    small = img.resize((W // 4, H // 4), Image.BILINEAR)
    hi = small.point(lambda v: 0 if v < 170 else min(255, (v - 170) * 3)).filter(ImageFilter.GaussianBlur(12)).resize((W, H), Image.BILINEAR)
    img = ImageChops.screen(img, Image.eval(hi, lambda v: int(v * .35)))
    # vinheta
    dark = Image.new("RGB", img.size, (8, 5, 3)); img = Image.composite(img, dark, Image.eval(VIG, lambda v: int(150 + v * 105 / 255)))
    # vazamento de luz nos cortes e na abertura
    for k, c in enumerate(CUTS[1:-1]):
        img = leak(img, (t - (c - .35)) / .8, k % 2 == 0)
    img = leak(img, t / 1.2, True)
    # granulação
    g = GRAINS[f % len(GRAINS)]; img = Image.blend(img, ImageChops.overlay(img, Image.merge("RGB", (g, g, g))), 0.35)
    img = img.convert("RGBA")
    # fade de entrada e saída
    if t < .5: img.alpha_composite(Image.new("RGBA", img.size, (0, 0, 0, int(255 * (1 - t / .5)))))
    if t > T - .6: img.alpha_composite(Image.new("RGBA", img.size, (0, 0, 0, int(255 * min(1, (t - (T - .6)) / .6)))))
    credits_open(img, t); credits_close(img, t, T)
    d = ImageDraw.Draw(img); d.rectangle((0, 0, W, BAR), fill=(0, 0, 0)); d.rectangle((0, H - BAR, W, H), fill=(0, 0, 0))
    out.write(img.convert("RGB").tobytes())
