from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageChops
import os,sys,math,random
D=os.path.dirname(os.path.abspath(__file__)); S=os.path.dirname(D)
W,H,FPS=1080,1920,30
ROSE=(226,160,150); GOLD=(222,184,120); CREAM=(252,244,236); DEEP=(40,22,30)
ease=lambda p:(lambda q:q*q*(3-2*q))(min(1,max(0,p))); lerp=lambda a,b,p:a+(b-a)*p
F=lambda w,s:ImageFont.truetype(os.path.join(S,f"mont{w}.ttf"),s)
SERIF=lambda s:ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSerif-BoldItalic.ttf",s)
EMO=ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf",109)
# (arquivo, olho x, olho y relativos, linha1, linha2)
SL=[("ffe0626d",.60,.48,"Cílios curvados,","olhar aberto."),
    ("33b4e8e7",.58,.45,"Efeito rímel","sem rímel."),
    ("4cdaa92c",.55,.45,"Curvatura natural,","dia e noite."),
    ("129fc009",.34,.47,"Acorde com o","olhar pronto.")]
SEG=3.3; T_END=3.6; TOTAL=SEG*4+T_END
IM=[Image.open(os.path.join(D,f"r_{s[0]}.jpg")) for s in SL]
GT=Image.new("L",(1,620)); GT.putdata([int(200*(1-i/620)**1.5) for i in range(620)]); GT=GT.resize((W,620))
GB=Image.new("L",(1,700)); GB.putdata([int(215*(i/700)**1.4) for i in range(700)]); GB=GB.resize((W,700))
def shot(i,lt):
    im=IM[i]; fx,fy=SL[i][1],SL[i][2]; z=lerp(1.25,1.65,ease(lt/SEG)); h=im.height/z*1.0; w=h*W/H
    cx=im.width*fx+ (lt-SEG/2)*40; cy=im.height*fy+60
    cx=min(max(cx,w/2),im.width-w/2); cy=min(max(cy,h/2),im.height-h/2)
    c=im.crop((int(cx-w/2),int(cy-h/2),int(cx+w/2),int(cy+h/2))).resize((W,H),Image.LANCZOS)
    c=ImageEnhance.Contrast(c).enhance(1.08); c=ImageEnhance.Color(c).enhance(1.06)
    return c.convert("RGBA")
def spark(img,cx,cy,r,a):
    lay=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(lay); col=(255,246,225,int(255*a))
    d.polygon([(cx,cy-r),(cx+r*.14,cy-r*.14),(cx+r,cy),(cx+r*.14,cy+r*.14),(cx,cy+r),(cx-r*.14,cy+r*.14),(cx-r,cy),(cx-r*.14,cy-r*.14)],fill=col)
    g=lay.filter(ImageFilter.GaussianBlur(8)); img.alpha_composite(g); img.alpha_composite(lay)
def text2(img,l1,l2,lt):
    lay=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(lay)
    for k,(t,f,col,y) in enumerate(((l1,F(900,84),CREAM,1380),(l2,SERIF(112),(255,208,198),1490))):
        kk=ease((lt-.15-k*.18)/.35); a=int(255*kk); off=int((1-kk)*40); tw=d.textlength(t,font=f)
        d.text(((W-tw)/2+3,y+off+4),t,font=f,fill=(0,0,0,int(a*.85))); d.text(((W-tw)/2,y+off),t,font=f,fill=col+(a,))
    wl=int(240*ease((lt-.5)/.4)); d.rectangle((W/2-wl/2,1650,W/2+wl/2,1654),fill=GOLD+(255,))
    img.alpha_composite(lay)
def tag(img,lt):
    k=ease(lt/.4); d=ImageDraw.Draw(img); txt="LASH LIFTING"; f=F(900,34); tw=d.textlength(txt,font=f)+90
    x0=(W-tw)/2; y=170-(1-k)*30
    d.rounded_rectangle((x0,y,x0+tw,y+78),39,fill=ROSE+(int(235*k),))
    d.text((W/2,y+39),txt,font=f,fill=DEEP+(int(255*k),),anchor="mm")
