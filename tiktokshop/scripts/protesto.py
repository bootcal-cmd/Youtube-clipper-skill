"""Vídeo de protesto: narração + prints da violação + legendas. Gera frames RGBA em prot_ov/ e timeline.json."""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os, re, json, math, random

S = os.path.dirname(os.path.abspath(__file__))
U = "/root/.claude/uploads/f05dfe21-700d-5c7c-a427-931b58f48d32/"
OUT = os.path.join(S, "prot_ov"); os.makedirs(OUT, exist_ok=True)
for f in os.listdir(OUT): os.remove(os.path.join(OUT, f))
W, H, FPS = 1080, 1920, 30
WINE = (120, 18, 42)

meta = json.load(open(os.path.join(S, "narr/meta.json")))
LEAD, GAP = 0.3, 0.35
starts, t = [], LEAD
for d in meta["dur"]:
    starts.append(round(t, 2)); t += d + GAP
TOTAL = round(t + 0.6, 2)
SEG = [(s, s + d) for s, d in zip(starts, meta["dur"])]
json.dump({"starts": starts, "total": TOTAL, "seg": SEG}, open(os.path.join(S, "prot_timeline.json"), "w"))

F = lambda w, s: ImageFont.truetype(os.path.join(S, f"mont{w}.ttf"), s)
SUB = F(800, 50)
EMO = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf", 109)
EMO_RE = re.compile(r"([\U0001F300-\U0001FAFF☀-➿⌚⌛]️?)")
_ec = {}
def emoji(ch, size):
    if (ch, size) not in _ec:
        im = Image.new("RGBA", (160, 160), (0, 0, 0, 0)); ImageDraw.Draw(im).text((10, 10), ch, font=EMO, embedded_color=True)
        im = im.crop(im.getbbox()); _ec[(ch, size)] = im.resize((int(im.width * size / im.height), size), Image.LANCZOS)
    return _ec[(ch, size)]

# ---------- letras recortadas (hook) ----------
SERIFS = ["/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf", "/usr/share/fonts/truetype/liberation/LiberationSerif-BoldItalic.ttf",
          "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"]
TILES = [(120, 18, 42), (20, 14, 16), (176, 44, 72), (245, 222, 226), (214, 150, 160)]
def tile(ch, rnd, h=150):
    font = ImageFont.truetype(rnd.choice(SERIFS), int(h * rnd.uniform(.80, .95))); bg = rnd.choice(TILES)
    fg = rnd.choice([(255, 255, 255), (250, 232, 232)]) if sum(bg) < 520 else rnd.choice([WINE, (60, 8, 20)])
    w = int(font.getlength(ch)) + rnd.randint(12, 24); hh = h + rnd.randint(-14, 10)
    im = Image.new("RGBA", (w + 20, hh + 20), (0, 0, 0, 0)); d = ImageDraw.Draw(im); j = lambda: rnd.randint(-5, 5)
    d.polygon([(10 + j(), 10 + j()), (w + 10 + j(), 10 + j()), (w + 10 + j(), hh + 10 + j()), (10 + j(), hh + 10 + j())], fill=bg + (255,))
    d.text(((w + 20) / 2, (hh + 20) / 2), ch, font=font, fill=fg, anchor="mm")
    im = im.rotate(rnd.uniform(-8, 8), resample=Image.BICUBIC, expand=True)
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); sh.putalpha(im.getchannel("A").point(lambda a: a * .45))
    out = Image.new("RGBA", (im.width + 8, im.height + 8), (0, 0, 0, 0))
    out.alpha_composite(sh.filter(ImageFilter.GaussianBlur(4)), (6, 6)); out.alpha_composite(im, (0, 0)); return out
def ransom(text, seed, y, maxw=960):
    rnd = random.Random(seed); tiles = [None if c == " " else tile(c, rnd) for c in text]
    gap, sp = -16, 60; total = sum(sp if t is None else t.width + gap for t in tiles); sc = min(1.0, maxw / total)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0)); x = (W - total * sc) / 2
    for t in tiles:
        if t is None: x += sp * sc; continue
        t2 = t.resize((int(t.width * sc), int(t.height * sc)), Image.LANCZOS)
        layer.alpha_composite(t2, (int(x), int(y + rnd.randint(-8, 8)))); x += (t.width + gap) * sc
    return layer
RANSOM = [ransom("COMO ASSIM", s, 160) for s in (31, 32, 33)]

