import random
MOD = 1_000_000_007
def c_ref(arr):
    n=len(arr); return sum(min(arr[i:j+1]) for i in range(n) for j in range(i,n)) % MOD
def c_bug(arr):
    n = len(arr)
    left = [0] * n
    right = [0] * n
    stack = []
    for i in range(n):
        while stack and arr[stack[-1]] >= arr[i]:
            stack.pop()
        left[i] = i - stack[-1] if stack else i + 1
        stack.append(i)
    stack = []
    for i in range(n - 1, -1, -1):
        while stack and arr[stack[-1]] >= arr[i]:
            stack.pop()
        right[i] = stack[-1] - i if stack else n - i
        stack.append(i)
    return sum(a * l * r for a, l, r in zip(arr, left, right)) % MOD

def to_min(t):
    h, m = t.split(":")
    return int(h) * 60 + int(m)
def d_core(fees, records, keyf, ceil_ok):
    base_time, base_fee, unit_time, unit_fee = fees
    enter = {}; total = {}
    for rec in records:
        t, member, kind = rec.split()
        if kind == "IN": enter[member] = to_min(t)
        else: total[member] = total.get(member, 0) + to_min(t) - enter.pop(member)
    for member, t in enter.items():
        total[member] = total.get(member, 0) + to_min("22:00") - t
    answer = []
    for member in sorted(total, key=keyf):
        t = total[member]
        if t <= base_time: answer.append(base_fee)
        elif ceil_ok: answer.append(base_fee + -(-(t - base_time) // unit_time) * unit_fee)
        else: answer.append(base_fee + ((t - base_time) // unit_time + 1) * unit_fee)
    return answer
d_ref = lambda f,r: d_core(f,r,int,True)
d_bug = lambda f,r: d_core(f,r,None,False)

if __name__ == "__main__":
    for a in ([3,1,2,4],[2,2],[5,3,3,7]): print("C",a,c_ref(a),c_bug(a))
    random.seed(5); w=0
    for _ in range(2000):
        a=[random.randint(1,6) for _ in range(random.randint(1,8))]
        w += c_ref(a)!=c_bug(a)
    print("C wrong",w,"/2000")
    fees=[120,3000,30,500]
    recs=["09:10 42 IN","10:05 17 IN","11:47 42 OUT","12:30 35 IN","13:20 17 OUT","14:00 42 IN","15:02 35 OUT","16:40 42 OUT","19:25 17 IN"]
    print("D sample ref",d_ref(fees,recs),"bug",d_bug(fees,recs))
    r2=["09:00 9 IN","12:00 9 OUT","09:00 10 IN","10:00 10 OUT"]
    print("D ex ref",d_ref(fees,r2),"bug",d_bug(fees,r2))
