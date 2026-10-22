"""5 abordagens para o vestido midi de tricô (TikTok Shop). uso: python3 vest.py <1-5>  -> frames RGB no stdout + vest<N>.json (SFX)"""
import sys, os, math, json, random
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),"fxlib.py")).read().replace("D=os.path.dirname(os.path.abspath(__file__)); S=os.path.dirname(D)","D=os.path.dirname(os.path.abspath(__file__)); S=os.path.dirname(D)"))
from PIL import ImageChops
P=int(sys.argv[1]); RED=(254,44,85); GREEN=(46,204,113)
_cache={}
def fr(c,st):
    i=min(240,max(1,int(st*24)+1)); k=(c,i)
    if k not in _cache:
        if len(_cache)>60:_cache.clear()
        _cache[k]=Image.open(os.path.join(D,f"f_{c}","%04d.jpg"%i)).convert("RGB")
    return _cache[k]
def view(c,st,z=1.0,fx=.5,fy=.5,w=W,h=H):
    im=fr(c,st); iw,ih=im.size; base=max(w/iw,h/ih); cw,ch=w/(base*z),h/(base*z)
    cx=min(max(fx*iw,cw/2),iw-cw/2); cy=min(max(fy*ih,ch/2),ih-ch/2)
    return im.crop((int(cx-cw/2),int(cy-ch/2),int(cx+cw/2),int(cy+ch/2))).resize((w,h),Image.BILINEAR)
# segmento: (clipe, s0, dur, vel, z0, z1, fx, fy)
class Seg:
    def __init__(s,c,s0,d,v=1.0,z0=1.0,z1=1.08,fx=.5,fy=.5): s.c,s.s0,s.d,s.v,s.z0,s.z1,s.fx,s.fy=c,s0,d,v,z0,z1,fx,fy
    def img(s,lt,w=W,h=H,fy=None): return view(s.c,s.s0+lt*s.v,lerp(s.z0,s.z1,lt/s.d),s.fx,s.fy if fy is None else fy,w,h)
def starts(segs):
    t=0; out=[]
    for s in segs: out.append(t); t+=s.d
    return out,t
def seg_at(segs,st,t):
    i=max(k for k,x in enumerate(st) if t>=x-1e-9); return i,t-st[i]
def punch(img,lt,flash=True):
    if lt<.12: img=img.crop((0,0,W,H)); z=1+.05*(1-lt/.12); cw,ch=W/z,H/z; img=img.crop((int((W-cw)/2),int((H-ch)/2),int((W+cw)/2),int((H+ch)/2))).resize((W,H),Image.BILINEAR)
    img=img.convert("RGBA")
    if flash and lt<.06: img.alpha_composite(Image.new("RGBA",(W,H),(255,255,255,int(150*(1-lt/.06)))))
    return img
def shade(img,top=420,bot=520,a=150):
    g=Image.new("L",(1,top)); g.putdata([int(a*(1-i/top)**1.5) for i in range(top)]); t=Image.new("RGBA",(W,top),(0,0,0,0)); t.putalpha(g.resize((W,top))); img.alpha_composite(t,(0,0))
    g=Image.new("L",(1,bot)); g.putdata([int(a*(i/bot)**1.5) for i in range(bot)]); b=Image.new("RGBA",(W,bot),(0,0,0,0)); b.putalpha(g.resize((W,bot))); img.alpha_composite(b,(0,H-bot))
def plaq(img,l1,l2,t,seed=1,y1=250,y2=450,h1=150,h2=105):
    k=min(1,t/.2); f=int(t*6)%3
    a=ransom(l1,seed+f,y1,900,h1); b=ransom(l2,seed+f+9,y2,860,h2)
    for L in (a,b):
        if k<1: sc=.6+.4*k; r=L.resize((int(W*sc),int(H*sc)),Image.LANCZOS); img.alpha_composite(r,(int(W/2-W/2*sc),int(420-420*sc)))
        else: img.alpha_composite(L)
def cart(d,cx,cy,s=1.0,col="white"):
    d.line((cx-34*s,cy-30*s,cx-22*s,cy-30*s,cx-10*s,cy+12*s,cx+30*s,cy+12*s),fill=col,width=int(7*s))
    d.polygon([(cx-18*s,cy-18*s),(cx+38*s,cy-18*s),(cx+30*s,cy+6*s),(cx-12*s,cy+6*s)],fill=col)
    d.ellipse((cx-8*s,cy+20*s,cx+4*s,cy+32*s),fill=col); d.ellipse((cx+18*s,cy+20*s,cx+30*s,cy+32*s),fill=col)