# ---------- texto com contorno (legendas) ----------
def wrap(text, font, maxw):
    words, lines, cur = text.split(), [], ""
    for w_ in words:
        test = (cur + " " + w_).strip()
        if font.getlength(EMO_RE.sub("MM", test)) <= maxw: cur = test
        else: lines.append(cur); cur = w_
    return lines + [cur]
def outlined(layer, lines, y, font, n_chars=None, fill="white"):
    d = ImageDraw.Draw(layer); asc, desc = font.getmetrics(); lh = asc + desc; es = int(asc * .95)
    left = 10 ** 6 if n_chars is None else n_chars
    for li, line in enumerate(lines):
        parts = [p for p in EMO_RE.split(line) if p]
        full_w = sum(emoji(p, es).width if EMO_RE.fullmatch(p) else font.getlength(p) for p in parts)
        x = (W - full_w) / 2; yy = y + li * lh
        for p in parts:
            if left <= 0: return
            if EMO_RE.fullmatch(p):
                layer.alpha_composite(emoji(p, es), (int(x), int(yy + (asc - es) / 2 + 6))); x += emoji(p, es).width; left -= 1
            else:
                q = p[:left]; left -= len(p)
                d.text((x + 3, yy + 4), q, font=font, fill=(0, 0, 0, 120), stroke_width=5, stroke_fill=(0, 0, 0, 120))
                d.text((x, yy), q, font=font, fill=fill, stroke_width=5, stroke_fill="black"); x += font.getlength(p)

# ---------- cartões com os prints ----------
def card_from(path, box, width=960, radius=34):
    im = Image.open(U + path).convert("RGB").crop(box)
    im = im.resize((width, int(im.height * width / im.width)), Image.LANCZOS).convert("RGBA")
    m = Image.new("L", im.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, im.width, im.height), radius, fill=255); im.putalpha(m)
    return im
C_PTS = card_from("a29c0322-image.jpg", (0, 250, 1080, 1060))
C_MOT = card_from("a29c0322-image.jpg", (0, 1350, 1080, 1830))
C_REC = card_from("920b7bb0-image.jpg", (0, 350, 1080, 910))
C_LIST = card_from("44f1918e-image.jpg", (0, 1545, 1080, 1685), width=880, radius=26)
C_INT = card_from("43dd8f42-image.jpg", (0, 1770, 1080, 2240))
SCALE_MOT = 960 / 1080
# grifos no print do motivo (coordenadas do recorte original, antes da escala)
HL_FONE = [(515, 85, 1005, 142), (45, 140, 205, 197)]          # "fones de ouvido sem fio" + "3 em 1"
HL_PULS = [(862, 140, 1025, 197), (45, 193, 268, 250)]          # "pulseira" + "de relógio"

def put_card(layer, card, t_in, t, cy=820, hl=None):
    k = min(1.0, max(0.0, (t - t_in) / 0.3)); k = 1 - (1 - k) ** 3
    s = (0.86 + 0.14 * k) * (1 + 0.012 * max(0, t - t_in))          # pop + zoom lento
    c = card.copy()
    if hl:
        hlay = Image.new("RGBA", c.size, (0, 0, 0, 0)); d = ImageDraw.Draw(hlay)
        for (boxes, st, dur) in hl:
            p = min(1.0, max(0.0, (t - st) / dur))
            if p <= 0: continue
            total = sum(b[2] - b[0] for b in boxes); acc = p * total
            for (x0, y0, x1, y1) in boxes:
                seg = min(acc, x1 - x0); acc -= seg
                if seg <= 0: break
                d.rounded_rectangle((x0 * SCALE_MOT - 6, y0 * SCALE_MOT, (x0 + seg) * SCALE_MOT + 6, y1 * SCALE_MOT), 10, fill=(255, 220, 0, 110))
        # grifo por baixo do texto: mistura "multiply" simples para o texto continuar legível
        base = c.convert("RGB"); hl_rgb = Image.new("RGB", c.size, (255, 226, 60))
        mask = hlay.getchannel("A").point(lambda v: 255 if v else 0)
        from PIL import ImageChops
        mult = ImageChops.multiply(base, hl_rgb)
        base.paste(mult, (0, 0), mask); a = c.getchannel("A"); c = base.convert("RGBA"); c.putalpha(a)
    c = c.resize((int(c.width * s), int(c.height * s)), Image.LANCZOS)
    if k < 1: c.putalpha(c.getchannel("A").point(lambda v: int(v * k)))
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    x, y = (W - c.width) // 2, int(cy - c.height / 2)
    ImageDraw.Draw(sh).rounded_rectangle((x + 8, y + 14, x + c.width + 8, y + c.height + 14), 34, fill=(0, 0, 0, int(110 * k)))
    layer.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14))); layer.alpha_composite(c, (x, y))

