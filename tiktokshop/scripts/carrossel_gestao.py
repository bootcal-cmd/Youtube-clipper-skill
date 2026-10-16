from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os, math
S="/tmp/claude-0/-home-user-Youtube-clipper-skill/f05dfe21-700d-5c7c-a427-931b58f48d32/scratchpad/"
W,H=1080,1350
BG=(10,16,30); BG2=(18,28,52); GOLD=(214,171,84); WHITE=(245,247,250); MUTE=(150,162,188); RED=(226,84,84); GRN=(72,196,140); LINE=(44,58,92)
def F(w,s): return ImageFont.truetype(S+f"mont{w}.ttf",s)
def new():
    im=Image.new("RGB",(W,H),BG); px=Image.new("RGB",(W,H),BG2)
    m=Image.new("L",(W,H),0); ImageDraw.Draw(m).ellipse((300,-500,1500,500),fill=150)
    im=Image.composite(px,im,m.filter(ImageFilter.GaussianBlur(160)))
    return im
def wrap(d,t,f,mw):
    out=[];cur=""
    for w in t.split():
        if d.textlength((cur+" "+w).strip(),font=f)<=mw: cur=(cur+" "+w).strip()
        else: out.append(cur);cur=w
    out.append(cur);return out
def text(d,t,x,y,f,fill=WHITE,mw=900,ls=1.28,hl=()):
    """hl: palavras em dourado"""
    for ln in wrap(d,t,f,mw):
        cx=x
        for w in ln.split():
            c=GOLD if w.strip(".,:?!").lower() in hl else fill
            d.text((cx,y),w,font=f,fill=c); cx+=d.textlength(w+" ",font=f)
        y+=int(f.size*ls)
    return y
def frame(n,tag):
    im=new(); d=ImageDraw.Draw(im)
    d.text((80,70),"ALTA PERFORMANCE",font=F(800,24),fill=GOLD)
    d.text((W-80-d.textlength(f"{n:02d} / 08",font=F(700,24)),70),f"{n:02d} / 08",font=F(700,24),fill=MUTE)
    d.line((80,112,W-80,112),fill=LINE,width=2)
    d.text((80,H-90),tag,font=F(700,24),fill=MUTE)
    if n<8:
        t="ARRASTE"; tw=d.textlength(t,font=F(800,24)); d.text((W-80-tw-44,H-90),t,font=F(800,24),fill=GOLD)
        x=W-80-30; y=H-77; d.line((x-6,y,x+24,y),fill=GOLD,width=4); d.polygon([(x+30,y),(x+16,y-10),(x+16,y+10)],fill=GOLD)
    return im,d
def rr(d,b,r,fill=None,outline=None,w=3): d.rounded_rectangle(b,r,fill=fill,outline=outline,width=w)
def person(d,cx,cy,s=1.0,col=WHITE):
    d.ellipse((cx-22*s,cy-60*s,cx+22*s,cy-16*s),fill=col); d.rounded_rectangle((cx-38*s,cy-8*s,cx+38*s,cy+70*s),int(30*s),fill=col)
def arrow(d,a,b,col,w=5,h=16):
    d.line((*a,*b),fill=col,width=w); ang=math.atan2(b[1]-a[1],b[0]-a[0])
    d.polygon([b,(b[0]-h*math.cos(ang-.45),b[1]-h*math.sin(ang-.45)),(b[0]-h*math.cos(ang+.45),b[1]-h*math.sin(ang+.45))],fill=col)
def curve(d,pts,col,w=8):
    d.line(pts,fill=col,width=w,joint="curve")
    for p in (pts[0],pts[-1]): d.ellipse((p[0]-w/2,p[1]-w/2,p[0]+w/2,p[1]+w/2),fill=col)
def save(im,n): im.save(f"slide{n}.png")

