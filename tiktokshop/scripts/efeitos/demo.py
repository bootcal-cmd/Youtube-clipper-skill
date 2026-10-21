"""Demo: aplica cada efeito por ~1,6 s sobre um vídeo (frames JPG 1080x1920 a 30fps em SRC), com contador 01/11 como na referência.
uso: FONT_DIR=<pasta fontes> python3 demo.py <pasta_frames> | ffmpeg ... """
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from efeitos import *
SRC = sys.argv[1]; SEG = 1.6; FPS = 30; N = len(EFFECTS); NFR = len([f for f in os.listdir(SRC) if f.endswith(".jpg")])
out = sys.stdout.buffer
for f in range(int(N * SEG * FPS)):
    t = f / FPS; i = int(t // SEG); lt = t - i * SEG
    im = Image.open(os.path.join(SRC, "%04d.jpg" % (min(NFR, f % NFR) + 1))).convert("RGB")
    r = EFFECTS[i](im, lt).convert("RGBA"); d = ImageDraw.Draw(r)
    d.rounded_rectangle((60, 70, 230, 130), 16, fill=(0, 0, 0, 170)); d.text((145, 100), "%02d/%02d" % (i + 1, N), font=F(900, 34), fill="white", anchor="mm")
    d.text((W - 60, 100), EFFECTS[i].__name__, font=F(700, 26), fill=(255, 255, 255, 200), anchor="rm")
    out.write(r.convert("RGB").tobytes())
