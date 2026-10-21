"""Biblioteca de efeitos de vídeo vertical (1080x1920) aprendidos de um vídeo de referência (17 efeitos).
Cada efeito: fn(img: PIL.Image RGB 1080x1920, t: segundos desde o início do efeito, **opts) -> PIL.Image RGB.
Fontes: espera mont500/700/900.ttf em FONT_DIR (padrão: pasta pai do scratchpad)."""
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops, ImageEnhance, ImageOps
import math, random, os
W, H = 1080, 1920
FONT_DIR = os.environ.get("FONT_DIR", ".")
ease = lambda p: (lambda q: q * q * (3 - 2 * q))(min(1, max(0, p)))
lerp = lambda a, b, p: a + (b - a) * p
def F(w, s): return ImageFont.truetype(os.path.join(FONT_DIR, f"mont{w}.ttf"), s)
SERIF = "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"
def back(o, s, c=1.0, o2=None):  # overshoot "pop": 0→1 com leve estouro
    p = min(1, max(0, s)); return 1 + 2.7 * (p - 1) ** 3 + 1.7 * (p - 1) ** 2 if p < 1 else 1.0
def cover(im, w, h, z=1.0, fx=.5, fy=.5):
    iw, ih = im.size; b = max(w / iw, h / ih) * z; cw, ch = w / b, h / b
    cx = min(max(fx * iw, cw / 2), iw - cw / 2); cy = min(max(fy * ih, ch / 2), ih - ch / 2)
    return im.crop((int(cx - cw / 2), int(cy - ch / 2), int(cx + cw / 2), int(cy + ch / 2))).resize((int(w), int(h)), Image.BILINEAR)
def rounded(im, r):
    m = Image.new("L", im.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, im.width - 1, im.height - 1), r, fill=255)
    o = im.convert("RGBA"); o.putalpha(m); return o
def shadow(layer, off=(10, 14), blur=18, a=.55):
    sh = Image.new("RGBA", layer.size, (0, 0, 0, 0)); sh.putalpha(layer.getchannel("A").point(lambda v: int(v * a)))
    return sh.filter(ImageFilter.GaussianBlur(blur))
def paste_rot(base, im, cx, cy, ang, sc=1.0, shadowed=True):
    im = im.convert("RGBA"); im = im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))), Image.LANCZOS).rotate(ang, resample=Image.BICUBIC, expand=True)
    if shadowed:
        sh = shadow(im); base.alpha_composite(sh, (int(cx - im.width / 2 + 10), int(cy - im.height / 2 + 14)))
    base.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))
def outline_text(d, xy, txt, font, fill="white", stroke=8, anchor="mm", sfill="black"):
    d.text(xy, txt, font=font, fill=fill, stroke_width=stroke, stroke_fill=sfill, anchor=anchor)

# 1) PAREDE DE POLAROIDS — fotos (frames do próprio vídeo) caem e grudam em ângulos aleatórios
def polaroids(img, t, n=7, seed=3, text="TODO DIA"):
    rnd = random.Random(seed); base = ImageEnhance.Brightness(cover(img, W, H)).enhance(.55).convert("RGBA")
    for i in range(n):
        a = i * .22; k = (t - a) / .35
        if k <= 0: continue
        pw = 330; ph = 400; ph_im = Image.new("RGBA", (pw, ph), (250, 248, 242, 255)); ph_im.paste(cover(img, pw - 36, ph - 100, 1.6 - .1 * i, .3 + .4 * rnd.random(), .35).convert("RGBA"), (18, 18))
        cx = rnd.randint(200, 880); cy = rnd.randint(380, 1380); ang = rnd.uniform(-14, 14); sc = back(0, k) * min(1, k * 2.5 + .3)
        paste_rot(base, ph_im, cx, cy - (1 - min(1, k)) * 300, ang, sc)
    d = ImageDraw.Draw(base); outline_text(d, (W / 2, 1560), text, F(900, 110), fill=(255, 255, 255), stroke=9)
    return base.convert("RGB")

