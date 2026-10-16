import sys,os,soundfile as sf
from kokoro_onnx import Kokoro
S=os.path.dirname(os.path.abspath(__file__))+"/.."
k=Kokoro(S+"/kokoro-v1.0.onnx",S+"/voices-v1.0.bin")
for p in ("p1","p2"):
    os.makedirs(f"{S}/nuc/{p}/n",exist_ok=True)
    for i,l in enumerate([x for x in open(f"{S}/nuc/{p}/lines.txt",encoding="utf8").read().split("\n") if x.strip()]):
        a,sr=k.create(l.replace("*",""),voice="pm_santa",speed=0.92,lang="pt-br")
        sf.write(f"{S}/nuc/{p}/n/{i}.wav",a,sr); print(p,i,round(len(a)/sr,2))