# 1 capa
im,d=frame(1,"@oficialcosmelima • gestão de alta performance")
d.text((80,170),"LIDERANÇA",font=F(800,28),fill=GOLD)
y=text(d,"Sua equipe é de alta performance ou só funciona quando você está olhando?",80,230,F(900,76),mw=920,ls=1.16,hl=("alta","performance"))
y=text(d,"A diferença sutil entre liderar pelo contexto e a armadilha do microgerenciamento.",80,y+26,F(500,36),fill=MUTE,mw=860,ls=1.35)
# gráfico
gx0,gy0,gx1,gy1=100,860,980,1180
d.line((gx0,gy0,gx0,gy1),fill=LINE,width=3); d.line((gx0,gy1,gx1,gy1),fill=LINE,width=3)
for i in range(1,4): d.line((gx0,gy1-i*80,gx1,gy1-i*80),fill=(26,38,66),width=2)
xs=[gx0+i*(gx1-gx0-30)/20 for i in range(21)]
lead=[gy0+20+ (gy1-gy0-40)*(1/(1+math.exp(-(i-10)/2.4))) for i in range(21)]
team=[gy1-20-(gy1-gy0-40)*(1/(1+math.exp(-(i-10)/2.4))) for i in range(21)]
curve(d,list(zip(xs,lead)),RED,8); curve(d,list(zip(xs,team)),GOLD,8)
d.text((gx0+10,gy0-48),"Esforço do líder",font=F(800,28),fill=RED); d.text((gx1-290,gy0-48),"Autonomia do time",font=F(800,28),fill=GOLD)
d.text((gx1-60,gy1+14),"tempo",font=F(500,22),fill=MUTE)
save(im,1)

# 2 dor
im,d=frame(2,"@oficialcosmelima • gestão de alta performance")
d.text((80,170),"A DOR",font=F(800,28),fill=GOLD)
y=text(d,"Você tira 3 dias de folga e a operação trava?",80,225,F(900,62),mw=920,ls=1.16,hl=("trava?",))
# calendário + gargalo
y+=70
rr(d,(80,y+40,420,y+250),22,fill=BG2,outline=LINE)
d.text((110,y+58),"FOLGA",font=F(800,24),fill=MUTE)
for i in range(3): rr(d,(110+i*100,y+110,190+i*100,y+190),14,fill=GOLD); d.text((150+i*100,y+150),str(i+1),font=F(900,40),fill=BG,anchor="mm")
# funil
cx=700; top=y+40
for i,(w,yy) in enumerate([(260,top),(200,top+60),(140,top+120)]): pass
d.polygon([(560,top),(840,top),(740,top+140),(660,top+140)],outline=RED,fill=(40,24,36))
d.rectangle((660,top+140,740,top+200),fill=(40,24,36),outline=RED)
for i,x in enumerate((590,650,710,770)): d.ellipse((x-14,top-40,x+14,top-12),fill=WHITE)
person(d,700,top+250,0.55,GOLD)
d.text((700,top+335),"VOCÊ = GARGALO",font=F(800,24),fill=RED,anchor="mm")
y2=y+380
y2=text(d,"O problema não é a capacidade técnica do seu time. É o seu modelo de comando.",80,y2+30,F(700,40),mw=900,ls=1.3,hl=("modelo","comando."))
y2=text(d,"Centralizar decisões dá uma falsa sensação de segurança, mas transforma o líder no maior gargalo do projeto.",80,y2+14,F(500,34),fill=MUTE,mw=900,ls=1.35)
save(im,2)

# 3 virada
im,d=frame(3,"@oficialcosmelima • gestão de alta performance")
d.text((80,170),"A VIRADA DE CHAVE",font=F(800,28),fill=GOLD)
y=text(d,"Alta performance não nasce de vigilância. Nasce do Comando por Intenção.",80,225,F(900,60),mw=920,ls=1.16,hl=("comando","intenção."))
y+=40
items=[("O QUÊ","precisa ser entregue",GOLD,True),("POR QUÊ","aquilo importa",GOLD,True),("COMO","a ponta decide",GRN,False)]
for i,(a,b,c,own) in enumerate(items):
    yy=y+i*150; rr(d,(80,yy,1000,yy+124),26,fill=BG2,outline=c,w=3)
    d.ellipse((108,yy+22,188,yy+102),fill=c); d.text((148,yy+62),str(i+1),font=F(900,40),fill=BG,anchor="mm")
    d.text((220,yy+20),a,font=F(900,44),fill=c); d.text((220,yy+74),b,font=F(500,32),fill=WHITE)
    tag="VOCÊ DEFINE" if own else "O TIME DECIDE"; tw=d.textlength(tag,font=F(800,22))
    rr(d,(1000-tw-70,yy+40,970,yy+84),22,outline=c,w=2); d.text((985-tw/2-20+ (tw+60-tw)/2 -15,yy+62),tag,font=F(800,22),fill=c,anchor="mm") if False else d.text((1000-tw/2-50,yy+62),tag,font=F(800,22),fill=c,anchor="mm")
text(d,"Você dá o destino e o motivo. Liberdade total no caminho.",80,y+480,F(600,34) if os.path.exists(S+"mont600.ttf") else F(700,34),fill=MUTE,mw=900,ls=1.35)
save(im,3)

