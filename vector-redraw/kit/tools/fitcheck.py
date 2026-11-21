import numpy as np, hand as h
def try_anchors(P, A_first, t_first, mids, A_last, t_last=None):
    """P samples ordered; mids: list of x (or y) picks -> snapped to samples; smooth tangents from samples."""
    anchors=[np.asarray(A_first,float)]+[P[np.argmin(np.linalg.norm(P-np.asarray(m),axis=1))] for m in mids]+[np.asarray(A_last,float)]
    T=[np.asarray(t_first,float) if t_first is not None else None]
    for a in anchors[1:-1]:
        t=h.tangent_at(P,a,6); T.append(t)
    T.append(np.asarray(t_last,float) if t_last is not None else None)
    # orient tangents along path direction
    for i in range(1,len(anchors)-1):
        d=anchors[i+1]-anchors[i-1]
        if T[i] @ d < 0: T[i]=-T[i]
    # index anchors in samples
    idx=[np.argmin(np.linalg.norm(P-a,axis=1)) for a in anchors]
    ctrls=[];rep=[]
    for j in range(len(anchors)-1):
        lo,hi=sorted((idx[j],idx[j+1])); s=P[lo+1:hi] if hi>lo+1 else P[0:0]
        t0=T[j]; t3=(-T[j+1]) if T[j+1] is not None else None
        c=h.solve(anchors[j],anchors[j+1],s,t0,t3); e=h.err(c,s) if len(s) else np.zeros(1)
        ctrls.append(c); rep.append((round(float(e.max()),2),round(float(e.mean()),2),len(s)))
    return anchors,ctrls,rep
