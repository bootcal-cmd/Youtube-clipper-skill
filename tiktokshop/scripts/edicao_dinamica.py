"""Vestido tubinho — edição dinâmica: câmera lenta, aceleração com rastro, revelação das costas,
tela dividida em 3 e zooms acompanhando o movimento. Frames RGB no stdout; eventos de som em dyn_sfx.json."""
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
import os, sys, math, re, json, random

V = os.path.dirname(os.path.abspath(__file__)); S = os.path.dirname(V)
W, H, FPS = 1080, 1920, 30
NSRC = 284
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

# --- linha do tempo (duração de saída, função que devolve o quadro) ---
SEGS = []
def seg(dur, fn): SEGS.append((dur, fn))

def A(lt):  # hook em câmera lenta
    img = zoom(fr(0.0 + lt * 0.5), 1.0 + 0.06 * lt).convert("RGBA")
    rich(img, "espera ela virar… 😳", W / 2, 230, F(900, 74), n=int(lt * 24)); return img
seg(1.6, A)
def B(lt):  # aceleração com rastro
    p = lt / 0.8; st = 0.8 + (3.1 - 0.8) * ease(p); return zoom(blurred(st, 3), 1.08 - 0.08 * p).convert("RGBA")
seg(0.8, B)
def C(lt):  # revelação das costas em câmera lenta
    img = zoom(fr(3.1 + lt * 0.5), 1.0 + 0.22 * ease(lt / 0.5), .5, .5).convert("RGBA")
    if lt < 0.1: img.alpha_composite(Image.new("RGBA", img.size, (255, 255, 255, int(230 * (1 - lt / .1)))))
    pop_text(img, "COSTAS NUAS 🔥", 0.12, lt, y=1250); return img
seg(2.0, C)
def Dd(lt):  # tela dividida em 3 faixas
    img = Image.new("RGBA", (W, H), (0, 0, 0, 255)); bh = H // 3
    parts = [(0.3 + lt, .42, "frente"), (2.05 + lt * .25, .45, "lado"), (3.05 + lt * .35, .50, "costas")]
    for i, (st, fy, lab) in enumerate(parts):
        k = ease((lt - i * 0.12) / 0.3)
        if k <= 0: continue
        f_ = fr(st); band = f_.crop((0, int(fy * H - bh / 2), W, int(fy * H + bh / 2)))
        x = int((1 - k) * (W if i % 2 == 0 else -W)); img.paste(band, (x, i * bh))
        if k > .9: pill(img, lab, W - 140, i * bh + 30, 40)
    d = ImageDraw.Draw(img)
    for i in (1, 2): d.rectangle((0, i * bh - 4, W, i * bh + 4), fill="white")
    return img
seg(1.7, Dd)
def E(lt):  # volta de frente com zooms acompanhando
    st = 5.5 + lt * 0.8
    if lt < 1.4: z, fx, fy, lab = 1.0 + 0.6 * ease(lt / .25), .48, .36, "gola alta ✨"
    else: z, fx, fy, lab = 1.0 + 0.55 * ease((lt - 1.4) / .25), .48, .52, "decote drapeado 🖤"
    img = zoom(fr(st), z, fx, fy).convert("RGBA")
    if (lt % 1.4) > .3: pill(img, lab, W / 2, 1380, 54)
    return img
seg(2.8, E)
def Fn(lt):  # final: ela aponta + CTA
    st = min(9.45, 7.8 + lt * 0.7); img = zoom(fr(st), 1.1 - 0.1 * ease(lt / .4)).convert("RGBA")
    if lt > 0.4: cta(img, lt - 0.4)
    return img
seg(2.6, Fn)

TOTAL = sum(d for d, _ in SEGS); starts = []; a = 0
for d, _ in SEGS: starts.append(a); a += d
out = sys.stdout.buffer
for f in range(int(TOTAL * FPS)):
    t = f / FPS; i = max(k for k, s in enumerate(starts) if t >= s - 1e-6)
    lt = t - starts[i]
    punch = 1 + 0.06 * max(0.0, 1 - lt / 0.12) if i > 0 else 1   # micro zoom de impacto a cada troca
    img = SEGS[i][1](lt)
    if punch > 1: img = zoom(img.convert("RGB"), punch).convert("RGBA")
    out.write(img.convert("RGB").tobytes())
json.dump({"total": TOTAL, "starts": starts}, open(os.path.join(V, "dyn_sfx.json"), "w"))
