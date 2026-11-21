import numpy as np, hand as h
I=h.IMG
def vruns(x, y0, y1, thr=18, minlen=2):
    out=[]; start=y0; cur=I[y0,x].astype(int)
    for y in range(y0+1,y1):
        c=I[y,x].astype(int)
        if np.abs(c-cur).max()>thr: out.append([start,y-1]); start=y
        cur=c
    out.append([start,y1-1])
    return [(a,b,np.median(I[a:b+1,x],0)) for a,b in out if b-a+1>=minlen]
def bounds(x, y0, y1, thr=18):
    """sub-pixel y of each boundary between consecutive runs (colour projection crossing 0.5) at column centre x+0.5"""
    R=vruns(x,y0,y1,thr); res=[]
    for (a0,b0,c0),(a1,b1,c1) in zip(R[:-1],R[1:]):
        ys=np.arange(b0-1.0, a1+2.0, 0.05); col=h.at(np.full(len(ys),x+0.5),ys)
        d=c1-c0; t=((col-c0)@d)/(d@d)
        k=np.where((t[:-1]<0.5)&(t[1:]>=0.5))[0]
        if len(k)==0: continue
        k=k[0]; y=ys[k]+(0.5-t[k])/(t[k+1]-t[k]+1e-9)*0.05
        res.append((round(float(y),2), tuple(c0.astype(int)), tuple(c1.astype(int)), b0-a0+1, b1-a1+1))
    return res
