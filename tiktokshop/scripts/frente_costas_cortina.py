"""Vestido tubinho (foto frente+costas): enquete 'frente ou costas?', cortina deslizante,
zoom de detalhes com moldura de foco de câmera e CTA com a moldura travando no link.
Escreve frames RGB no stdout e os tempos dos 'cliques' em split/clicks.json."""
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter
import os, sys, math, re, json

D = os.path.dirname(os.path.abspath(__file__)); S = os.path.dirname(D)
W, H, FPS = 1080, 1920, 30
FULL = ImageOps.exif_transpose(Image.open("/root/.claude/uploads/f05dfe21-700d-5c7c-a427-931b58f48d32/8ac6eb4a-image.jpg")).convert("RGB")
SPLIT = 1535
FRONT, BACK = FULL.crop((0, 0, SPLIT, FULL.height)), FULL.crop((SPLIT + 1, 0, FULL.width, FULL.height))
FULL_SMALL = FULL.resize((W, int(FULL.height * W / FULL.width)), Image.LANCZOS)
AR = W / H
VH_MAX = int(FRONT.width / AR)

def view(img, cx, cy, vh):
    vh = min(vh, VH_MAX); vw = vh * AR
    cx = min(max(cx, vw / 2), img.width - vw / 2); cy = min(max(cy, vh / 2), img.height - vh / 2)
    return img.crop((int(cx - vw / 2), int(cy - vh / 2), int(cx + vw / 2), int(cy + vh / 2))).resize((W, H), Image.BILINEAR)

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
def rich(img, text, x, y, font, fill="white", stroke=6, sfill="black", n=None, center=True):
    parts = [p for p in EMO_RE.split(text) if p]; asc, desc = font.getmetrics(); es = int(asc * .95)
    wid = sum(emoji(p, es).width if EMO_RE.fullmatch(p) else font.getlength(p) for p in parts)
    cx = x - wid / 2 if center else x; d = ImageDraw.Draw(img); left = 10 ** 6 if n is None else n
    for p in parts:
        if left <= 0: break
        if EMO_RE.fullmatch(p):
            img.alpha_composite(emoji(p, es), (int(cx), int(y + (asc - es) / 2 + 4))); cx += emoji(p, es).width; left -= 1
        else:
            q = p[:left]; left -= len(p); d.text((cx, y), q, font=font, fill=fill, stroke_width=stroke, stroke_fill=sfill); cx += font.getlength(p)
    return wid

def brackets(img, box, k, color=(255, 255, 255), L=70, w=9, rec=True):
    """cantinhos de foco de câmera; k=0..1 'trava' de fora para dentro"""
    x0, y0, x1, y1 = box; pad = (1 - ease(k)) * 120
    x0, y0, x1, y1 = x0 - pad, y0 - pad, x1 + pad, y1 + pad
    d = ImageDraw.Draw(img)
    for (cx, cy, sx, sy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
        d.line((cx, cy, cx + sx * L, cy), fill=color, width=w); d.line((cx, cy, cx, cy + sy * L), fill=color, width=w)
    if k >= 1 and rec:  # pontinho vermelho de 'gravando'
        d.ellipse((x0 + 24, y0 + 24, x0 + 46, y0 + 46), fill=(255, 60, 60))

def pill(img, text, cx, y, font, bg=(255, 255, 255, 235), fg=(20, 20, 20)):
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0)); tw = rich(Image.new("RGBA", (4, 4)), text, 0, 0, font)
    ImageDraw.Draw(lay).rounded_rectangle((cx - tw / 2 - 30, y, cx + tw / 2 + 30, y + 84), 42, fill=bg)
    rich(lay, text, cx, y + 14, font, fill=fg, stroke=0); img.alpha_composite(lay)

# detalhes (metade, cx, cy, altura visível, legenda)
DET = [
    (FRONT, 738, 1700, 1000, "gola alta ✨"),
    (FRONT, 738, 2120, 1100, "decote drapeado 🖤"),
    (BACK, 771, 1930, 1300, "costas nuas 🔥"),
    (BACK, 771, 2280, 950, "tirinha atrás ✨"),
]
T_HOOK, T_SLIDE, T_DET, T_END = 2.6, 3.0, 1.3, 3.0
t1 = T_HOOK; t2 = t1 + T_SLIDE; t3 = t2 + T_DET * len(DET); TOTAL = t3 + T_END
CLICKS = [t2 + i * T_DET + 0.28 for i in range(len(DET))] + [t3 + 1.0 + 0.3]