# 4 alinhamento x autonomia
im,d=frame(4,"@oficialcosmelima • gestão de alta performance")
d.text((80,170),"O ERRO CLÁSSICO",font=F(800,28),fill=GOLD)
y=text(d,"A regra do Alinhamento × Autonomia",80,225,F(900,62),mw=920,ls=1.16,hl=("alinhamento","autonomia"))
# dois painéis
py=y+30
rr(d,(80,py,520,py+360),26,fill=BG2,outline=RED); rr(d,(560,py,1000,py+360),26,fill=BG2,outline=GRN)
d.text((300,py+34),"“SOLTAR NA SELVA”",font=F(800,24),fill=RED,anchor="mm"); d.text((780,py+34),"AUTONOMIA REAL",font=F(800,24),fill=GRN,anchor="mm")
import random; r=random.Random(3); x0,y0=100,py+70
for i in range(6):
    a=(r.randint(120,480),r.randint(py+110,py+320)); b=(a[0]+r.randint(-90,90),a[1]+r.randint(-60,60)); b=(min(500,max(110,b[0])),min(py+330,max(py+100,b[1]))); arrow(d,a,b,RED,4,12)
d.polygon([(600,py+330),(640,py+90),(920,py+90),(960,py+330)],fill=(30,44,74))
d.line((600,py+330,640,py+90),fill=GOLD,width=6); d.line((960,py+330,920,py+90),fill=GOLD,width=6)
d.line((780,py+330,780,py+100),fill=LINE,width=3)
arrow(d,(740,py+310),(790,py+140),GRN,6,18); arrow(d,(830,py+300),(800,py+180),GRN,4,12) if False else None
d.text((300,py+388),"",font=F(500,20))
y=py+400
y=text(d,"Dar autonomia não é soltar na selva — isso gera caos.",80,y,F(700,38),mw=900,ls=1.3)
rr(d,(80,y+20,1000,y+20+232),24,fill=BG2,outline=GOLD)
d.text((110,y+38),"AUTONOMIA REAL EXIGE ALINHAMENTO NAS BORDAS:",font=F(800,24),fill=GOLD)
for i,t in enumerate(["Metas claras","Prazos inegociáveis","Limites de segurança definidos"]):
    d.ellipse((112,y+92+i*46,134,y+114+i*46),fill=GOLD); d.text((152,y+88+i*46),t,font=F(700,32),fill=WHITE)
save(im,4)

# 5 delegação 1-2
im,d=frame(5,"@oficialcosmelima • gestão de alta performance")
d.text((80,170),"FRAMEWORK • PARTE 1",font=F(800,28),fill=GOLD)
y=text(d,"Como passar o bastão na prática",80,225,F(900,62),mw=920,ls=1.16)
rr(d,(80,y+30,430,y+82),26,fill=GOLD); d.text((255,y+56),"📌 SALVE ESTE SLIDE".replace("📌 ",""),font=F(800,24),fill=BG,anchor="mm")
y+=130
cards=[(1,"EXECUÇÃO GUIADA","“Analise o problema, traga os dados e decidimos juntos.”","Para juniores ou processos novos."),
       (2,"RECOMENDAÇÃO","“Analise o problema, me diga qual decisão pretende tomar e aguarde meu OK.”","Você valida, o time propõe.")]
for i,(n,t,q,s) in enumerate(cards):
    yy=y+i*340; rr(d,(80,yy,1000,yy+310),28,fill=BG2,outline=LINE)
    d.rounded_rectangle((80,yy,100+8,yy+310),4,fill=GOLD)
    d.ellipse((130,yy+30,210,yy+110),fill=GOLD); d.text((170,yy+70),str(n),font=F(900,44),fill=BG,anchor="mm")
    d.text((236,yy+52),"NÍVEL "+str(n),font=F(800,24),fill=GOLD); d.text((236,yy+78),t,font=F(900,34),fill=WHITE)
    yq=text(d,q,130,yy+135,F(700,32),mw=830,ls=1.3)
    d.text((130,yy+265),s,font=F(500,26),fill=MUTE)
save(im,5)