rnd=random.Random(7)
def frame(t):
    if t<SEG*4:
        i=int(t//SEG); lt=t-i*SEG; img=shot(i,lt)
        top=Image.new("RGBA",(W,620),DEEP+(0,)); top.putalpha(GT); img.alpha_composite(top,(0,0))
        bot=Image.new("RGBA",(W,700),DEEP+(0,)); bot.putalpha(GB); img.alpha_composite(bot,(0,H-700))
        tag(img,lt); text2(img,SL[i][3],SL[i][4],lt)
        # brilhos no olho
        for j in range(3):
            ph=(lt*1.3+j*.37)%1.0; a=math.sin(math.pi*ph)
            if a>0: spark(img,int(W*(.35+.3*((j*.37+i*.13)%1))),int(760+120*math.sin(j*2+i)),int(34+30*a),a)
        if lt<.12: img.alpha_composite(Image.new("RGBA",(W,H),(255,240,230,int(190*(1-lt/.12)))))
        if i==0 and t<.3: img.alpha_composite(Image.new("RGBA",(W,H),(0,0,0,int(255*(1-t/.3)))))
        # barra de progresso discreta
        d=ImageDraw.Draw(img); d.rectangle((60,120,60+int((W-120)*t/TOTAL),124),fill=GOLD+(255,))
        return img.convert("RGB")
    lt=t-SEG*4; img=Image.new("RGBA",(W,H),DEEP+(255,)); d=ImageDraw.Draw(img)
    for r in range(8): d.ellipse((540-760+r*70,720-760+r*70,540+760-r*70,720+760-r*70),fill=(40+r*7,22+r*3,30+r*4))
    def c(txt,y,f,col,t0):
        k=ease((lt-t0)/.4); tw=d.textlength(txt,font=f); d.text(((W-tw)/2,y+(1-k)*40),txt,font=f,fill=col+(int(255*k),))
    c("Quer esse",470,F(900,96),CREAM,.1); c("olhar?",590,SERIF(190),ROSE,.3)
    wl=int(320*ease((lt-.7)/.4)); d.rectangle((W/2-wl/2,860,W/2+wl/2,865),fill=GOLD)
    if lt>1.0:
        k=ease((lt-1.0)/.4); pill=Image.new("RGBA",(W,H),(0,0,0,0)); pd=ImageDraw.Draw(pill); pd.rounded_rectangle((170,950,910,1070),60,fill=ROSE+(int(255*k),)); img.alpha_composite(pill)
        d=ImageDraw.Draw(img); txt="AGENDE SEU HORÁRIO"; f=F(900,46); d.text((W/2,1010),txt,font=f,fill=DEEP+(int(255*k),),anchor="mm")
    if lt>1.5:
        k=ease((lt-1.5)/.4); f=F(700,38); txt="chame no direct"; tw=d.textlength(txt,font=f); d.text(((W-tw)/2,1130),txt,font=f,fill=CREAM+(int(255*k),))
        f=F(800,30); txt="LASH DESIGNER"; tw=d.textlength(txt,font=f); d.text(((W-tw)/2,1230),txt,font=f,fill=GOLD+(int(255*k),))
    for j in range(5): 
        ph=(lt*.9+j*.21)%1; a=math.sin(math.pi*ph); spark(img,int(160+j*190),int(330+60*math.sin(j*2.3)),int(26+22*a),a)
    if lt<.12: img.alpha_composite(Image.new("RGBA",(W,H),(255,240,230,int(190*(1-lt/.12)))))
    if t>TOTAL-.4: img.alpha_composite(Image.new("RGBA",(W,H),(0,0,0,int(255*(t-(TOTAL-.4))/.4))))
    return img.convert("RGB")
out=sys.stdout.buffer
for f in range(int(TOTAL*FPS)): out.write(frame(f/FPS).tobytes())