# 2) CONTORNO NEON PULSANTE + chamada
def neon_frame(img, t, color=(120, 255, 60), text="PULA PRA"):
    base = cover(img, W, H).convert("RGBA"); base = ImageEnhance.Brightness(base).enhance(.8)
    pulse = .75 + .25 * math.sin(t * 7); lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle((40, 40, W - 40, H - 40), 70, outline=color + (255,), width=14)
    glow = lay.filter(ImageFilter.GaussianBlur(26)); glow.putalpha(glow.getchannel("A").point(lambda v: int(min(255, v * 2.2 * pulse))))
    base.alpha_composite(glow); base.alpha_composite(lay)
    d = ImageDraw.Draw(base); k = ease(t / .3)
    d.text((W / 2, 230 - (1 - k) * 60), text, font=F(900, 96), fill=color + (int(255 * k),), anchor="mm")
    return base.convert("RGB")

# 3) P&B + PALAVRA-CHAVE AMARELA GIGANTE (estoura na tela)
def bw_keyword(img, t, word="SEM SABER", color=(255, 214, 0)):
    base = ImageOps.grayscale(cover(img, W, H)); base = ImageEnhance.Contrast(base).enhance(1.25).convert("RGBA")
    base.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, 70)))
    s = back(0, t / .3); size = 190
    while ImageDraw.Draw(base).textlength(word, font=F(900, size)) > 940: size -= 6
    f = F(900, int(size * max(.2, s))); d = ImageDraw.Draw(base)
    outline_text(d, (W / 2, 1480), word, f, fill=color, stroke=10)
    return base.convert("RGB")

# 4) TELA DIVIDIDA + CHAT (mensagens digitando)
def chat_split(img, t, msgs=("faz um corte rápido?", "feito ✅  legenda e zoom aplicados")):
    base = Image.new("RGBA", (W, H), (12, 14, 24, 255)); top = cover(img, W, 980, 1.0).convert("RGBA"); base.alpha_composite(top, (0, 0))
    d = ImageDraw.Draw(base); y = 1040
    for i, m in enumerate(msgs):
        a = i * 1.1; k = (t - a) / .35
        if k <= 0: continue
        me = i % 2 == 0; f = F(700, 38); w = int(d.textlength(m, font=f)) + 70; h = 96; x0 = (W - w - 60) if me else 60; yy = y + (1 - ease(k)) * 30
        col = (108, 92, 231) if me else (36, 40, 62)
        bub = Image.new("RGBA", (W, H), (0, 0, 0, 0)); bd = ImageDraw.Draw(bub); bd.rounded_rectangle((x0, yy, x0 + w, yy + h), 38, fill=col + (int(255 * min(1, k)),))
        bd.text((x0 + 35, yy + 22), m, font=f, fill=(255, 255, 255, int(255 * min(1, k)))); base.alpha_composite(bub); y += 130
    if t % 1.1 < .8 and t < len(msgs) * 1.1:  # "digitando..."
        for j in range(3): d.ellipse((90 + j * 34, 1760 - 8 * abs(math.sin(t * 8 + j)), 110 + j * 34, 1780 - 8 * abs(math.sin(t * 8 + j))), fill=(140, 150, 180))
    return base.convert("RGB")

