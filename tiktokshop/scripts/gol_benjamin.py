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
HK=[(ransom("GOLAÇO",s,95,900,170),ransom("DO BENJAMIN",s+9,285,820,110)) for s in (1,2,3)]
GOOOL=[ransom("GOOOL!",s+30,300,940,190) for s in (1,2,3)]
_r=random.Random(4); CONF=[(_r.uniform(0,W),_r.uniform(-H,0),_r.uniform(12,24),_r.uniform(0,6.28),_r.uniform(300,600),_r.choice(TILES)) for _ in range(80)]
def confetti(img,t,t0,amt=1.0):
    lay=Image.new("RGBA",img.size,(0,0,0,0)); d=ImageDraw.Draw(lay)
    for x,y,s,ph,sp,c in CONF[:int(len(CONF)*amt)]:
        yy=(y+sp*(t-t0))%(H+200)-100; xx=x+40*math.sin(t*2+ph); w=abs(math.cos(t*6+ph))*s+3
        d.rectangle((xx-w/2,yy-s*.3,xx+w/2,yy+s*.3),fill=c+(235,))
    img.alpha_composite(lay)
# linha do tempo
T_NORM,T_REP,T_END=6.5,4.6,3.2; REP_SRC=4.2; GOAL=5.4
TOTAL=T_NORM+T_REP+T_END
def src_time(t):
    if t<T_NORM: return t
    return REP_SRC+(t-T_NORM)*0.5
_c={}
def band(st):
    i=min(396,max(1,int(round(st*60))+1))
    if i not in _c:
        if len(_c)>40:_c.clear()
        _c[i]=Image.open(os.path.join(D,"src/%04d.jpg"%i)).convert("RGB")
    return _c[i]
def panel(st,lt_out):
    b=band(st)
    cx=lerp(900,1080,ease(st/2.5)) if st<6.0 else 1080
    cy=640+10
    size=720
    if st>6.0: size=lerp(720,1000,ease((st-6.0)/.5))
    if lt_out>=T_NORM: # replay: aperta um pouco no lance
        size=lerp(720,600,ease((lt_out-T_NORM)/T_REP))
    cx=min(max(cx,size/2),1440-size/2); cy=min(max(cy,size/2),1280-size/2)
    cr=b.crop((int(cx-size/2),int(cy-size/2),int(cx+size/2),int(cy+size/2))).resize((1080,1080),Image.LANCZOS)
    return cr,b
AV=ImageOps.exif_transpose(Image.open("/root/.claude/uploads/f05dfe21-700d-5c7c-a427-931b58f48d32/a216812f-image.jpg")).convert("RGB").crop((72,382,292,602)).resize((300,300),Image.LANCZOS)
mask=Image.new("L",(300,300),0); ImageDraw.Draw(mask).ellipse((0,0,299,299),fill=255)
def frame(t):
    st=src_time(t)
    if t<T_NORM+T_REP:
        pn,b=panel(st,t)
        bg=b.crop((0,0,1440,1280)).resize((1440*1920//1280,1920),Image.BILINEAR); bg=bg.crop(((bg.width-W)//2,0,(bg.width-W)//2+W,1920)).filter(ImageFilter.GaussianBlur(28))
        img=Image.eval(bg,lambda v:int(v*.45)).convert("RGBA")
        img.paste(pn,(0,420)); d=ImageDraw.Draw(img)
        d.rectangle((0,416,W,422),fill=(255,200,0)); d.rectangle((0,1498,W,1504),fill=(255,200,0))
        # legendas
        if t<2.4:
            k=min(1,t/.2); f=int(t*6)%3
            for L in HK[f]:
                if k<1:
                    sc=.6+.4*k; r=L.resize((int(W*sc),int(H*sc)),Image.LANCZOS); img.alpha_composite(r,(int(W/2-W/2*sc),int(300-300*sc)))
                else: img.alpha_composite(L)
            rich(img,"na escolinha de futebol ⚽",W/2,1560,F(900,60),n=int(max(0,t-.3)*26))
        elif t<T_NORM:
            if t<GOAL: rich(img,"olha o aperto na área 👀",W/2,1560,F(900,64),n=int((t-2.4)*26))
            else:
                f=int(t*8)%3; k=ease((t-GOAL)/.25); L=GOOOL[f]; sc=.5+.5*k
                r=L.resize((int(W*sc),int(H*sc)),Image.LANCZOS); img.alpha_composite(r,(int(W/2-W/2*sc),int(300-300*sc)))
                rich(img,"É DELE! 🔥",W/2,1560,F(900,80))
                confetti(img,t,GOAL,min(1,(t-GOAL)/.4))
        else:
            lt=t-T_NORM
            d.rounded_rectangle((W/2-190,170,W/2+190,260),45,fill=(255,60,60)); rich(img,"REPLAY 🔁",W/2,185,F(900,50),stroke=0)
            rich(img,"câmera lenta 🐢",W/2,1560,F(900,64),n=int(lt*26))
            if t>T_NORM+T_REP-1.4: confetti(img,t,T_NORM+T_REP-1.4,.5)
        if abs(t-GOAL)<.07 or abs(t-T_NORM)<.07: img.alpha_composite(Image.new("RGBA",img.size,(255,255,255,150)))
        if t<.2: img.alpha_composite(Image.new("RGBA",img.size,(0,0,0,int(255*(1-t/.2)))))
        return img
    lt=t-T_NORM-T_REP
    img=Image.new("RGBA",(W,H),(12,18,34,255)); d=ImageDraw.Draw(img)
    for r in range(8): d.ellipse((540-700+r*60,700-700+r*60,540+700-r*60,700+700-r*60),fill=(12+r*2,18+r*3,34+r*5))
    k=ease(lt/.4)
    av=Image.new("RGBA",(300,300),(0,0,0,0)); av.paste(AV,(0,0),mask)
    sc=.6+.4*k; a2=av.resize((int(300*sc),int(300*sc)),Image.LANCZOS)
    d.ellipse((540-170,400-170,540+170,400+170),outline=(255,200,0),width=8)
    img.alpha_composite(a2,(int(540-a2.width/2),int(400-a2.height/2)))
    rich(img,"BENJAMIN ALVES",W/2,640,F(900,78),n=int(lt*30))
    rich(img,"ator & modelo mirim ⚽",W/2,760,F(800,50),n=int(max(0,lt-.4)*28))
    if lt>.9: 
        pill=Image.new("RGBA",(W,H),(0,0,0,0)); pd=ImageDraw.Draw(pill); pd.rounded_rectangle((250,900,830,1000),50,fill=(255,200,0,255)); img.alpha_composite(pill)
        rich(img,"segue pra acompanhar 💛",W/2,918,F(900,42),stroke=0,fill=(20,20,20))
    if lt<.08: img.alpha_composite(Image.new("RGBA",img.size,(255,255,255,int(150*(1-lt/.08)))))
    if t>TOTAL-.4: img.alpha_composite(Image.new("RGBA",img.size,(0,0,0,int(255*(t-(TOTAL-.4))/.4))))
    return img
out=sys.stdout.buffer
for f in range(int(TOTAL*FPS)): out.write(frame(f/FPS).convert("RGB").tobytes())
json.dump({"total":TOTAL,"norm":T_NORM,"rep":T_REP,"goal":GOAL,"rep_src":REP_SRC},open(os.path.join(D,"gol.json"),"w"))
