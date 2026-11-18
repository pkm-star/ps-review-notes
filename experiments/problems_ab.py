import heapq, random, itertools

# ---------- A: ribbon cutting ----------
def a_ref(ribbons, k):
    lo, hi = 1, max(ribbons)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if sum(r // mid for r in ribbons) >= k: lo = mid
        else: hi = mid - 1
    return lo

def a_bug(ribbons, k, limit=10000):
    lo, hi = 1, max(ribbons)
    steps = 0
    while lo < hi:
        steps += 1
        if steps > limit: return None  # infinite loop
        mid = (lo + hi) // 2
        pieces = sum(r // mid for r in ribbons)
        if pieces >= k: lo = mid
        else: hi = mid - 1
    return lo

for case in [([8,5,6],4), ([10,7,4],5), ([12,9,7],6), ([9,6,3],6), ([20,15,9],7), ([7,7,7],3),([10,10],4),([5,5,5],15)]:
    print("A", case, "ref", a_ref(*case), "bug", a_bug(*case))

random.seed(1)
hang = ok = wrong = 0
for _ in range(2000):
    n = random.randint(1,5); rb = [random.randint(1,50) for _ in range(n)]
    k = random.randint(1, sum(rb))
    r, b = a_ref(rb,k), a_bug(rb,k)
    if b is None: hang += 1
    elif b == r: ok += 1
    else: wrong += 1
print("A stats ok/hang/wrong", ok, hang, wrong)

# ---------- B: coupon dijkstra ----------
def b_ref(n, roads):
    g = [[] for _ in range(n+1)]
    for a,b,c in roads: g[a].append((b,c)); g[b].append((a,c))
    INF = float('inf')
    dist = [[INF]*2 for _ in range(n+1)]
    dist[1][0] = 0
    pq = [(0,1,0)]
    while pq:
        cost,node,used = heapq.heappop(pq)
        if cost > dist[node][used]: continue
        for nxt,c in g[node]:
            if cost + c < dist[nxt][used]:
                dist[nxt][used] = cost + c; heapq.heappush(pq,(cost+c,nxt,used))
            if not used and cost < dist[nxt][1]:
                dist[nxt][1] = cost; heapq.heappush(pq,(cost,nxt,1))
    return min(dist[n])

def b_bug(n, roads):
    graph = [[] for _ in range(n + 1)]
    for a, b, c in roads:
        graph[a].append((b, c)); graph[b].append((a, c))
    INF = float('inf')
    dist = [INF] * (n + 1)
    dist[1] = 0
    pq = [(0, 1, False)]
    while pq:
        cost, node, used = heapq.heappop(pq)
        if cost > dist[node]:
            continue
        for nxt, c in graph[node]:
            if cost + c < dist[nxt]:
                dist[nxt] = cost + c
                heapq.heappush(pq, (cost + c, nxt, used))
            if not used and cost < dist[nxt]:
                dist[nxt] = cost
                heapq.heappush(pq, (cost, nxt, True))
    return dist[n]

for case in [(3,[[1,2,1],[2,3,100]]), (4,[[1,2,5],[2,4,3],[1,3,2],[3,4,9]]), (4,[[1,2,10],[2,3,4],[3,4,6],[1,4,25]]), (5,[[1,2,7],[1,3,3],[3,4,4],[2,5,6],[4,5,8]])]:
    print("B", case, "ref", b_ref(*case), "bug", b_bug(*case))
ok = wrong = 0
for _ in range(3000):
    n = random.randint(2,6)
    roads = []
    for i in range(2,n+1): roads.append([random.randint(1,i-1), i, random.randint(1,20)])
    for _ in range(random.randint(0,4)):
        a,b = random.sample(range(1,n+1),2); roads.append([a,b,random.randint(1,20)])
    if b_ref(n,roads)==b_bug(n,roads): ok+=1
    else: wrong+=1
print("B stats ok/wrong", ok, wrong)