out = sys.stdout.buffer
for f in range(int(TOTAL * FPS)):
    t = f / FPS
    if t < t1:  # hook: frente com câmera descendo + enquete
        p = t / T_HOOK; img = view(FRONT, 768, lerp(1800, 2500, ease(p)), lerp(2500, 2729, p)).convert("RGBA")
        n = int(max(0, t - .1) * 24); rich(img, "frente ou costas? 🤔", W / 2, 200, F(900, 76), n=n)
        if t > 1.0:
            k = ease((t - 1.0) / .3)
            pill(img, "FRENTE 👀", lerp(W / 2, 290, k), 320, F(800, 50)); pill(img, "COSTAS 🔥", lerp(W / 2, 790, k), 320, F(800, 50))
    elif t < t2:  # cortina deslizante entre frente e costas
        lt = t - t1; fr = view(FRONT, 768, 2500, 2729); bk = view(BACK, 768, 2500, 2729)
        if lt < 1.1: x = lerp(W, 0, ease(lt / 1.1))
        elif lt < 1.5: x = 0
        elif lt < 2.4: x = lerp(0, W / 2, ease((lt - 1.5) / .9))
        else: x = W / 2 + 18 * math.sin((lt - 2.4) * 10) * max(0, 1 - (lt - 2.4) / .6)
        img = bk.copy(); img.paste(fr.crop((0, 0, int(x), H)), (0, 0)); img = img.convert("RGBA")
        d = ImageDraw.Draw(img); d.rectangle((x - 4, 0, x + 4, H), fill="white")
        d.ellipse((x - 46, H / 2 - 46, x + 46, H / 2 + 46), fill="white")
        d.polygon([(x - 30, H / 2), (x - 12, H / 2 - 16), (x - 12, H / 2 + 16)], fill=(30, 30, 30))
        d.polygon([(x + 30, H / 2), (x + 12, H / 2 - 16), (x + 12, H / 2 + 16)], fill=(30, 30, 30))
        if x > 160: pill(img, "FRENTE", min(x / 2, 300), 200, F(800, 46))
        if x < W - 160: pill(img, "COSTAS", max((x + W) / 2, 780), 200, F(800, 46))
    elif t < t3:  # zoom nos detalhes com moldura de foco
        i = int((t - t2) / T_DET); lt = t - t2 - i * T_DET
        half, cx, cy, vh, txt = DET[i]
        if i == 0: pcx, pcy, pvh, phalf = 768, 2500, 2729, FRONT
        else: phalf, pcx, pcy, pvh, _ = DET[i - 1]
        if phalf is not half: pcx, pcy, pvh = 768, 2500, 2729
        q = ease(lt / 0.3)
        img = view(half, lerp(pcx, cx, q), lerp(pcy, cy, q), lerp(pvh, vh, q))
        if lt < 0.3: img = img.filter(ImageFilter.GaussianBlur(6 * (1 - q)))
        img = img.convert("RGBA")
        if lt > 0.25:
            k = min(1.0, (lt - 0.25) / 0.18); brackets(img, (190, 620, 890, 1300), k)
        if lt > 0.45: pill(img, txt, W / 2, 1360, F(800, 54))
        if lt < 0.06: img.alpha_composite(Image.new("RGBA", img.size, (255, 255, 255, int(180 * (1 - lt / .06)))))
    else:  # final: as duas metades + CTA
        lt = t - t3; s = lerp(1.08, 1.0, ease(lt / .5))
        big = FULL_SMALL.resize((int(W * s), int(FULL_SMALL.height * s)), Image.BILINEAR)
        img = Image.new("RGB", (W, H), (0, 0, 0)); img.paste(big, ((W - big.width) // 2, (H - big.height) // 2)); img = img.convert("RGBA")
        rich(img, "os dois lados 🖤", W / 2, 170, F(900, 76), n=int(lt * 24))
        if lt > 1.0:  # moldura de foco travando na área do link da loja
            k = min(1.0, (lt - 1.0) / 0.3); pulse = 6 * math.sin((lt - 1.0) * 6) if k >= 1 else 0
            brackets(img, (40 - pulse, 1480 - pulse, 860 + pulse, 1770 + pulse), k, color=(255, 255, 255), L=60, w=8, rec=False)
    out.write(img.convert("RGB").tobytes())
json.dump({"total": TOTAL, "clicks": CLICKS, "whoosh": [t1 + 0.0, t1 + 1.5]}, open(os.path.join(D, "clicks.json"), "w"))
