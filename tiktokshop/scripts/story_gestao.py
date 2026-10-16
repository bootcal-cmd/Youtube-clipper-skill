src=open('car.py').read().split("# 1 capa")[0]
exec(src)
W,H=1080,1920
def snew():
    im=Image.new("RGB",(W,H),BG); px=Image.new("RGB",(W,H),BG2)
    m=Image.new("L",(W,H),0); ImageDraw.Draw(m).ellipse((200,-300,1500,700),fill=160)
    return Image.composite(px,im,m.filter(ImageFilter.GaussianBlur(180)))
def top(d,n):
    d.text((80,250),"ALTA PERFORMANCE",font=F(800,26),fill=GOLD)
    for i in range(3): d.rounded_rectangle((W-80-3*70+i*74,258,W-80-3*70+i*74+64,266),4,fill=GOLD if i<n else LINE)
H_=1920
# story 1: gancho + enquete
im=snew(); d=ImageDraw.Draw(im); top(d,1)
y=text(d,"Se você sumir 3 dias, sua operação para?",80,380,F(900,84),mw=920,ls=1.14,hl=("para?",))
# funil mini
cx=540; t=y+130
d.polygon([(380,t),(700,t),(600,t+150),(480,t+150)],outline=RED,fill=(40,24,36),width=4); d.rectangle((480,t+150,600,t+215),fill=(40,24,36),outline=RED,width=4)
for x in (410,490,570,650): d.ellipse((x-16,t-56,x+16,t-24),fill=WHITE)
person(d,540,t+290,.6,GOLD); d.text((540,t+360),"VOCÊ = GARGALO?",font=F(800,26),fill=RED,anchor="mm")
# espaço p/ figurinha de enquete
im.save("story1.png")
# story 2: tease
im=snew(); d=ImageDraw.Draw(im); top(d,2)
y=text(d,"A maioria dos líderes está no Nível 1 e nem sabe.",80,380,F(900,76),mw=920,ls=1.15,hl=("nível","1"))
yy=y+50
for i,(lab,c,op) in enumerate([("NÍVEL 1","“Analise e decidimos juntos.”",1),("NÍVEL 2","“Decida, mas aguarde meu OK.”",.55),("NÍVEL 3","",.3)]):
    a=int(255*op); b=yy+i*190; rr(d,(80,b,1000,b+160),28,fill=BG2,outline=GOLD if i==0 else LINE,w=3)
    d.ellipse((112,b+40,192,b+120),fill=GOLD if i==0 else LINE); d.text((152,b+80),str(i+1),font=F(900,44),fill=BG if i==0 else MUTE,anchor="mm")
    d.text((224,b+34),lab,font=F(900,38),fill=GOLD if i==0 else MUTE); d.text((224,b+92),c,font=F(700,30),fill=WHITE if i==0 else MUTE)
    if i==2:
        rr(d,(224,b+92,520,b+112),10,fill=LINE)
        d.text((960,b+80),"🔒".replace("🔒",""),font=F(800,30),fill=GOLD,anchor="rm")
        rr(d,(760,b+52,960,b+108),28,outline=GOLD,w=3); d.text((860,b+80),"NO POST",font=F(800,26),fill=GOLD,anchor="mm")
text(d,"O Nível 3 — onde mora a alta performance — está no post novo do feed.",80,yy+620,F(700,38),fill=MUTE,mw=900,ls=1.3,hl=("nível","3"))
im.save("story2.png")
# story 3: CTA
im=snew(); d=ImageDraw.Draw(im); top(d,3)
y=text(d,"Salve antes da sua próxima reunião.",80,380,F(900,84),mw=920,ls=1.14,hl=("salve",))
y=text(d,"Os 3 níveis de delegação + como cobrar sem ser o chefe chato.",80,y+30,F(500,40),fill=MUTE,mw=900,ls=1.35)
# mini capa do post (miniatura)
im2=Image.open("slide1.png").resize((540,675)); mask=Image.new("L",im2.size,0); ImageDraw.Draw(mask).rounded_rectangle((0,0,540,675),28,fill=255)
px=300; py=y+60; sh=Image.new("RGBA",(W,H),(0,0,0,0)); ImageDraw.Draw(sh).rounded_rectangle((px-4,py-4,px+544,py+679),30,outline=GOLD+(255,),width=5)
im.paste(im2,(px,py),mask); im.paste(Image.alpha_composite(im.convert("RGBA"),sh).convert("RGB"))
d=ImageDraw.Draw(im)
rr(d,(250,py+715,830,py+800),43,fill=GOLD); d.text((540,py+757),"TOQUE NA FOTO ↑ E LEIA".replace(" ↑",""),font=F(900,30),fill=BG,anchor="mm")
d.text((540,py+850),"@oficialcosmelima",font=F(800,34),fill=GOLD,anchor="mm")
im.save("story3.png")