# 5) SCRAPBOOK / CORTA E COLA — papel kraft, vídeo inclinado com fita e letras recortadas
def scrapbook(img, t, text="CORTA E COLA", seed=5):
    base = Image.new("RGBA", (W, H), (178, 143, 100, 255)); rnd = random.Random(seed)
    for _ in range(900): x, y = rnd.randint(0, W), rnd.randint(0, H); ImageDraw.Draw(base).point((x, y), fill=(160, 126, 86, 255))
    k = ease(t / .4); vid = cover(img, 760, 1000).convert("RGBA"); vid = ImageOps.expand(vid, 14, (250, 248, 240)).convert("RGBA")
    paste_rot(base, vid, W / 2, 1080 + (1 - k) * 400, -4 + (1 - k) * 12, 1.0)
    for (x, y, a, c) in ((250, 600, -35, (255, 200, 0, 220)), (840, 590, 32, (240, 60, 150, 220))):
        tape = Image.new("RGBA", (220, 64), c); paste_rot(base, tape, x, y, a, 1.0, False)
    # letras recortadas
    d = ImageDraw.Draw(base); cols = [(240, 60, 150), (255, 200, 0), (30, 170, 240), (40, 190, 90), (255, 120, 30)]; x = (W - len(text) * 70) / 2; r2 = random.Random(9)
    for i, ch in enumerate(text):
        if ch == " ": x += 40; continue
        if (t - i * .05) < 0: x += 70; continue
        bg = r2.choice(cols); ln = Image.new("RGBA", (84, 110), bg + (255,)); ld = ImageDraw.Draw(ln)
        ld.text((42, 55), ch, font=ImageFont.truetype(SERIF, 80), fill=(255, 255, 255) if bg != (255, 200, 0) else (20, 20, 20), anchor="mm")
        paste_rot(base, ln, x + 35, 330 + r2.randint(-12, 12), r2.uniform(-9, 9), 1.0); x += 70
    return base.convert("RGB")

# 6) RABISCOS DESENHADOS À MÃO (coroa, estrelas, coração) em quadro negro
def doodles(img, t):
    base = Image.new("RGBA", (W, H), (22, 34, 30, 255)); vid = rounded(cover(img, 800, 1050), 60); base.alpha_composite(vid, (140, 560))
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); gold = (255, 214, 90, 255)
    def prog(pts, a, b):  # desenha polilinha progressivamente
        p = ease((t - a) / b); n = max(2, int(len(pts) * p))
        if p > 0: d.line(pts[:n], fill=gold, width=10, joint="curve")
    prog([(330, 460), (370, 360), (440, 430), (540, 330), (640, 430), (710, 360), (750, 460), (330, 460)], .1, .7)
    star = lambda cx, cy, r: [(cx + r * math.cos(-math.pi / 2 + i * 4 * math.pi / 5), cy + r * math.sin(-math.pi / 2 + i * 4 * math.pi / 5)) for i in range(6)]
    prog(star(150, 700, 70), .5, .6); prog(star(940, 820, 55), .8, .6)
    heart = [(940 + 60 * math.sin(a) ** 3, 520 - (50 * math.cos(a) - 20 * math.cos(2 * a) - 8 * math.cos(3 * a) - 4 * math.cos(4 * a))) for a in [i * .15 for i in range(43)]]
    prog(heart, 1.0, .8)
    for _ in range(2): lay = lay  # mantém
    wob = lay.filter(ImageFilter.GaussianBlur(.6)); base.alpha_composite(wob)
    return base.convert("RGB")

# 7) DUOTONE VERMELHO + PERGUNTA GIGANTE
def duotone_red(img, t, text="NUNCA EDITOU?"):
    g = ImageOps.grayscale(cover(img, W, H)); g = ImageOps.autocontrast(g, 2)
    base = ImageOps.colorize(g, (30, 0, 6), (255, 235, 235), mid=(190, 20, 40)).convert("RGBA")
    d = ImageDraw.Draw(base); k = ease(t / .35); f = F(900, 120)
    words = text.split(); y = 300
    for i, w in enumerate(words):
        kk = ease((t - i * .18) / .3); d.text((W / 2, y + (1 - kk) * 50), w, font=f, fill=(255, 255, 255, int(255 * kk)), anchor="mm"); y += 140
    return base.convert("RGB")

