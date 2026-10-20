from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops, ImageEnhance
import os,sys,math,json
import numpy as np
D=os.path.dirname(os.path.abspath(__file__)); S=os.path.dirname(D)
W,H,FPS,N=1080,1920,30,594; T=N/FPS
NAVY=(10,16,30); GOLD=(214,171,84); WHITE=(245,247,250)
ease=lambda p:(lambda q:q*q*(3-2*q))(min(1,max(0,p))); lerp=lambda a,b,p:a+(b-a)*p
F=lambda w,s:ImageFont.truetype(os.path.join(S,f"mont{w}.ttf"),s)
# (início, fim, [(linha, [palavras douradas])...], y)
CAPS=[(0.3,3.3,[("ALTA PERFORMANCE",["PERFORMANCE"]),("NÃO É TALENTO.",["TALENTO."])],300),
      (3.5,6.6,[("É REPETIÇÃO.",["REPETIÇÃO."]),("TODO SANTO DIA.",[])],300),
      (6.8,9.9,[("QUANDO PESA,",[]),("VOCÊ NÃO DESISTE.",["NÃO","DESISTE."])],300),
      (10.1,13.2,[("VOCÊ AJUSTA",["AJUSTA"]),("E CONTINUA.",[])],300),
      (13.4,16.4,[("NA ACADEMIA.",[]),("NA GESTÃO. NA VIDA.",["GESTÃO.","VIDA."])],300)]
END=(16.6,T)
VIG=Image.new("L",(W//8,H//8),0); ImageDraw.Draw(VIG).ellipse((-30,-20,W//8+30,H//8+20),fill=255); VIG=VIG.filter(ImageFilter.GaussianBlur(14)).resize((W,H),Image.BILINEAR)
def grad(h,top=True,a=190):
    g=Image.new("L",(1,h)); g.putdata([int(a*(1-i/h)**1.6) if top else int(a*(i/h)**1.6) for i in range(h)]); return g.resize((W,h))
GT=grad(760,True); GB=grad(620,False,170)
def cap(img,lines,y,k,t):
    lay=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(lay); yy=y
    for li,(txt,hl) in enumerate(lines):
        kk=ease((k-li*.18)/.35); a=int(255*kk); off=int((1-kk)*40)
        f=F(900,88 if len(txt)<14 else 74); words=txt.split(); tw=sum(d.textlength(w+" ",font=f) for w in words)-d.textlength(" ",font=f)
        x=(W-tw)/2
        for w in words:
            col=(GOLD if w in hl else WHITE)+(a,)
            d.text((x+3,yy+off+4),w,font=f,fill=(0,0,0,int(a*.6)))
            d.text((x,yy+off),w,font=f,fill=col); x+=d.textlength(w+" ",font=f)
        yy+=112
    # filete dourado
    wl=int(300*ease(k/.5)); d.rectangle((W/2-wl/2,yy+14,W/2+wl/2,yy+19),fill=GOLD+(255,))
    img.alpha_composite(lay)
def frame(t):
    i=min(N,int(t*FPS)+1); im=Image.open(os.path.join(D,"src/%04d.jpg"%i)).convert("RGB")
    z=1.0+0.07*t/T; cw,ch=W/z,H/z; im=im.crop((int((W-cw)/2),int((H-ch)/2)-int(30*t/T),int((W+cw)/2),int((H+ch)/2)-int(30*t/T))).resize((W,H),Image.BICUBIC)
    im=ImageEnhance.Contrast(im).enhance(1.12); im=ImageEnhance.Color(im).enhance(.9)
    # tom frio-dourado nas sombras
    tint=Image.new("RGB",(W,H),(10,20,48)); im=ImageChops.blend(im,ImageChops.multiply(im,Image.new("RGB",(W,H),(215,225,255))),.35)
    dark=Image.new("RGB",(W,H),(6,9,18)); im=Image.composite(im,dark,Image.eval(VIG,lambda v:int(165+v*90/255)))
    im=im.convert("RGBA")
    top=Image.new("RGBA",(W,760),NAVY+(0,)); top.putalpha(GT); im.alpha_composite(top,(0,0))
    bot=Image.new("RGBA",(W,620),NAVY+(0,)); bot.putalpha(GB); im.alpha_composite(bot,(0,H-620))
    d=ImageDraw.Draw(im)
    # marca discreta
    if t<END[0]:
        d.text((80,110),"ALTA PERFORMANCE",font=F(800,24),fill=GOLD); d.line((80,150,W-80,150),fill=(60,74,110),width=2)
        # barra de progresso
        d.rectangle((80,152,80+int((W-160)*t/T),155),fill=GOLD)
    for a,b,lines,y in CAPS:
        if a<=t<b:
            k=(t-a)/.6; out=ease((b-t)/.25)
            tmp=Image.new("RGBA",(W,H),(0,0,0,0)); cap(tmp,lines,y,k,t)
            if out<1: tmp.putalpha(tmp.getchannel("A").point(lambda v:int(v*out)))
            im.alpha_composite(tmp)
            if t-a<.07: im.alpha_composite(Image.new("RGBA",(W,H),(255,255,255,70)))
    if t>=END[0]:
        lt=t-END[0]; k=ease(lt/.5)
        ov=Image.new("RGBA",(W,H),NAVY+(int(215*k),)); im.alpha_composite(ov)
        d=ImageDraw.Draw(im)
        def ctr(txt,y,f,col,a=1.0,sp=0):
            d.text(((W-d.textlength(txt,font=f))/2,y+int((1-ease((lt-.15)/.4))*30)),txt,font=f,fill=col+(int(255*min(1,max(0,(lt-.15)/.4)*a)),))
        ctr("CONSTÂNCIA",700,F(900,100),WHITE); ctr("GERA RESULTADO.",820,F(900,86),GOLD)
        wl=int(360*ease((lt-.5)/.4)); d.rectangle((W/2-wl/2,960,W/2+wl/2,965),fill=GOLD)
        if lt>.9:
            kk=ease((lt-.9)/.4); 
            f=F(900,56); txt="COSME ALVES"; d.text(((W-d.textlength(txt,font=f))/2,1030),txt,font=f,fill=WHITE+(int(255*kk),))
            f=F(700,30); txt="GESTÃO  •  PERFORMANCE  •  ALINHAMENTO"; d.text(((W-d.textlength(txt,font=f))/2,1112),txt,font=f,fill=GOLD+(int(255*kk),))
        if lt>1.5:
            kk=ease((lt-1.5)/.4); f=F(800,34); txt="SALVE E COMPARTILHE COM QUEM TREINA COM VOCÊ"
            d.text(((W-d.textlength(txt,font=f))/2,1260),txt,font=f,fill=(170,180,205,int(255*kk)))
    if t<.3: im.alpha_composite(Image.new("RGBA",(W,H),(0,0,0,int(255*(1-t/.3)))))
    if t>T-.4: im.alpha_composite(Image.new("RGBA",(W,H),(0,0,0,int(255*(t-(T-.4))/.4))))
    return im.convert("RGB")
out=sys.stdout.buffer
for f in range(N): out.write(frame(f/FPS).tobytes())
