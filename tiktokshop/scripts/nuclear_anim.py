"""Animação 2D plana + narração: sobrevivência a um ataque nuclear (regras: ENTRE, FIQUE, SINTONIZE).
uso: python3 anim.py <1|2>   -> escreve frames RGB no stdout e <pasta>/timeline.json
Personagem, cenários e paleta são originais."""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os, sys, re, math, json, random
import numpy as np, soundfile as sf

D = os.path.dirname(os.path.abspath(__file__)); S = os.path.dirname(D)
P = int(sys.argv[1]); PD = os.path.join(D, f"p{P}")
W, H, FPS = 1080, 1920, 30
def F(w, s): return ImageFont.truetype(os.path.join(S, f"mont{w}.ttf"), s)
MONO = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 90)
def ease(p): p = min(1.0, max(0.0, p)); return p * p * (3 - 2 * p)
def lerp(a, b, p): return a + (b - a) * p

# paleta
NAVY = (14, 18, 38); WALL = (40, 50, 88); FLOOR = (26, 30, 56); ORANGE = (255, 140, 40); RED = (232, 56, 56)
YEL = (255, 206, 70); SKIN = (238, 188, 148); HOOD = (214, 62, 62); PANTS = (58, 68, 112); WHITE = (255, 255, 255)
GREEN = (60, 200, 110); BLUE = (70, 150, 230); GRAY = (120, 128, 150); DARK = (22, 26, 48)

# ---------------- roteiro e tempos ----------------
LINES = [l.strip() for l in open(os.path.join(PD, "lines.txt"), encoding="utf-8") if l.strip()]
def process(i):
    a, sr = sf.read(os.path.join(PD, "n", f"{i}.wav"), dtype="float32")
    if a.ndim > 1: a = a.mean(1)
    fr = int(sr * 0.02); n = len(a) // fr
    e = np.sqrt((a[: n * fr].reshape(n, fr) ** 2).mean(1)); loud = e > 0.012
    idx = np.where(loud)[0]
    if len(idx) == 0: return a, sr
    a = a[max(0, idx[0] * fr - int(.05 * sr)): (idx[-1] + 1) * fr + int(.08 * sr)]
    # limita pausas internas a 0,5 s
    n = len(a) // fr; e = np.sqrt((a[: n * fr].reshape(n, fr) ** 2).mean(1)); quiet = e < 0.012
    out, k = [], 0
    while k < n:
        if quiet[k]:
            j = k
            while j < n and quiet[j]: j += 1
            keep = min(j - k, 25)  # 25 * 20 ms = 0,5 s
            out.append(a[k * fr:(k + keep) * fr]); k = j
        else:
            j = k
            while j < n and not quiet[j]: j += 1
            out.append(a[k * fr:j * fr]); k = j
    return np.concatenate(out), sr
CLIPS = [process(i) for i in range(len(LINES))]
SR = CLIPS[0][1]; DUR = [len(a) / sr for a, sr in CLIPS]
LEAD, GAP, TAIL, END = 0.5, 0.45, 0.8, 3.2
START = []; t = LEAD
for d in DUR: START.append(t); t += d + GAP
NARR_END = START[-1] + DUR[-1]; SCENE_END = NARR_END + TAIL; TOTAL = SCENE_END + END
BOUND = [0.0] + [s - 0.2 for s in START[1:]] + [SCENE_END]

# legendas palavra a palavra
DANGER = {"erro", "pior", "bate", "alerta", "poeira"}
def parse(line):
    ws = []
    for tok in line.split():
        kw = tok.startswith("*") or tok.endswith("*") or ("*" in tok)
        ws.append((tok.replace("*", ""), kw))
    return ws
def chunks(line, start, dur):
    ws = parse(line); wt = [len(w) + 2 for w, _ in ws]; tot = sum(wt); acc = 0; times = []
    for w, k in zip(ws, wt): times.append(start + dur * 0.96 * acc / tot); acc += k
    groups, cur = [], []
    for i, (w, kw) in enumerate(ws):
        if cur and (len(cur) >= 3 or sum(len(x[0]) for x in cur) + len(w) > 17): groups.append(cur); cur = []
        cur.append((w, kw, times[i]))
    if cur: groups.append(cur)
    return [(g[0][2], g) for g in groups]
SUBS = []
for i, ln in enumerate(LINES):
    cs = chunks(ln, START[i], DUR[i])
    for j, (t0, g) in enumerate(cs):
        t1 = cs[j + 1][0] if j + 1 < len(cs) else START[i] + DUR[i] + 0.25
        SUBS.append((t0, t1, g))
def draw_sub(img, t):
    for t0, t1, g in SUBS:
        if t0 <= t < t1:
            words = [w.upper().strip(".,:;!?") if False else w.upper() for w, _, _ in g]
            text = " ".join(words); size = 96
            while F(900, size).getlength(text) > 960 and size > 50: size -= 4
            font = F(900, size); d = ImageDraw.Draw(img); x = (W - font.getlength(text)) / 2; y = 1360
            pop = 1 + 0.08 * max(0, 1 - (t - t0) / 0.12)
            for (w, kw, _), ww in zip(g, words):
                col = (RED if w.lower().strip(".,:;!?") in DANGER else YEL) if kw else WHITE
                d.text((x, y), ww, font=font, fill=col, stroke_width=9, stroke_fill=(0, 0, 0))
                x += font.getlength(ww + " ")
            return