# 8) CAPA DE REVISTA
def magazine(img, t, title="LUCÃO", sub="17 EFEITOS", edition="EDIÇÃO Nº 17"):
    base = Image.new("RGBA", (W, H), (236, 232, 222, 255)); d = ImageDraw.Draw(base)
    k = ease(t / .4); photo = cover(img, 920, 1160, 1.0 + .06 * t).convert("RGBA"); base.alpha_composite(photo, (80, 560))
    ms = ImageFont.truetype(SERIF, 230); d.text((W / 2, 330 - (1 - k) * 80), title, font=ms, fill=(20, 20, 20), anchor="mm")
    d.line((80, 470, W - 80, 470), fill=(20, 20, 20), width=5); d.text((80, 495), edition, font=F(700, 28), fill=(60, 60, 60))
    d.text((W - 80, 495), "TODOS OS DIREITOS", font=F(700, 28), fill=(60, 60, 60), anchor="ra")
    d.rounded_rectangle((90, 1500, 520, 1690), 14, fill=(214, 40, 40)); d.text((305, 1560), sub, font=F(900, 58), fill="white", anchor="mm"); d.text((305, 1630), "que mudam seu vídeo", font=F(700, 30), fill="white", anchor="mm")
    return base.convert("RGB")

# 9) TEXTO "VIDRO" GIGANTE (translúcido com desfoque) sobre o vídeo
def glass_text(img, t, word="CRIA"):
    base = cover(img, W, H).convert("RGBA"); k = ease(t / .5)
    mask = Image.new("L", (W, H), 0); ImageDraw.Draw(mask).text((W / 2, 1000 - (1 - k) * 80), word, font=F(900, 380), fill=int(255 * k), anchor="mm")
    blur = base.filter(ImageFilter.GaussianBlur(24)); blur = ImageEnhance.Brightness(blur).enhance(1.35)
    base = Image.composite(blur, base, mask)
    edge = ImageChops.subtract(mask, mask.filter(ImageFilter.MinFilter(9))); base.paste((255, 255, 255, 255), mask=edge.point(lambda v: int(v * .8)))
    return base.convert("RGB")

# 10) TIMELINE DE EDITOR (playhead correndo, faixas coloridas)
def timeline_ui(img, t, dur=4.0):
    base = Image.new("RGBA", (W, H), (16, 18, 28, 255)); base.alpha_composite(rounded(cover(img, 760, 1000), 24), (160, 140)); d = ImageDraw.Draw(base)
    y0 = 1330; tracks = [((255, 140, 50), [(0, .3), (.33, .7), (.72, 1)]), ((130, 90, 255), [(.05, .55), (.6, .95)]), ((60, 200, 140), [(0, 1)])]
    for r, (col, segs) in enumerate(tracks):
        for a, b in segs: d.rounded_rectangle((60 + a * 960, y0 + r * 110, 60 + b * 960 - 6, y0 + r * 110 + 90), 16, fill=col)
    x = 60 + 960 * ((t / dur) % 1); d.rectangle((x - 3, y0 - 40, x + 3, y0 + 340), fill=(255, 255, 255)); d.polygon([(x - 16, y0 - 40), (x + 16, y0 - 40), (x, y0 - 14)], fill=(255, 255, 255))
    d.text((60, 1270), "00:%02d" % int(t % 60), font=F(700, 34), fill=(180, 190, 215)); return base.convert("RGB")

# 11) CARD DE PROMO COM DEGRADÊ ROXO
def gradient_promo(img, t, title="Seu editor agora é o Claude."):
    g = Image.new("RGB", (1, H)); g.putdata([(int(lerp(90, 200, i / H)), int(lerp(40, 70, i / H)), int(lerp(255, 230, i / H))) for i in range(H)]); base = g.resize((W, H)).convert("RGBA")
    k = ease(t / .4); d = ImageDraw.Draw(base); f = F(900, 92); y = 260
    words = title.split(); lines = []; cur = ""
    for w in words:
        if d.textlength(cur + " " + w, font=f) < 880: cur = (cur + " " + w).strip()
        else: lines.append(cur); cur = w
    lines.append(cur)
    for ln in lines: d.text((80, y + (1 - k) * 40), ln, font=f, fill=(255, 255, 255, int(255 * k))); y += 112
    vid = rounded(cover(img, 800, 900), 50); paste_rot(base, vid, W / 2, 1230 + (1 - k) * 200, 0, 1.0)
    return base.convert("RGB")

EFFECTS = [polaroids, neon_frame, bw_keyword, chat_split, scrapbook, doodles, duotone_red, magazine, glass_text, timeline_ui, gradient_promo]
