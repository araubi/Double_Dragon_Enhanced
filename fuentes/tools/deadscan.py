import sys, re, os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import z80dis as Z
D0=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','dd')+'/'
base=bytearray(open(D0+'mem.bin','rb').read())
blocks={1:6,2:9,3:11,4:13,5:15,6:17,7:19}
def traverse(mem, entries, reach):
    D=Z.Dis(bytes(mem),0); seen=set(); work=list(entries)
    while work:
        pc=work.pop()
        while pc not in seen and 0<=pc<0x10000:
            seen.add(pc); t,l,f,tg=D.dec(pc)
            for k in range(l): reach.add((pc+k)&0xFFFF)
            for x in tg:
                if x not in seen: work.append(x)
            if f in ('jp','ret','stop'): break
            pc+=l
def analyse(lo,hi,covexec,covread,extra_entries=()):
    reach=set()
    ex=open(covexec,'rb').read(); rd=open(covread,'rb').read()
    dyn=[a for a in range(65536) if ex[a]]
    for n,k in blocks.items():
        mem=bytearray(base)
        mb=open(D0+'b%02d.bin'%k,'rb').read()[1:1+0x50F6]; mem[0x9056:0x9056+len(mb)]=mb
        if n==7: mem[0xEE48:0xEE48+0x550]=open(D0+'b20.bin','rb').read()[1:1+0x550]
        # stubs
        traverse(mem,[0x9056,0xEA60,0xE612,0xE14C]+list(extra_entries)+dyn,reach)
    dead=[a for a in range(lo,hi) if a not in reach and not ex[a] and not rd[a]]
    runs=[];s=None;p=None
    for a in dead:
        if s is None: s=p=a
        elif a==p+1: p=a
        else: runs.append((s,p)); s=p=a
    if s is not None: runs.append((s,p))
    return runs
if __name__=='__main__':
    lo,hi=int(sys.argv[1],16),int(sys.argv[2],16)
    for s,e in analyse(lo,hi,D0+'../emu/cov_exec.bin',D0+'../emu/cov_read.bin'):
        if e-s+1>=int(sys.argv[3] if len(sys.argv)>3 else 4): print('%04X-%04X %4d'%(s,e,e-s+1))
