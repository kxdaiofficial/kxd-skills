import numpy as np, hand as h
I=h.IMG
def rays(c, col, tol=16, angs=np.arange(0,360,1.0), rmax=400, step=0.25):
    """walk out from centre c along rays; stop where the colour leaves `col` (max-channel diff > tol).
    returns list of (angle, point, outside_colour) with sub-pixel crossing by colour projection."""
    col=np.asarray(col,float); out=[]
    for a in angs:
        d=np.array([np.cos(np.radians(a)), np.sin(np.radians(a))])
        rs=np.arange(0,rmax,step); P=c[None]+rs[:,None]*d[None]
        ok=(P[:,0]>=0.5)&(P[:,0]<h.W-0.5)&(P[:,1]>=0.5)&(P[:,1]<h.H-0.5)
        rs,P=rs[ok],P[ok]
        C=h.at(P[:,0],P[:,1]); diff=np.abs(C-col).max(1)
        k=np.where(diff>tol)[0]
        if len(k)==0: out.append((a,None,None)); continue
        k=k[0]
        # outside colour: 3 px further
        j=min(len(rs)-1,k+int(3/step)); oc=C[j]
        dd=oc-col; t=((C[max(0,k-12):k+1]-col)@dd)/max(dd@dd,1e-6)
        seg=rs[max(0,k-12):k+1]; kk=np.where(t>=0.5)[0]
        r=seg[kk[0]] if len(kk) else rs[k]
        out.append((a,c+r*d,oc))
    return out