def cta(img,lt,dy=0):
    """animação SEM texto apontando para o link da loja (canto inferior esquerdo); termina acima de y≈1500"""
    k=ease(lt/.35); lay=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(lay); cx=300
    pulse=(lt*1.4)%1.0
    d.ellipse((cx-60-pulse*70,1250+dy-60-pulse*70,cx+60+pulse*70,1250+dy+60+pulse*70),outline=(255,255,255,int(200*(1-pulse)*k)),width=6)
    d.ellipse((cx-62,1188+dy,cx+62,1312+dy),fill=RED+(int(255*k),)); cart(d,cx,1250+dy,1.0,(255,255,255,int(255*k)))
    for j in range(3):
        ph=(lt*1.6-j*.18)%1.0; y=1345+dy+ph*105; a=int(255*math.sin(math.pi*ph)*k)
        d.line((cx-34,y,cx,y+30,cx+34,y),fill=(255,255,255,a),width=14,joint="curve")
    sh=lay.filter(ImageFilter.GaussianBlur(10)); sh.putalpha(sh.getchannel("A").point(lambda v:int(v*.6))); 
    img.alpha_composite(Image.new("RGBA",(W,H),(0,0,0,0))); img.alpha_composite(sh); img.alpha_composite(lay)
def pill(img,text,cx,y,size=50,bg=(255,255,255,235),fg=(20,20,20),pad=34):
    f=F(900,size); parts=[p for p in EMO_RE.split(text) if p]; asc,_=f.getmetrics(); es=int(asc*.95)
    tw=sum(emoji(p,es).width if EMO_RE.fullmatch(p) else f.getlength(p) for p in parts)
    lay=Image.new("RGBA",(W,H),(0,0,0,0)); ImageDraw.Draw(lay).rounded_rectangle((cx-tw/2-pad,y,cx+tw/2+pad,y+size+36),(size+36)//2,fill=bg)
    img.alpha_composite(lay); rich(img,text,cx,y+10,f,stroke=0,fill=fg)
SFX=[]  # (tempo, tipo)
def sfx(t,k): SFX.append((round(t,3),k))
def typed(img,txt,y,t0,t,size=58,stroke=7): rich(img,txt,W/2,y,F(900,size),n=int(max(0,t-t0)*26),stroke=stroke)

# ---------- V1: plaquinhas + cortes no ritmo ----------
def v1():
    segs=[Seg("a",0.0,2.8,1.0,1.05,1.2,.5,.42),Seg("c",4.6,1.1,1,1.0,1.12,.5,.4),Seg("b",5.5,1.1,1,1.0,1.12,.5,.4),Seg("a",3.3,1.1,1,1.0,1.1,.5,.45),
          Seg("b",3.0,1.1,1,1.0,1.1,.5,.45),Seg("c",8.0,1.1,1,1.0,1.1,.5,.4),Seg("a",6.8,1.1,1,1.0,1.1,.5,.4),Seg("b",8.0,1.1,1,1.0,1.1,.5,.4),Seg("b",7.3,2.7,1,1.0,1.08,.5,.45)]
    st,T=starts(segs); CT=st[-1]
    for s in st[1:]: sfx(s,"thump")
    sfx(.05,"whoosh"); sfx(.2,"pop"); sfx(CT+.3,"ding")
    def f(t):
        i,lt=seg_at(segs,st,t); img=punch(segs[i].img(lt),lt); shade(img)
        if i==0: plaq(img,"OLHA ESSAS","COSTAS",t,1)
        if 0<i<len(segs)-1 and t>3.3: typed(img,"comprei e amei o detalhe 🖤",1290,3.4,t,50)
        if i==len(segs)-1: cta(img,t-CT)
        return img
    return f,T
# ---------- V2: 3 coisas que eu amei ----------
def v2():
    segs=[Seg("a",5.0,2.6,1,1.0,1.1,.5,.42),Seg("c",0.0,3.2,1,1.0,1.15,.5,.5),Seg("c",4.4,3.2,1,1.0,1.1,.5,.45),Seg("b",3.0,3.2,1,1.0,1.1,.5,.45),Seg("c",7.4,2.6,1,1.0,1.06,.5,.4)]
    st,T=starts(segs); CT=st[-1]; labels=[None,"TECIDO CANELADO","TRANÇADO NAS COSTAS","CAIMENTO PERFEITO"]
    sfx(.05,"whoosh"); sfx(.2,"pop")
    for k in (1,2,3): sfx(st[k],"thump"); sfx(st[k]+.25,"tick")
    sfx(CT+.3,"ding")
    def f(t):
        i,lt=seg_at(segs,st,t); img=punch(segs[i].img(lt),lt); shade(img)
        if i==0: plaq(img,"3 COISAS","QUE EU AMEI",t,2,250,450,150,105)
        elif i<4:
            k=ease(lt/.3); d=ImageDraw.Draw(img); cx=W/2; y=1240+(1-k)*40
            lay=Image.new("RGBA",(W,H),(0,0,0,0)); ld=ImageDraw.Draw(lay); f2=F(900,54); tw=ld.textlength(labels[i],font=f2)
            ld.rounded_rectangle((cx-tw/2-130,y,cx+tw/2+50,y+120),60,fill=(255,255,255,int(240*k)))
            ld.ellipse((cx-tw/2-120,y+10,cx-tw/2-20,y+110),fill=RED+(int(255*k),)); ld.text((cx-tw/2-70,y+60),str(i),font=F(900,60),fill=(255,255,255,int(255*k)),anchor="mm")
            ld.text((cx-tw/2,y+60),labels[i],font=f2,fill=(20,20,20,int(255*k)),anchor="lm"); img.alpha_composite(lay)
            for j in range(3): d.ellipse((W/2-60+j*60,1200+0,W/2-40+j*60,1220),fill=(255,255,255,255) if j<i else (255,255,255,90))
        else: cta(img,t-CT); typed(img,"vale cada detalhe 🖤",1010,CT+.2,t,52)
        return img
    return f,T
# ---------- V3: testei antes de indicar ----------
def v3():
    segs=[Seg("a",8.0,2.0,1,1.0,1.1,.5,.4),Seg("b",0.0,2.4,1,1.0,1.1,.5,.5),Seg("b",3.2,2.4,1,1.0,1.1,.5,.45),Seg("a",3.3,2.4,1,1.0,1.1,.5,.45),Seg("c",4.5,2.4,1,1.0,1.1,.5,.45),Seg("c",7.4,2.6,1,1.0,1.06,.5,.4)]
    st,T=starts(segs); CT=st[-1]; items=["SENTADA","ANDANDO","GIRANDO","COSTAS"]
    sfx(.05,"whoosh"); sfx(.2,"pop")
    for k in range(1,5): sfx(st[k],"thump"); sfx(st[k]+1.0,"check")
    sfx(CT+.2,"stamp"); sfx(CT+1.2,"ding")
    def f(t):
        i,lt=seg_at(segs,st,t); img=punch(segs[i].img(lt),lt); shade(img)
        if i==0: plaq(img,"TESTEI","ANTES DE INDICAR",t,3,250,450,170,90)
        if i>=1:
            lay=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(lay); n=min(4,i)
            for j in range(n):
                y=780+j*92; done=(j<i-1) or (j==i-1 and lt>1.0); k=ease((t-st[j+1])/.3)
                d.rounded_rectangle((70,y,560,y+80),40,fill=(0,0,0,int(150*k))); 
                d.ellipse((84,y+10,144,y+70),fill=(GREEN if done else (255,255,255))+(int(255*k),))
                if done: d.line((98,y+40,111,y+54,132,y+26),fill=(255,255,255,255),width=8)
                d.text((170,y+40),items[j],font=F(900,40),fill=(255,255,255,int(255*k)),anchor="lm")
            img.alpha_composite(lay)
        if i==5:
            k=ease((t-CT)/.25); sc=1.6-.6*k; lay=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(lay); f2=F(900,int(70*sc)); tw=d.textlength("APROVADO",font=f2)
            d.rounded_rectangle((790-tw/2-40,720,790+tw/2+40,720+int(86*sc)+60),24,outline=GREEN+(int(255*k),),width=10); d.text((790,720+(int(86*sc)+60)/2),"APROVADO",font=f2,fill=GREEN+(int(255*k),),anchor="mm")
            lay=lay.rotate(-6,center=(790,780)); img.alpha_composite(lay); cta(img,t-CT)
        return img
    return f,T
# ---------- V4: frente x costas ----------
def v4():
    A=Seg("c",7.4,2.6,1,1.0,1.05,.5,.4); B=Seg("a",1.2,2.7,1,1.0,1.1,.5,.4)
    segs=[Seg("a",1.2,2.6),Seg("a",1.2,2.8,1,1.0,1.15,.5,.42),Seg("b",7.3,2.7,1,1.0,1.08,.5,.45),Seg("c",7.4,3.0,1,1.0,1.05,.5,.4)]
    st,T=starts(segs); CT=st[3]+0.0
    sfx(.05,"whoosh"); sfx(.2,"pop"); sfx(st[1],"thump"); sfx(st[2],"thump"); sfx(st[3],"whoosh"); sfx(st[3]+.5,"ding")
    def splitimg(lt,x):
        l=A.img(lt%A.d); r=B.img(lt%B.d); im=r.copy(); im.paste(l.crop((0,0,int(x),H)),(0,0)); im=im.convert("RGBA"); d=ImageDraw.Draw(im)
        d.rectangle((x-4,0,x+4,H),fill="white"); d.ellipse((x-44,H/2-44,x+44,H/2+44),fill="white")
        d.polygon([(x-28,H/2),(x-10,H/2-16),(x-10,H/2+16)],fill=(30,30,30)); d.polygon([(x+28,H/2),(x+10,H/2-16),(x+10,H/2+16)],fill=(30,30,30)); return im
    def f(t):
        i,lt=seg_at(segs,st,t)
        if i==0:
            img=splitimg(t,W/2+30*math.sin(t*4)); shade(img); plaq(img,"FRENTE","OU COSTAS?",t,4,250,450,160,105)
            pill(img,"FRENTE 👀",270,1230,46) if t>.8 else None; pill(img,"COSTAS 🔥",810,1230,46) if t>.8 else None
        elif i in (1,2):
            img=punch(segs[i].img(lt),lt); shade(img); pill(img,"COSTAS 🔥" if i==1 else "FRENTE 👀",W/2,1230,56)
        else:
            x=lerp(0,W,ease(lt/.6)) if lt<.6 else W/2+14*math.sin((lt-.6)*9)*max(0,1-(lt-.6)/.8) if lt<1.4 else W/2
            img=splitimg(t,x if lt>=.6 else W/2*ease(lt/.6)+0); shade(img)
            if lt>.4: typed(img,"amo as duas 🖤",1110,st[3]+.4,t,60)
            if lt>1.0: cta(img,lt-1.0)
        return img
    return f,T
# ---------- V5: chat com a amiga ----------
def v5():
    pan=[Seg("a",3.3,2.6,1,1.0,1.15,.5,.5),Seg("b",5.5,2.6,1,1.0,1.12,.5,.45),Seg("c",4.6,2.6,1,1.0,1.1,.5,.45),Seg("a",6.8,2.8,1,1.0,1.1,.5,.4),Seg("b",8.0,2.2,1,1.0,1.1,.5,.4)]
    st,T=starts(pan)
    msgs=[(.5,True,"amiga, olha o que chegou 😍"),(2.6,False,"QUEM É ESSA?? 😱"),(4.6,False,"esse trançado nas costas 🔥"),(6.9,True,"amei demais, ficou lindo 🖤"),(9.3,False,"MANDA O LINK! 🛒")]
    CT=10.0; T=13.0
    for m in msgs: sfx(m[0],"msg")
    sfx(.05,"whoosh"); sfx(CT,"ding")
    def f(t):
        i,lt=seg_at(pan,st,min(t,st[-1]+pan[-1].d-.01)); v=pan[i].img(lt,W,800); img=Image.new("RGBA",(W,H),(14,16,28,255)); img.alpha_composite(v.convert("RGBA"),(0,0))
        if lt<.1: img.alpha_composite(Image.new("RGBA",(W,H),(255,255,255,100)),(0,0))
        d=ImageDraw.Draw(img); d.rectangle((0,800,W,860),fill=(24,28,46)); rich(img,"amiga ❤️",230,806,F(800,32),stroke=0)
        y=885
        for (a,me,txt) in msgs:
            k=ease((t-a)/.3)
            if k<=0: continue
            f2=F(700,32); tw=sum(emoji(p,30).width if EMO_RE.fullmatch(p) else f2.getlength(p) for p in [q for q in EMO_RE.split(txt) if q])+56; h=60
            x0=(W-tw-50) if me else 50; yy=y+(1-k)*24; col=(108,92,231) if me else (44,48,72)
            lay=Image.new("RGBA",(W,H),(0,0,0,0)); ImageDraw.Draw(lay).rounded_rectangle((x0,yy,x0+tw,yy+h),36,fill=col+(int(255*k),)); img.alpha_composite(lay)
            rich(img,txt,x0+tw/2,yy+9,f2,stroke=0,fill=(255,255,255)); y+=70
        if t>CT: cta(img,t-CT,40)
        return img
    return f,T
f,T=[None,v1,v2,v3,v4,v5][P]()
out=sys.stdout.buffer
for n in range(int(T*30)): out.write(f(n/30).convert("RGB").tobytes())
json.dump({"total":T,"sfx":SFX},open(os.path.join(D,f"vest{P}.json"),"w"))