# ---------------- desenho de personagem e cenário ----------------
def rr(d, box, r, fill, outline=None, w=0): d.rounded_rectangle(box, r, fill=fill, outline=outline, width=w)
def person(d, cx, fy, sc=1.0, t=0.0, pose="stand", hood=HOOD, worried=True, back=False):
    s = sc; bob = 4 * math.sin(t * 5) * s if pose == "walk" else 0
    leg = 22 * math.sin(t * 8) * s if pose == "walk" else 0
    # pernas
    rr(d, (cx - 42 * s, fy - 190 * s, cx - 6 * s + leg, fy), 10, PANTS); rr(d, (cx + 6 * s - leg, fy - 190 * s, cx + 42 * s, fy), 10, PANTS)
    rr(d, (cx - 50 * s + leg, fy - 14 * s, cx - 2 * s + leg, fy + 6 * s), 8, (30, 30, 40)); rr(d, (cx + 2 * s - leg, fy - 14 * s, cx + 50 * s - leg, fy + 6 * s), 8, (30, 30, 40))
    ty = fy - 345 * s + bob
    rr(d, (cx - 62 * s, ty, cx + 62 * s, ty + 175 * s), 26 * s, hood)
    # braços
    aw = int(24 * s)
    if pose == "alarm":
        d.line((cx - 60 * s, ty + 30 * s, cx - 110 * s, ty - 50 * s), fill=hood, width=aw); d.line((cx + 60 * s, ty + 30 * s, cx + 110 * s, ty - 50 * s), fill=hood, width=aw)
        for sx in (-110, 110): d.ellipse((cx + sx * s - 16 * s, ty - 66 * s, cx + sx * s + 16 * s, ty - 34 * s), fill=SKIN)
    elif pose == "point":
        d.line((cx + 60 * s, ty + 40 * s, cx + 170 * s, ty + 20 * s), fill=hood, width=aw); d.ellipse((cx + 160 * s, ty + 4 * s, cx + 190 * s, ty + 34 * s), fill=SKIN)
        d.line((cx - 60 * s, ty + 40 * s, cx - 72 * s, ty + 150 * s), fill=hood, width=aw)
    elif pose == "ear":
        d.line((cx + 60 * s, ty + 40 * s, cx + 92 * s, ty - 60 * s), fill=hood, width=aw); d.ellipse((cx + 78 * s, ty - 100 * s, cx + 108 * s, ty - 70 * s), fill=SKIN)
        d.line((cx - 60 * s, ty + 40 * s, cx - 72 * s, ty + 150 * s), fill=hood, width=aw)
    else:
        for sx in (-1, 1): d.line((cx + sx * 60 * s, ty + 40 * s, cx + sx * 72 * s, ty + 150 * s + (8 * math.sin(t * 8 + sx) * s if pose == "walk" else 0)), fill=hood, width=aw)
        for sx in (-1, 1): d.ellipse((cx + sx * 72 * s - 14 * s, ty + 142 * s, cx + sx * 72 * s + 14 * s, ty + 170 * s), fill=SKIN)
    # cabeça
    hy = ty - 60 * s
    d.ellipse((cx - 58 * s, hy - 58 * s, cx + 58 * s, hy + 58 * s), fill=SKIN)
    d.pieslice((cx - 62 * s, hy - 66 * s, cx + 62 * s, hy + 50 * s), 180, 360, fill=(48, 34, 30))
    if not back:
        for ex in (-20, 20):
            d.ellipse((cx + ex * s - 11 * s, hy - 6 * s, cx + ex * s + 11 * s, hy + 16 * s), fill=WHITE); d.ellipse((cx + ex * s - 5 * s, hy, cx + ex * s + 5 * s, hy + 12 * s), fill=(20, 20, 30))
        if worried:
            d.line((cx - 34 * s, hy - 16 * s, cx - 10 * s, hy - 24 * s), fill=(48, 34, 30), width=int(6 * s)); d.line((cx + 34 * s, hy - 16 * s, cx + 10 * s, hy - 24 * s), fill=(48, 34, 30), width=int(6 * s))
        d.arc((cx - 16 * s, hy + 26 * s, cx + 16 * s, hy + 46 * s), 200, 340, fill=(120, 60, 50), width=int(5 * s))
    else:
        d.ellipse((cx - 58 * s, hy - 58 * s, cx + 58 * s, hy + 58 * s), fill=(48, 34, 30))

def sky(img, top, bot, y0=0, y1=H):
    d = ImageDraw.Draw(img)
    for y in range(int(y0), int(y1), 6):
        p = (y - y0) / max(1, y1 - y0); d.rectangle((0, y, W, y + 6), fill=tuple(int(lerp(a, b, p)) for a, b in zip(top, bot)))
def skyline(d, base_y, col, seed=3, x0=0, x1=W, scale=1.0):
    rnd = random.Random(seed); x = x0
    while x < x1:
        w = rnd.randint(70, 150); h = int(rnd.randint(120, 380) * scale); d.rectangle((x, base_y - h, x + w, base_y), fill=col)
        for wy in range(base_y - h + 20, base_y - 20, 40):
            for wx in range(x + 12, x + w - 16, 30):
                if rnd.random() < .35: d.rectangle((wx, wy, wx + 12, wy + 18), fill=(255, 220, 130))
        x += w + rnd.randint(0, 12)
def glow(img, cx, cy, r, col, a):
    g = Image.new("RGBA", img.size, (0, 0, 0, 0)); ImageDraw.Draw(g).ellipse((cx - r, cy - r, cx + r, cy + r), fill=col + (a,))
    img.alpha_composite(g.filter(ImageFilter.GaussianBlur(r / 2)))
def pill(img, text, cx, y, size=44, bg=(255, 255, 255), fg=(20, 20, 30)):
    f = F(800, size); w = f.getlength(text); d = ImageDraw.Draw(img)
    d.rounded_rectangle((cx - w / 2 - 28, y, cx + w / 2 + 28, y + size + 34), 40, fill=bg); d.text((cx - w / 2, y + 14), text, font=f, fill=fg)
def label(img, text, cx, y, lt, t0=0.3, size=44, bg=YEL, fg=(20, 20, 30)):
    k = ease((lt - t0) / .25)
    if k > 0: pill(img, text, cx, int(y + 20 * (1 - k)), size, bg, fg)
def cross(d, cx, cy, r, col=RED, w=22):
    d.line((cx - r, cy - r, cx + r, cy + r), fill=col, width=w); d.line((cx - r, cy + r, cx + r, cy - r), fill=col, width=w)
def check(d, cx, cy, r, col=GREEN, w=20):
    d.line((cx - r, cy, cx - r * .3, cy + r * .7), fill=col, width=w); d.line((cx - r * .3, cy + r * .7, cx + r, cy - r * .7), fill=col, width=w)

