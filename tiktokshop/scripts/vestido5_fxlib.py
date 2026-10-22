from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
import os, sys, math, re, random, json
D=os.path.dirname(os.path.abspath(__file__)); S=os.path.dirname(D)
W,H,FPS=1080,1920,30
ease=lambda p:(lambda q:q*q*(3-2*q))(min(1,max(0,p))); lerp=lambda a,b,p:a+(b-a)*p
F=lambda w,s:ImageFont.truetype(os.path.join(S,f"mont{w}.ttf"),s)
EMO=ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf",109)
EMO_RE=re.compile(r"([\U0001F300-\U0001FAFF☀-➿]️?)")
_ec={}
def emoji(ch,size):
    if (ch,size) not in _ec:
        im=Image.new("RGBA",(160,160),(0,0,0,0)); ImageDraw.Draw(im).text((10,10),ch,font=EMO,embedded_color=True)
        im=im.crop(im.getbbox()); _ec[(ch,size)]=im.resize((max(1,int(im.width*size/im.height)),size),Image.LANCZOS)
    return _ec[(ch,size)]
def rich(img,text,x,y,font,n=None,stroke=7,fill="white"):
    parts=[p for p in EMO_RE.split(text) if p]; asc,_=font.getmetrics(); es=int(asc*.95)
    wid=sum(emoji(p,es).width if EMO_RE.fullmatch(p) else font.getlength(p) for p in parts)
    cx=x-wid/2; d=ImageDraw.Draw(img); left=10**6 if n is None else n
    for p in parts:
        if left<=0: break
        if EMO_RE.fullmatch(p): img.alpha_composite(emoji(p,es),(int(cx),int(y+(asc-es)/2+4))); cx+=emoji(p,es).width; left-=1
        else: q=p[:left]; left-=len(p); d.text((cx,y),q,font=font,fill=fill,stroke_width=stroke,stroke_fill="black"); cx+=font.getlength(p)
SERIFS=["/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf","/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf","/usr/share/fonts/truetype/liberation/LiberationSerif-BoldItalic.ttf"]
TILES=[(240,60,150),(255,200,0),(30,170,240),(130,70,220),(40,190,90),(255,120,30)]
def _tile(ch,rnd,h=140):
    font=ImageFont.truetype(rnd.choice(SERIFS),int(h*rnd.uniform(.8,.95))); bg=rnd.choice(TILES); fg=(20,20,20) if bg==(255,200,0) else (255,255,255)
    w=int(font.getlength(ch))+rnd.randint(12,24); hh=h+rnd.randint(-12,10)
    im=Image.new("RGBA",(w+20,hh+20),(0,0,0,0)); d=ImageDraw.Draw(im); j=lambda:rnd.randint(-5,5)
    d.polygon([(10+j(),10+j()),(w+10+j(),10+j()),(w+10+j(),hh+10+j()),(10+j(),hh+10+j())],fill=bg+(255,))
    d.text(((w+20)/2,(hh+20)/2),ch,font=font,fill=fg,anchor="mm")
    im=im.rotate(rnd.uniform(-8,8),resample=Image.BICUBIC,expand=True)
    sh=Image.new("RGBA",im.size,(0,0,0,0)); sh.putalpha(im.getchannel("A").point(lambda a:a*.45))
    out=Image.new("RGBA",(im.width+8,im.height+8),(0,0,0,0)); out.alpha_composite(sh.filter(ImageFilter.GaussianBlur(4)),(6,6)); out.alpha_composite(im,(0,0)); return out
def ransom(text,seed,y,maxw=980,h=140):
    rnd=random.Random(seed); tiles=[None if c==" " else _tile(c,rnd,h) for c in text]
    total=sum(55 if t is None else t.width-14 for t in tiles); sc=min(1.0,maxw/total)
    layer=Image.new("RGBA",(W,H),(0,0,0,0)); x=(W-total*sc)/2
    for t in tiles:
        if t is None: x+=55*sc; continue
        t2=t.resize((int(t.width*sc),int(t.height*sc)),Image.LANCZOS); layer.alpha_composite(t2,(int(x),int(y+rnd.randint(-8,8)))); x+=(t.width-14)*sc
    return layer