def pill(layer, text, y, font, bg, fg, a=255):
    d = ImageDraw.Draw(layer); w = font.getlength(text); asc, desc = font.getmetrics()
    x0 = (W - w) / 2 - 34; d.rounded_rectangle((x0, y, x0 + w + 68, y + asc + desc + 30), 40, fill=bg + (a,))
    d.text((x0 + 34, y + 15), text, font=font, fill=fg + (a,))

def pop_word(layer, text, emo, cx, cy, t_in, t, color):
    k = min(1.0, max(0.0, (t - t_in) / 0.2))
    if k <= 0: return
    s = 1.35 - 0.35 * k; font = F(900, int(110 * s))
    d = ImageDraw.Draw(layer); w = font.getlength(text); e = emoji(emo, int(100 * s))
    x = cx - (w + e.width + 20) / 2
    d.text((x, cy), text, font=font, fill=color, stroke_width=8, stroke_fill="black", anchor="lm")
    layer.alpha_composite(e, (int(x + w + 20), int(cy - e.height / 2)))

timeline = {i: s for i, s in enumerate(starts)}
SUB_Y = 1330
for f in range(int(round(TOTAL * FPS))):
    t = f / FPS; L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    seg = max([i for i, s in enumerate(starts) if t >= s - 0.15] or [0])
    st = starts[seg]; lt = t - st
    if seg == 0:
        L.alpha_composite(RANSOM[(f // 5) % 3])
    elif seg == 1:
        pill(L, "o vídeo que eu postei 👇".replace(" 👇", ""), 170, F(800, 46), (255, 255, 255), (20, 20, 20))
        if lt > 3.4:
            put_card(L, C_LIST, st + 3.4, t, cy=1170)
            pill(L, "o produto que eu vinculei", 1040, F(800, 40), (30, 150, 90), (255, 255, 255), int(255 * min(1, (lt - 3.4) / .25)))
    elif seg == 2: put_card(L, C_PTS, st, t)
    elif seg == 3:
        put_card(L, C_MOT, st, t, cy=800, hl=[(HL_FONE, st + 2.3, 1.2), (HL_PULS, st + 6.0, 1.0)])
    elif seg == 4:
        pop_word(L, "FONE", "🎧", W / 2, 620, st + 0.0, t, (255, 90, 90))
        pop_word(L, "PULSEIRA", "⌚", W / 2, 800, st + 0.55, t, (255, 200, 60))
        pop_word(L, "CAMISOLA?", "👗", W / 2, 980, st + 1.2, t, (255, 255, 255))
    elif seg == 5: put_card(L, C_REC, st, t, cy=800)
    elif seg == 6: put_card(L, C_INT, st, t, cy=820)
    elif seg == 7:
        if lt > meta["dur"][7] - 1.6:
            k = min(1.0, (lt - (meta["dur"][7] - 1.6)) / .2)
            fnt = F(900, int(96 * (1.3 - .3 * k)))
            ImageDraw.Draw(L).text((W / 2, 760), "ABSURDO.", font=fnt, fill=(255, 255, 255), stroke_width=8, stroke_fill=WINE, anchor="mm")
    elif seg == 8:
        e = emoji("💬", 120); b = 22 * abs(math.sin(math.pi * 1.6 * lt))
        L.alpha_composite(emoji("👉", 110), (int(800 + b), 1190))
        pill(L, "me conta nos comentários", 1040, F(800, 46), (255, 255, 255), (20, 20, 20))
    # legenda da narração (digitando no ritmo da fala)
    if seg < len(SEG) and SEG[seg][0] <= t <= SEG[seg][1] + GAP:
        text = meta["lines"][seg]; lines = wrap(text, SUB, 940)
        n = int(len(text) * min(1.0, (t - SEG[seg][0]) / max(0.5, meta["dur"][seg] * 0.9)))
        outlined(L, lines, SUB_Y if seg not in (0,) else 360, SUB, n)
    L.save(os.path.join(OUT, f"{f:04d}.png"), compress_level=1)
print("frames", f + 1, "total", TOTAL, "starts", starts)