# ---------------- cenas ----------------
SC = {1: [], 2: []}
def scene(p):
    def deco(fn): SC[p].append(fn); return fn
    return deco

@scene(1)
def s1_alert(lt, dur):
    img = Image.new("RGBA", (W, H), WALL + (255,)); d = ImageDraw.Draw(img)
    d.rectangle((0, 1240, W, H), fill=FLOOR)
    sky(img, (10, 14, 40), (40, 40, 90), 330, 760); d = ImageDraw.Draw(img)
    skyline(d, 760, (16, 18, 40), 5, 120, 520, .6)
    d.rectangle((120, 330, 520, 760), outline=(150, 160, 200), width=14); d.line((320, 330, 320, 760), fill=(150, 160, 200), width=10); d.line((120, 545, 520, 545), fill=(150, 160, 200), width=10)
    for (sx, sy) in ((200, 400), (420, 450), (350, 380), (160, 480)): d.ellipse((sx - 3, sy - 3, sx + 3, sy + 3), fill=WHITE)
    # relógio de LED
    rr(d, (640, 380, 980, 520), 18, (14, 14, 22)); d.text((672, 394), "03:00", font=MONO, fill=ORANGE)
    # cama e criado-mudo
    rr(d, (40, 1040, 780, 1290), 30, (70, 92, 150)); rr(d, (40, 1010, 300, 1130), 40, (200, 205, 230))
    rr(d, (780, 1030, 1010, 1290), 14, (60, 44, 40))
    # pessoa sentada na cama (levantando assustada)
    rise = ease(lt / .6); person(d, 330, 1090 + 30 * (1 - rise), 0.95, lt, "alarm" if lt > .7 else "stand")
    # celular tocando
    sh = 6 * math.sin(lt * 40) if int(lt * 3) % 2 == 0 else 0
    rr(d, (820 + sh, 700, 980 + sh, 1030), 24, (10, 10, 16)); pulse = 0.5 + 0.5 * math.sin(lt * 10)
    rr(d, (834 + sh, 722, 966 + sh, 1008), 14, (int(150 + 100 * pulse), 20, 20)); d.text((866 + sh, 800), "!", font=F(900, 150), fill=WHITE)
    d.text((842 + sh, 940), "ALERTA", font=F(900, 28), fill=WHITE)
    for k in range(3):  # ondas do toque
        p = ((lt * 1.2) - k * .33) % 1; r = 70 + 230 * p; ov = Image.new("RGBA", img.size, (0, 0, 0, 0)); ImageDraw.Draw(ov).ellipse((900 - r, 860 - r, 900 + r, 860 + r), outline=RED + (int(200 * (1 - p)),), width=10); img.alpha_composite(ov)
    ov = Image.new("RGBA", img.size, RED + (int(28 + 30 * pulse),)); img.alpha_composite(ov)
    return img

@scene(1)
def s1_cars(lt, dur):
    img = Image.new("RGBA", (W, H), NAVY + (255,)); sky(img, (16, 20, 48), (70, 50, 80), 0, 900); d = ImageDraw.Draw(img)
    skyline(d, 900, (18, 20, 42), 8, 0, W, 1.2)
    d.rectangle((0, 900, W, 1250), fill=(44, 46, 62)); d.rectangle((0, 1236, W, 1250), fill=(120, 126, 150))
    for x in range(0, W, 140): d.rectangle((x, 1070, x + 70, 1082), fill=(220, 220, 90))
    cols = [(230, 80, 80), (80, 150, 230), (240, 190, 60), (90, 190, 120), (200, 110, 220), (240, 240, 240), (255, 140, 40)]
    x = -60
    for i in range(6):
        c = cols[i % len(cols)]; cy = 1130 + (6 if i % 2 else 0) + 3 * math.sin(lt * 20 + i)
        rr(d, (x, cy, x + 250, cy + 90), 24, c); rr(d, (x + 50, cy - 56, x + 200, cy + 8), 20, c); rr(d, (x + 64, cy - 42, x + 120, cy), 8, (170, 210, 240)); rr(d, (x + 130, cy - 42, x + 188, cy), 8, (170, 210, 240))
        d.ellipse((x + 34, cy + 56, x + 94, cy + 116), fill=(20, 20, 26)); d.ellipse((x + 156, cy + 56, x + 216, cy + 116), fill=(20, 20, 26))
        d.rectangle((x + 244, cy + 22, x + 256, cy + 44), fill=(255, 60, 60) if int(lt * 4) % 2 == 0 else (120, 30, 30))
        x += 230
    glow(img, 540, 1160, 380, RED, 60)
    d = ImageDraw.Draw(img)
    if lt > 1.0:
        k = ease((lt - 1.0) / .2); ov = Image.new("RGBA", img.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov); cross(od, 540, 700, 190 * (1.4 - .4 * k), RED + (int(255 * k),), 40); img.alpha_composite(ov)
    label(img, "SAIR DE CARRO", 540, 250, lt, .3, 50, RED, WHITE)
    return img

