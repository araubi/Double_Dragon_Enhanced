from PIL import Image
import collections
m=Image.open('snap/0031.png').convert('RGB').crop((0,0,256,198)); mp=m.load()
r=Image.open('ruben.png').convert('RGB'); rp=r.load()
def his(x,y): return rp[int(45+(x-11)*900/233+0.5*3.85), int(21+(y-24)*536/173+0.5*3.08)]
acc=collections.defaultdict(list); mask=set()
for y in range(24,198):
    for x in range(11,245):
        c=mp[x,y]
        if c==(0,0,0): continue
        h=his(x,y)
        blu = h[2]>h[0]+15 or (abs(h[0]-h[1])<20 and abs(h[1]-h[2])<20 and h[0]>90)   # azulado o gris
        if blu and 60<=y<=115: mask.add((x,y)); acc[c].append(h)
print(len(mask))
for c,l in sorted(acc.items(),key=lambda t:-len(t[1])):
    avg=tuple(sum(v[i] for v in l)//len(l) for i in range(3)); print(c,len(l),avg)
xs=[p[0] for p in mask]; ys=[p[1] for p in mask]
print('bbox',min(xs),max(xs),min(ys),max(ys))
MAP={(255,238,170):(187,204,221),(238,204,136):(170,187,204),(221,170,102):(119,136,153),(119,68,51):(68,85,102),
     (136,85,68):(85,102,119),(51,17,0):(51,68,85),(255,255,221):(238,238,255)}
out=m.copy(); op=out.load()
near=set()
for (x,y) in mask:
    for dx in (-2,-1,0,1,2):
        for dy in (-2,-1,0,1,2): near.add((x+dx,y+dy))
n=0
for (x,y) in near:
    if 0<=x<256 and 0<=y<198 and mp[x,y] in MAP and min(ys)-2<=y<=max(ys)+2:
        op[x,y]=MAP[mp[x,y]]; n+=1
print('recoloured',n)
out=out.crop((0,24,256,198))
out.save('logo_plata.png'); m.crop((0,24,256,198)).save('logo_crema.png')
Image.fromarray if False else None
big=Image.new('RGB',(512,348*2)); big.paste(m.crop((0,24,256,198)).resize((512,348),Image.NEAREST),(0,0)); big.paste(out.resize((512,348),Image.NEAREST),(0,348)); big.save('cmp.png')
