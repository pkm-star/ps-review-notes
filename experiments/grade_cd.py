import random, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from problems_cd import *
def c_fix(arr):
    n=len(arr);left=[0]*n;right=[0]*n;st=[]
    for i in range(n):
        while st and arr[st[-1]]>=arr[i]: st.pop()
        left[i]=i-st[-1] if st else i+1; st.append(i)
    st=[]
    for i in range(n-1,-1,-1):
        while st and arr[st[-1]]>arr[i]: st.pop()
        right[i]=st[-1]-i if st else n-i; st.append(i)
    return sum(a*l*r for a,l,r in zip(arr,left,right))%MOD
def dp(arr,strict):
    st=[];f=[0]*len(arr)
    for i,a in enumerate(arr):
        while st and (arr[st[-1]]>=a if strict else arr[st[-1]]>a): st.pop()
        j=st[-1] if st else -1
        f[i]=(f[j] if j>=0 else 0)+a*(i-j); st.append(i)
    return sum(f)%MOD
random.seed(9);bad=[0,0,0]
for _ in range(3000):
    a=[random.randint(1,5) for _ in range(random.randint(1,9))];r=c_ref(a)
    bad[0]+=c_fix(a)!=r;bad[1]+=dp(a,True)!=r;bad[2]+=dp(a,False)!=r
print('C fix / dp strict / dp nonstrict mismatches',bad)
print('C [1,1] bug',c_bug([1,1]),'ref',c_ref([1,1]),'| [2,2] bug',c_bug([2,2]),'ref',c_ref([2,2]))
def d_fix_int(fees,records):
    bt,bf,ut,uf=fees;enter={};total={}
    for rec in records:
        t,m,k=rec.split();m=int(m)
        if k=='IN': enter[m]=to_min(t)
        else: total[m]=total.get(m,0)+to_min(t)-enter.pop(m)
    for m,t in enter.items(): total[m]=total.get(m,0)+to_min('22:00')-t
    out=[]
    for m in sorted(total):
        t=total[m]
        out.append(bf if t<=bt else bf+((t-bt+ut-1)//ut)*uf)
    return out
F=[120,3000,30,500];G=[60,1000,10,100]
tests={'haiku1':(F,['09:00 42 IN','09:05 7 IN','11:00 7 OUT','12:50 42 OUT']),'haiku2':(F,['09:00 7 IN','12:30 7 OUT']),
'sonnet1':(G,['09:00 1 IN','10:10 1 OUT']),'sonnet2':(G,['09:00 9 IN','09:30 9 OUT','10:00 10 IN','11:25 10 OUT']),
'opus1':(F,['09:00 7 IN','12:00 7 OUT']),'opus2':(F,['09:00 7 IN','09:00 42 IN','10:00 7 OUT','11:50 42 OUT'])}
for k,(f,r) in tests.items(): print('D',k,'bug',d_bug(f,r),'ref',d_ref(f,r),'fix',d_fix_int(f,r))