@scene(1)
def s1_jam(lt, dur):
    img = Image.new("RGBA", (W, H), (30, 32, 46, 255)); d = ImageDraw.Draw(img)
    d.rectangle((90, 0, 990, H), fill=(50, 52, 68))
    for y in range(0, H, 90): d.rectangle((330, y, 344, y + 46), fill=(210, 210, 90)); d.rectangle((736, y, 750, y + 46), fill=(210, 210, 90))
    cols = [(230, 80, 80), (80, 150, 230), (240, 190, 60), (90, 190, 120), (200, 110, 220), (240, 240, 240)]
    rnd = random.Random(9)
    for lane, lx in enumerate((130, 480, 810)):
        y = 140
        while y < 1250:
            h = rnd.randint(150, 190); c = cols[rnd.randint(0, 5)]
            rr(d, (lx, y, lx + 130, y + h), 26, c); rr(d, (lx + 14, y + 28, lx + 116, y + h - 50), 16, (36, 40, 60))
            on = int(lt * 3 + lane + y // 100) % 2 == 0
            d.rectangle((lx + 8, y + h - 14, lx + 36, y + h - 4), fill=(255, 70, 70) if on else (120, 30, 30)); d.rectangle((lx + 94, y + h - 14, lx + 122, y + h - 4), fill=(255, 70, 70) if on else (120, 30, 30))
            y += h + 26
    # velocímetro
    rr(d, (240, 480, 840, 780), 40, (14, 16, 30), RED, 8); d.text((540 - F(900, 180).getlength("0") / 2 - 130, 500), "0", font=F(900, 220), fill=RED); d.text((540 - 30, 580), "km/h", font=F(900, 70), fill=WHITE)
    d.arc((290, 520, 450, 680), 120, 420, fill=(90, 90, 110), width=8)
    pill(img, "ESTRADAS TRAVADAS", 540, 250, 52, RED, WHITE)
    return img

@scene(1)
def s1_rule(lt, dur):
    img = Image.new("RGBA", (W, H), (28, 34, 70, 255)); d = ImageDraw.Draw(img)
    d.rectangle((0, 1250, W, H), fill=FLOOR)
    k = ease(lt / .35); r = 150 * k
    d.ellipse((540 - r, 330 - r, 540 + r, 330 + r), fill=YEL); d.text((540 - F(900, 190 * k + 1).getlength("1") / 2, 330 - 108 * k), "1", font=F(900, int(190 * k) + 1), fill=(20, 20, 30))
    t2 = ease((lt - .25) / .3); f = F(900, 170); d.text((540 - f.getlength("ENTRE") / 2 + 300 * (1 - t2), 520), "ENTRE", font=f, fill=WHITE, stroke_width=8, stroke_fill=(0, 0, 0))
    # porta e pessoa entrando
    rr(d, (640, 800, 960, 1250), 14, (92, 60, 44)); d.rectangle((660, 820, 940, 1250), fill=(10, 10, 16)); rr(d, (880, 1040, 912, 1060), 8, YEL)
    glow(img, 800, 1030, 240, YEL, 40); d = ImageDraw.Draw(img)
    px = lerp(120, 770, ease((lt - .4) / 1.8)); sc = lerp(1.0, 0.75, ease((lt - 1.6) / .6))
    if lt < 2.4: person(d, px, 1250, sc, lt, "walk")
    # seta
    b = 14 * abs(math.sin(lt * 5)); d.polygon([(560, 690 + b), (640, 690 + b), (640, 650 + b), (720, 720 + b), (640, 790 + b), (640, 750 + b), (560, 750 + b)], fill=ORANGE)
    return img

@scene(1)
def s1_building(lt, dur):
    img = Image.new("RGBA", (W, H), (22, 26, 56, 255)); sky(img, (16, 20, 46), (60, 56, 100), 0, 1300); d = ImageDraw.Draw(img)
    d.rectangle((0, 1180, W, H), fill=(36, 30, 40))
    bx0, bx1, top = 250, 830, 280
    for fl in range(6):  # 5 andares + subsolo
        y0 = top + fl * 150; sub = fl == 5
        d.rectangle((bx0, y0, bx1, y0 + 146), fill=(70, 62, 66) if sub else (96, 108, 150))
        if not sub:
            for wx in (bx0 + 24, bx1 - 124): d.rectangle((wx, y0 + 30, wx + 100, y0 + 116), fill=(255, 220, 130) if (fl % 2 == 0) else (200, 190, 140))
        d.line((bx0, y0 + 148, bx1, y0 + 148), fill=(30, 34, 60), width=4)
    # janelas marcadas com X
    for fl in range(5):
        if lt > 0.6 + fl * .18:
            for wx in (bx0 + 74, bx1 - 74): cross(d, wx, top + fl * 150 + 73, 26, RED, 10)
    d.rectangle((bx0 - 14, top - 14, bx1 + 14, top), fill=(60, 66, 100))
    # destaque do andar de baixo, no centro
    pu = 0.5 + 0.5 * math.sin(lt * 6); y0 = top + 5 * 150
    glow(img, 540, y0 + 73, 230, GREEN, int(70 + 50 * pu)); d = ImageDraw.Draw(img)
    rr(d, (bx0 + 150, y0 + 14, bx1 - 150, y0 + 134), 20, (30, 90, 60), GREEN, 8)
    person(d, 540, y0 + 128, 0.32, lt, "stand", worried=False)
    b = 16 * abs(math.sin(lt * 5)); ay = y0 - 140 + b; d.polygon([(540, ay + 100), (480, ay + 30), (520, ay + 30), (520, ay - 40), (560, ay - 40), (560, ay + 30), (600, ay + 30)], fill=GREEN)
    label(img, "ANDAR MAIS BAIXO", 540, 150, lt, .2, 50, GREEN, (10, 30, 20)); label(img, "NO CENTRO", 540, 1240, lt, .5, 44, YEL)
    return img

@scene(1)
def s1_walls(lt, dur):
    img = Image.new("RGBA", (W, H), (20, 24, 50, 255)); d = ImageDraw.Draw(img)
    cx, cy = 540, 760
    # camadas de parede (concreto)
    for i, (r, c) in enumerate(((480, (120, 124, 138)), (370, (96, 100, 114)), (260, (74, 78, 92)))): d.rectangle((cx - r, cy - r * .8, cx + r, cy + r * .8), fill=c)
    for i in range(0, 960, 40): d.line((60 + i, 160, 60 + i - 120, 1360), fill=(0, 0, 0), width=1) if False else None
    d.rectangle((cx - 180, cy - 150, cx + 180, cy + 150), fill=(30, 36, 70)); person(d, cx, cy + 148, 0.55, lt, "stand", worried=False)
    # radiação (flechas ondulantes) que morre na parede
    for side in (-1, 1):
        for k in range(4):
            p = ((lt * .7) + k * .27) % 1; x0 = cx + side * (640 - 400 * p); a = max(0, 1 - max(0, p - .1) * 3.2)
            if a > 0:
                ov = Image.new("RGBA", img.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov); yy = 460 + k * 130
                pts = [(x0 + side * j * 8, yy + 12 * math.sin(j + lt * 8)) for j in range(0, 14)]; od.line(pts, fill=ORANGE + (int(230 * a),), width=10); img.alpha_composite(ov)
    d = ImageDraw.Draw(img)
    pill(img, "CONCRETO", 540, 1100, 56, (190, 196, 214), (20, 20, 40)); label(img, "MENOS RADIAÇÃO", 540, 1200, lt, .6, 46, GREEN, (10, 30, 20))
    return img

@scene(1)
def s1_sky(lt, dur):
    img = Image.new("RGBA", (W, H), NAVY + (255,)); d = ImageDraw.Draw(img)
    p = ease(lt / dur); sky(img, (int(lerp(20, 140, p)), int(lerp(24, 40, p)), int(lerp(60, 50, p))), (int(lerp(60, 255, p)), int(lerp(50, 120, p)), int(lerp(110, 40, p))), 180, 1150); d = ImageDraw.Draw(img)
    skyline(d, 1150, (14, 12, 24), 4, 0, W, 1.5)
    d.rectangle((120, 180, 960, 1180), outline=(40, 44, 70), width=34); d.line((540, 180, 540, 1180), fill=(40, 44, 70), width=22); d.line((120, 680, 960, 680), fill=(40, 44, 70), width=22)
    d.rectangle((0, 1180, W, H), fill=(18, 20, 36)); person(d, 330, 1330, 1.1, lt, "stand", back=True)
    glow(img, 540, 900, 520, ORANGE, int(40 + 50 * p))
    return img

SC_END = {1: ("PARTE 2", "o que fazer nas próximas 48 horas?", "SEGUE PRA NÃO PERDER"), 2: ("VOCÊ ABRIRIA A PORTA?", "comenta SIM ou NÃO", "SEGUE O PERFIL")}

@scene(2)
def s2_dust(lt, dur):
    img = Image.new("RGBA", (W, H), NAVY + (255,)); sky(img, (60, 60, 74), (150, 110, 84), 0, 1150); d = ImageDraw.Draw(img)
    skyline(d, 1150, (26, 24, 34), 6, 0, W, 1.4)
    rnd = random.Random(2)
    for i in range(90):  # partículas caindo
        x = rnd.uniform(0, W); sp = rnd.uniform(90, 220); y = (rnd.uniform(0, H) + sp * lt) % 1250; r = rnd.uniform(3, 9)
        d.ellipse((x + 20 * math.sin(lt + i) - r, y - r, x + 20 * math.sin(lt + i) + r, y + r), fill=(210, 205, 190))
    d.rectangle((0, 1150, W, H), fill=(26, 28, 46)); d.rectangle((90, 240, 990, 1160), outline=(14, 16, 30), width=46); d.line((540, 240, 540, 1160), fill=(14, 16, 30), width=26)
    label(img, "POEIRA RADIOATIVA", 540, 150, lt, .4, 54, ORANGE, (20, 20, 30))
    return img

@scene(2)
def s2_clock(lt, dur):
    img = Image.new("RGBA", (W, H), (20, 24, 52, 255)); d = ImageDraw.Draw(img)
    k = ease(lt / .35); r = 150 * k; d.ellipse((540 - r, 280 - r, 540 + r, 280 + r), fill=YEL); d.text((540 - F(900, 190 * k + 1).getlength("2") / 2, 280 - 108 * k), "2", font=F(900, int(190 * k) + 1), fill=(20, 20, 30))
    t2 = ease((lt - .25) / .3); f = F(900, 170); d.text((540 - f.getlength("FIQUE") / 2 + 300 * (1 - t2), 470), "FIQUE", font=f, fill=WHITE, stroke_width=8, stroke_fill=(0, 0, 0))
    cx, cy, R = 540, 960, 280; d.ellipse((cx - R, cy - R, cx + R, cy + R), fill=(16, 18, 36), outline=(220, 224, 240), width=12)
    prog = ease(lt / (dur - .3)); d.pieslice((cx - R + 24, cy - R + 24, cx + R - 24, cy + R - 24), -90, -90 + 360 * prog, fill=(190, 50, 50))
    for i in range(12): a = math.radians(i * 30); d.line((cx + math.cos(a) * (R - 18), cy + math.sin(a) * (R - 18), cx + math.cos(a) * R, cy + math.sin(a) * R), fill=WHITE, width=6)
    a = math.radians(-90 + 360 * prog * 4); d.line((cx, cy, cx + math.cos(a) * 210, cy + math.sin(a) * 210), fill=WHITE, width=10)
    d.ellipse((cx - 18, cy - 18, cx + 18, cy + 18), fill=WHITE); f2 = F(900, 100); d.text((cx - f2.getlength("48h") / 2, cy + 100), "48h", font=f2, fill=WHITE, stroke_width=6, stroke_fill=(0, 0, 0))
    return img

@scene(2)
def s2_seal(lt, dur):
    img = Image.new("RGBA", (W, H), WALL + (255,)); d = ImageDraw.Draw(img); d.rectangle((0, 1250, W, H), fill=FLOOR)
    # janela
    sky(img, (70, 70, 90), (160, 120, 90), 360, 960); d = ImageDraw.Draw(img); d.rectangle((120, 360, 520, 960), outline=(190, 196, 220), width=16); d.line((320, 360, 320, 960), fill=(190, 196, 220), width=12)
    for k, (x0, y0, x1, y1) in enumerate(((120, 360, 520, 960), (520, 360, 120, 960), (320, 360, 320, 960), (120, 660, 520, 660))):  # fitas
        p = ease((lt - 1.5 - k * .25) / .3)
        if p > 0: d.line((x0, y0, x0 + (x1 - x0) * p, y0 + (y1 - y0) * p), fill=(210, 214, 226), width=22)
    # ar-condicionado
    rr(d, (600, 380, 1010, 560), 26, (226, 230, 240)); d.rectangle((620, 500, 990, 520), fill=(170, 176, 196))
    on = lt < 1.0
    for k in range(3):
        p = ((lt * 1.4) + k * .33) % 1
        if on: d.line((650 + k * 120, 580 + 40 * p, 650 + k * 120, 650 + 80 * p), fill=(150, 210, 255), width=8)
    d.ellipse((900, 400, 980, 480), fill=GREEN if on else RED)
    if not on:
        cr = Image.new("RGBA", img.size, (0, 0, 0, 0)); cross(ImageDraw.Draw(cr), 805, 470, 100, RED + (int(255 * ease((lt - 1.0) / .2)),), 24); img.alpha_composite(cr)
    person(d, 760, 1250, 0.95, lt, "point" if lt > 1.2 else "stand")
    label(img, "SEM AR DE FORA", 540, 200, lt, .4, 50, YEL)
    return img

@scene(2)
def s2_clothes(lt, dur):
    img = Image.new("RGBA", (W, H), (36, 44, 80, 255)); d = ImageDraw.Draw(img); d.rectangle((0, 1250, W, H), fill=FLOOR)
    if lt < dur * .5:
        p = ease(lt / (dur * .4)); d.rectangle((60, 300, 460, 360), fill=(0, 0, 0, 0)) if False else None
        # casaco indo para o saco
        jx = lerp(260, 740, p); jy = lerp(760, 1020, p) - 100 * math.sin(math.pi * p)
        rr(d, (jx - 90, jy - 100, jx + 90, jy + 110), 30, HOOD); d.line((jx - 90, jy - 60, jx - 150, jy + 80), fill=HOOD, width=44); d.line((jx + 90, jy - 60, jx + 150, jy + 80), fill=HOOD, width=44)
        rr(d, (620, 900, 880, 1250), 36, (60, 70, 100), (180, 190, 220), 6); d.text((690, 1040), "LIXO", font=F(900, 60), fill=(220, 224, 240))
        label(img, "ROUPA DE FORA", 540, 200, lt, .3, 50, YEL); person(d, 260, 1250, 0.9, lt, "stand")
    else:
        lt2 = lt - dur * .5
        d.rectangle((420, 1250, 700, 1262), fill=(60, 70, 100)); d.rectangle((680, 300, 700, 700), fill=(190, 196, 220)); d.rectangle((520, 280, 700, 330), fill=(190, 196, 220)); d.ellipse((470, 320, 580, 370), fill=(150, 156, 180))
        for i in range(34):
            q = ((lt2 * 1.6) + i * .037) % 1; x = 470 + (i * 53) % 110; y = 360 + q * 880; d.ellipse((x - 4, y - 8, x + 4, y + 8), fill=(120, 190, 255))
        person(d, 540, 1250, 0.95, lt2, "stand", worried=False); label(img, "TOME BANHO", 540, 200, lt2, .2, 50, BLUE, WHITE)
    return img

@scene(2)
def s2_supplies(lt, dur):
    img = Image.new("RGBA", (W, H), (44, 38, 56, 255)); d = ImageDraw.Draw(img); d.rectangle((0, 1250, W, H), fill=FLOOR)
    for sy in (560, 900):
        d.rectangle((120, sy, 960, sy + 24), fill=(120, 84, 60)); d.rectangle((150, sy + 24, 170, sy + 90), fill=(90, 60, 44)); d.rectangle((910, sy + 24, 930, sy + 90), fill=(90, 60, 44))
    for i in range(5):  # garrafas
        x = 170 + i * 110; rr(d, (x, 380, x + 70, 560), 18, (120, 190, 240)); d.rectangle((x + 20, 350, x + 50, 384), fill=(240, 240, 250))
        if lt > .5 + i * .15: check(d, x + 35, 470, 22, GREEN, 12)
    for i in range(4):  # latas
        x = 170 + i * 130; rr(d, (x, 760, x + 90, 900), 12, (200, 190, 180)); d.rectangle((x, 800, x + 90, 850), fill=(200, 70, 60))
        if lt > 1.0 + i * .15: check(d, x + 45, 830, 24, GREEN, 12)
    rr(d, (720, 720, 940, 900), 14, (172, 130, 80)); check(d, 830, 820, 30, GREEN, 14) if lt > 1.6 else None
    label(img, "ÁGUA E COMIDA GUARDADAS", 540, 200, lt, .3, 46, GREEN, (10, 30, 20))
    return img

@scene(2)
def s2_radio(lt, dur):
    img = Image.new("RGBA", (W, H), (30, 34, 66, 255)); d = ImageDraw.Draw(img); d.rectangle((0, 1250, W, H), fill=FLOOR)
    k = ease(lt / .35); r = 150 * k; d.ellipse((540 - r, 280 - r, 540 + r, 280 + r), fill=YEL); d.text((540 - F(900, 190 * k + 1).getlength("3") / 2, 280 - 108 * k), "3", font=F(900, int(190 * k) + 1), fill=(20, 20, 30))
    t2 = ease((lt - .25) / .3); f = F(900, 130); d.text((540 - f.getlength("SINTONIZE") / 2 + 300 * (1 - t2), 470), "SINTONIZE", font=f, fill=WHITE, stroke_width=8, stroke_fill=(0, 0, 0))
    rr(d, (140, 800, 640, 1100), 34, (170, 100, 60)); rr(d, (170, 830, 610, 1070), 22, (36, 24, 20)); d.ellipse((220, 880, 420, 1080), fill=(60, 44, 36), outline=(110, 90, 70), width=6)
    for ang in range(0, 360, 30): a = math.radians(ang); d.line((320 + math.cos(a) * 20, 980 + math.sin(a) * 20, 320 + math.cos(a) * 90, 980 + math.sin(a) * 90), fill=(90, 70, 56), width=4)
    d.line((560, 800, 700, 560), fill=(200, 204, 220), width=10); d.ellipse((690, 546, 714, 570), fill=(200, 204, 220))
    d.rectangle((460, 860, 590, 900), fill=(240, 220, 160)); d.line((470 + 60 * math.sin(lt * 2) + 60, 856, 470 + 60 * math.sin(lt * 2) + 60, 904), fill=RED, width=5)
    for k2 in range(4):
        p = ((lt * .9) + k2 * .25) % 1; rad = 40 + 220 * p; ov = Image.new("RGBA", img.size, (0, 0, 0, 0)); ImageDraw.Draw(ov).arc((702 - rad, 558 - rad, 702 + rad, 558 + rad), 200, 340, fill=YEL + (int(240 * (1 - p)),), width=10); img.alpha_composite(ov)
    d = ImageDraw.Draw(img); person(d, 860, 1250, 0.95, lt, "ear")
    return img

@scene(2)
def s2_door(lt, dur):
    img = Image.new("RGBA", (W, H), (14, 14, 26, 255)); d = ImageDraw.Draw(img)
    split = dur * .46
    if lt < split:  # gráfico: a radiação cai
        d.rectangle((0, 0, W, H), fill=(20, 24, 52)); ax, ay, aw, ah = 160, 1000, 760, 560
        d.line((ax, ay - ah, ax, ay), fill=WHITE, width=8); d.line((ax, ay, ax + aw, ay), fill=WHITE, width=8)
        p = ease(lt / (split - .3)); pts = [(ax + aw * x, ay - ah * (0.97 * math.exp(-4.2 * x) + .03)) for x in np.linspace(0, p, 40)]
        if len(pts) > 1: d.line(pts, fill=ORANGE, width=14, joint="curve")
        d.text((ax + 20, ay - ah - 70), "RADIAÇÃO", font=F(900, 54), fill=ORANGE); d.text((ax + aw - 230, ay + 20), "tempo", font=F(700, 40), fill=WHITE)
        d.polygon([(ax + aw + 30, ay), (ax + aw, ay - 22), (ax + aw, ay + 22)], fill=WHITE)
    else:
        lt2 = lt - split; d.rectangle((0, 1250, W, H), fill=(18, 18, 30)); sh = 8 * math.sin(lt2 * 60) if (lt2 % 0.9) < 0.18 else 0
        rr(d, (330 + sh, 420, 750 + sh, 1250), 18, (84, 56, 42)); d.rectangle((350 + sh, 440, 730 + sh, 1250), fill=(66, 44, 34)); d.ellipse((680 + sh, 860, 708 + sh, 888), fill=YEL)
        d.rectangle((350, 1236, 730, 1250), fill=(255, 220, 140)); glow(img, 540, 1240, 260, YEL, 60); d = ImageDraw.Draw(img)
        if (lt2 % 0.9) < 0.3: d.text((540 - F(900, 120).getlength("TOC!") / 2, 220), "TOC!", font=F(900, 120), fill=RED, stroke_width=8, stroke_fill=(0, 0, 0))
    return img

# ---------------- áudio (efeitos) ----------------
SFX = {1: [("alarm", 0.2, 3.6), ("whoosh", "b1"), ("honk", "b1", .3), ("honk", "b2", .2), ("thump", "b3", .3), ("whoosh", "b4"), ("ding", "b4", .45), ("whoosh", "b5"), ("thump", "b6", 0), ("rumble", "b6", 0)],
       2: [("whoosh", "b0"), ("whoosh", "b1"), ("tick", "b1", .5), ("beep", "b2", 1.0), ("tape", "b2", 1.5), ("whoosh", "b3"), ("splash", "b3", "h"), ("ding", "b4", .5), ("static", "b5", 0), ("ding", "b5", .45), ("knock", "b6", "k"), ("sting", "end")]}
def mix_audio():
    sr = 48000; n = int(TOTAL * sr) + sr; out = np.zeros(n, np.float32); rng = np.random.default_rng(P)
    def add(x, t0, v=1.0):
        o = int(t0 * sr)
        if o < 0 or o >= n: return
        m = min(len(x), n - o); out[o:o + m] += v * x[:m]
    def env_noise(dur, hp=False):
        k = int(dur * sr); x = rng.standard_normal(k).astype(np.float32); return x
    def whoosh(t0, dur=.5, v=.35):
        k = int(dur * sr); e = np.sin(np.linspace(0, np.pi, k)) ** 2; add(np.convolve(rng.standard_normal(k), np.ones(40) / 40, "same").astype(np.float32) * e * 5, t0, v)
    def thump(t0, v=.7):
        k = int(.5 * sr); tt = np.arange(k) / sr; f = 55 + 100 * np.exp(-tt * 20); add((np.sin(2 * np.pi * np.cumsum(f) / sr) * np.exp(-tt * 7)).astype(np.float32), t0, v)
    def ding(t0, v=.2):
        k = int(.9 * sr); tt = np.arange(k) / sr; add(((np.sin(2 * np.pi * 1320 * tt) + .4 * np.sin(2 * np.pi * 1320 * 2.76 * tt)) * np.exp(-tt * 5)).astype(np.float32), t0, v)
    def beep(t0, v=.2, f=880, dur=.12):
        k = int(dur * sr); tt = np.arange(k) / sr; add((np.sign(np.sin(2 * np.pi * f * tt)) * .6).astype(np.float32), t0, v)
    def honk(t0, v=.2):
        k = int(.45 * sr); tt = np.arange(k) / sr; add(((np.sign(np.sin(2 * np.pi * 410 * tt)) + np.sign(np.sin(2 * np.pi * 520 * tt))) * .35 * np.minimum(1, (0.45 - tt) / .08)).astype(np.float32), t0, v)
    def knock(t0, v=.9):
        for i in range(3):
            k = int(.18 * sr); tt = np.arange(k) / sr; add((np.sin(2 * np.pi * 95 * tt) * np.exp(-tt * 30) + rng.standard_normal(k) * np.exp(-tt * 90) * .3).astype(np.float32), t0 + i * .28, v)
    # narração
    for i, (a, s) in enumerate(CLIPS):
        if s != sr: from scipy import signal as sg; a = sg.resample_poly(a, sr // np.gcd(sr, s), s // np.gcd(sr, s)).astype(np.float32)
        add(a, START[i], 1.0)
    # drone de suspense (grave) + pulso lento
    tt = np.arange(n) / sr; drone = (np.sin(2 * np.pi * 55 * tt) * .6 + np.sin(2 * np.pi * 82.4 * tt) * .35 + np.sin(2 * np.pi * 110 * tt + 2 * np.sin(tt * .5)) * .15) * (.8 + .2 * np.sin(2 * np.pi * .13 * tt))
    ramp = np.clip(tt / 6, 0, 1) * .9 + .1; out += (drone * ramp * .10).astype(np.float32)
    for k in range(int(TOTAL / 1.1)): thump(k * 1.1 + .3, .06 + .05 * min(1, k / 20))  # batimento distante
    bd = lambda tag: (BOUND[int(tag[1])] if tag[0] == "b" else SCENE_END)
    for ev in SFX[P]:
        kind = ev[0]; ref = ev[1]
        if kind == "alarm":
            for i in range(int(ev[2] / .5)): beep(ev[1] + i * .5, .12, 880 if i % 2 == 0 else 660, .22)
            continue
        t0 = (bd(ref) if isinstance(ref, str) and (ref[0] == "b" or ref == "end") else ref) if isinstance(ref, str) else ref
        off = ev[2] if len(ev) > 2 and isinstance(ev[2], (int, float)) else 0
        t0 = (BOUND[int(ref[1:])] if ref.startswith("b") else SCENE_END) + off
        if kind == "whoosh": whoosh(t0 - .1)
        elif kind == "honk": honk(t0)
        elif kind == "thump": thump(t0)
        elif kind == "ding": ding(t0)
        elif kind == "tick":
            for i in range(10): beep(t0 + i * .2, .08, 1500, .02)
        elif kind == "beep": beep(t0, .15, 700, .2)
        elif kind == "tape":
            for i in range(4): whoosh(t0 + i * .25, .2, .25)
        elif kind == "splash": whoosh(t0 + 1.0, 1.4, .3)
        elif kind == "static": add((np.convolve(rng.standard_normal(int(2.5 * sr)), np.ones(3) / 3, "same") * .25 * np.minimum(1, np.linspace(1, 0, int(2.5 * sr)) * 3)).astype(np.float32), t0 + .2, .22)
        elif kind == "knock": knock(BOUND[6] + (SCENE_END - BOUND[6]) * .46 + .1)
        elif kind == "rumble": add((np.convolve(rng.standard_normal(int(2.2 * sr)), np.ones(300) / 300, "same") * 14 * np.sin(np.linspace(0, np.pi, int(2.2 * sr)))).astype(np.float32), t0, .35)
        elif kind == "sting":
            for f, d0 in ((196, 0), (185, .0)):
                k = int(2.6 * sr); t2 = np.arange(k) / sr; add(((np.sin(2 * np.pi * f * t2) + .5 * np.sin(2 * np.pi * f * 2 * t2)) * np.exp(-t2 * 1.4)).astype(np.float32), t0 + d0, .18)
    out = out[: int(TOTAL * sr)]; fi = int(.4 * sr); out[:fi] *= np.linspace(0, 1, fi); fo = int(.9 * sr); out[-fo:] *= np.linspace(1, 0, fo)
    out = np.tanh(out * 1.3) / np.tanh(1.3); out = out / max(1e-6, abs(out).max()) * .9
    sf.write(os.path.join(PD, "audio.wav"), np.stack([out, out], 1), sr)

# ---------------- render ----------------
def endcard(lt):
    img = Image.new("RGBA", (W, H), (10, 12, 26, 255)); d = ImageDraw.Draw(img); t1, t2, t3 = SC_END[P]
    k = ease(lt / .4)
    if P == 1:
        f = F(900, int(190 * k) + 4); d.text((540 - f.getlength(t1) / 2, 640 + 40 * (1 - k)), t1, font=f, fill=WHITE, stroke_width=8, stroke_fill=(0, 0, 0))
    else:
        f = F(900, 100); words = ["VOCÊ ABRIRIA", "A PORTA?"]
        for i, wd in enumerate(words): d.text((540 - f.getlength(wd) / 2, 560 + i * 130 + 40 * (1 - k)), wd, font=f, fill=WHITE, stroke_width=8, stroke_fill=(0, 0, 0))
    f2 = F(700, 48); ty = 900 if P == 1 else 880
    d.text((540 - f2.getlength(t2) / 2, ty), t2, font=f2, fill=YEL)
    if lt > .8: pill(img, t3, 540, 1180, 48, ORANGE, (20, 20, 30))
    f3 = F(700, 30)
    for k, msg in enumerate(("Informações gerais de segurança.", "Siga sempre a orientação da Defesa Civil.")): d.text((540 - f3.getlength(msg) / 2, 1360 + 44 * k), msg, font=f3, fill=(170, 176, 200))
    return img

def main():
    mix_audio()
    json.dump({"total": TOTAL, "start": START, "dur": DUR, "bound": BOUND}, open(os.path.join(PD, "timeline.json"), "w"))
    scenes = SC[P]; assert len(scenes) == len(LINES), (len(scenes), len(LINES))
    out = sys.stdout.buffer
    for f in range(int(TOTAL * FPS)):
        t = f / FPS
        if t >= SCENE_END: img = endcard(t - SCENE_END)
        else:
            i = max(k for k, b in enumerate(BOUND[:-1]) if t >= b); lt = t - BOUND[i]; dur = BOUND[i + 1] - BOUND[i]
            img = scenes[i](lt, dur)
            z = 1 + 0.05 * lt / max(.5, dur)  # push-in lento
            if z > 1.001: cw, ch = W / z, H / z; img = img.convert("RGB").crop((int((W - cw) / 2), int((H - ch) / 2), int((W + cw) / 2), int((H + ch) / 2))).resize((W, H), Image.BILINEAR).convert("RGBA")
            if lt < .1: img.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, int(110 * (1 - lt / .1)))))
            draw_sub(img, t)
        if t < .35: img.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, int(255 * (1 - t / .35)))))
        out.write(img.convert("RGB").tobytes())

if __name__ == "__main__": main()