# 6 nível 3
im,d=frame(6,"@oficialcosmelima • gestão de alta performance")
d.text((80,170),"FRAMEWORK • PARTE 2",font=F(800,28),fill=GOLD)
y=text(d,"Onde mora a alta performance",80,225,F(900,62),mw=920,ls=1.16,hl=("alta","performance"))
yy=y+30; rr(d,(80,yy,1000,yy+330),28,fill=BG2,outline=GOLD,w=4)
d.ellipse((130,yy+30,210,yy+110),fill=GOLD); d.text((170,yy+70),"3",font=F(900,44),fill=BG,anchor="mm")
d.text((236,yy+52),"NÍVEL 3",font=F(800,24),fill=GOLD); d.text((236,yy+78),"AUTONOMIA TOTAL",font=F(900,34),fill=WHITE)
text(d,"“Tome a decisão, resolva o incidente e apenas me informe o resultado depois.”",130,yy+140,F(700,34),mw=830,ls=1.3)
# escada
sy=yy+430
for i in range(3):
    x=120+i*290; h=70+i*70; col=[LINE,(120,104,60),GOLD][i]
    rr(d,(x,sy+210-h,x+260,sy+210),14,fill=col); d.text((x+130,sy+210-h/2),f"NÍVEL {i+1}",font=F(800,26),fill=WHITE if i<2 else BG,anchor="mm")
arrow(d,(200,sy+110),(560,sy+20),GRN,6,20); arrow(d,(560,sy+20),(900,sy-60),GRN,6,20)
text(d,"O segredo: mover seu time do Nível 1 ao Nível 3 o mais rápido possível.",80,sy+250,F(700,36),mw=900,ls=1.3,hl=("nível","3"))
save(im,6)

# 7 cobrança
im,d=frame(7,"@oficialcosmelima • gestão de alta performance")
d.text((80,170),"COBRAR SEM SER O CHEFE CHATO",font=F(800,28),fill=GOLD)
y=text(d,"A cobrança muda de lugar.",80,225,F(900,66),mw=920,ls=1.16)
y=text(d,"Pare de cobrar tarefas soltas no WhatsApp o dia inteiro. Crie rituais de cadência:",80,y+20,F(500,34),fill=MUTE,mw=900,ls=1.35)
yy=y+30
rr(d,(80,yy,1000,yy+170),26,fill=BG2,outline=LINE); d.text((120,yy+26),"SEMANAL",font=F(800,22),fill=GOLD)
d.text((120,yy+62),"15 minutos",font=F(900,44),fill=WHITE); d.text((120,yy+118),"no início da semana: travar prioridades",font=F(500,28),fill=MUTE)
rr(d,(80,yy+190,1000,yy+360),26,fill=BG2,outline=LINE); d.text((120,yy+216),"QUINZENAL",font=F(800,22),fill=GOLD)
d.text((120,yy+252),"1:1s",font=F(900,44),fill=WHITE); d.text((120,yy+308),"para destravar gargalos",font=F(500,28),fill=MUTE)
yy+=390
rr(d,(80,yy,1000,yy+130),26,fill=GOLD); d.text((120,yy+22),"COBRE O INDICADOR COMBINADO,",font=F(900,34),fill=BG); d.text((120,yy+70),"NÃO O PASSO A PASSO.",font=F(900,34),fill=BG)
save(im,7)

# 8 fechamento
im,d=frame(8,"@oficialcosmelima • gestão de alta performance")
d.text((80,170),"RESUMO",font=F(800,28),fill=GOLD)
rr(d,(80,225,520,520),26,fill=BG2,outline=RED); rr(d,(560,225,1000,520),26,fill=BG2,outline=GRN)
d.text((110,250),"MICROGERENCIAMENTO",font=F(800,24),fill=RED); text(d,"gera obediência e cansaço.",110,300,F(900,40),mw=380,ls=1.2)
d.text((590,250),"CONTEXTO CLARO",font=F(800,24),fill=GRN); text(d,"gera accountability e escala.",590,300,F(900,40),mw=380,ls=1.2)
y=text(d,"Em qual nível está a maior parte da sua equipe?",80,590,F(900,56),mw=920,ls=1.18,hl=("nível",))
for i in range(3):
    x=80+i*320; rr(d,(x,y+30,x+280,y+130),50,outline=GOLD,w=4); d.text((x+140,y+80),f"NÍVEL {i+1}",font=F(900,36),fill=GOLD,anchor="mm")
y=text(d,"Comente 1, 2 ou 3 aqui embaixo. 👇".replace(" 👇",""),80,y+170,F(700,38),mw=900,ls=1.3)
rr(d,(80,y+20,1000,y+160),26,fill=GOLD); d.text((120,y+44),"SALVE ESTE POST",font=F(900,40),fill=BG); d.text((120,y+100),"para consultar antes da sua próxima reunião de alinhamento.",font=F(700,26),fill=BG)
save(im,8)
