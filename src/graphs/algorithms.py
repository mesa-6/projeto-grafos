from typing import List, Dict, Any, Optional, Tuple
from collections import deque
import heapq
import time

# helpers mínimos
def _iter_neighbors(graph, u: str):
    for nbr in getattr(graph, "adj", {}).get(u, []):
        if isinstance(nbr, (list, tuple)):
            v = nbr[0] if len(nbr) >= 1 else None

            try:
                w = float(nbr[1]) if len(nbr) >= 2 else 1.0
            except Exception:
                w = 1.0
        else:
            v = nbr
            w = 1.0

        if v is None:
            continue

        yield v, w

def bfs(graph, source: str) -> Dict[str, Any]:
    t0 = time.time()
    nodes = list(graph.nodes_list())

    if source not in nodes:
        return {"time_sec": 0.0, "error": f"source '{source}' not in graph"}
    
    dist = {n: None for n in nodes}
    parent = {n: None for n in nodes}
    order: List[str] = []
    q = deque()
    dist[source] = 0
    q.append(source)

    while q:
        u = q.popleft()
        order.append(u)

        for v, _ in _iter_neighbors(graph, u):
            if dist.get(v) is None:
                dist[v] = dist[u] + 1
                parent[v] = u
                q.append(v)

    return {"time_sec": time.time() - t0, "dist": dist, "parent": parent, "order": order}

def dfs(graph, sources: Optional[List[str]] = None) -> Dict[str, Any]:
    t0 = time.time()
    nodes = list(graph.nodes_list())
    color = {n: "white" for n in nodes}
    discovery: Dict[str, Optional[int]] = {n: None for n in nodes}
    finish: Dict[str, Optional[int]] = {n: None for n in nodes}
    parent: Dict[str, Optional[str]] = {n: None for n in nodes}
    order: List[str] = []
    edge_classes: List[Tuple[str, str, str]] = []
    timer = 0

    def _visit(u: str):
        nonlocal timer
        color[u] = "gray"
        timer += 1
        discovery[u] = timer
        order.append(u)

        for v, _ in _iter_neighbors(graph, u):
            if color[v] == "white":
                parent[v] = u
                edge_classes.append((u, v, "tree"))
                _visit(v)
            else:
                if color[v] == "gray":
                    edge_classes.append((u, v, "back"))
                else:
                    if discovery.get(u) and discovery.get(v) and discovery[u] < discovery[v]:
                        edge_classes.append((u, v, "forward"))
                    else:
                        edge_classes.append((u, v, "cross"))

        color[u] = "black"
        timer += 1
        finish[u] = timer

    if sources:
        for s in sources:
            if s in color and color[s] == "white":
                _visit(s)

    for n in nodes:
        if color[n] == "white":
            _visit(n)

    return {
        "time_sec": time.time() - t0,
        "discovery": discovery,
        "finish": finish,
        "parent": parent,
        "order": order,
        "edge_classes": edge_classes
    }

def dijkstra(graph, source: str, dest: Optional[str] = None) -> Dict[str, Any]:
    t0 = time.time()
    nodes = list(graph.nodes_list())

    if source not in nodes:
        return {"time_sec": 0.0, "error": f"source '{source}' not in graph"}

    INF = float("inf")
    dist: Dict[str, float] = {n: INF for n in nodes}
    prev: Dict[str, Optional[str]] = {n: None for n in nodes}
    prev_edge: Dict[str, Optional[Any]] = {n: None for n in nodes}

    dist[source] = 0.0
    heap: List[Tuple[float, str]] = [(0.0, source)]

    while heap:
        d, u = heapq.heappop(heap)

        if d > dist[u]:
            continue

        if dest is not None and u == dest:
            break
        
        for nbr in getattr(graph, "adj", {}).get(u, []):
            if isinstance(nbr, (list, tuple)):
                v = nbr[0] if len(nbr) >= 1 else None

                try:
                    w = float(nbr[1]) if len(nbr) >= 2 else 1.0
                except Exception:
                    w = 1.0

                meta = nbr[2] if len(nbr) >= 3 else None
            else:
                v = nbr
                w = 1.0
                meta = None

            if v is None:
                continue

            if w < 0:
                return {"time_sec": time.time() - t0, "error": "negative_weight_detected", "edge": (u, v, w)}
            
            nd = d + w

            if nd < dist[v]:
                dist[v] = nd
                prev[v] = u
                prev_edge[v] = meta
                heapq.heappush(heap, (nd, v))

    return {"time_sec": time.time() - t0, "dist": dist, "prev": prev, "prev_edge": prev_edge}

def bellman_ford(graph, source: str) -> Dict[str, Any]:
    t0 = time.time()
    nodes = list(graph.nodes_list())

    if source not in nodes:
        return {"time_sec": 0.0, "error": f"source '{source}' not in graph"}
    
    dist = {n: float("inf") for n in nodes}
    prev: Dict[str, Optional[str]] = {n: None for n in nodes}
    dist[source] = 0.0
    edges: List[Tuple[str, str, float]] = []

    for u in getattr(graph, "adj", {}):
        for v, w in _iter_neighbors(graph, u):
            edges.append((u, v, float(w)))

    N = len(nodes)

    for i in range(N - 1):
        updated = False

        for u, v, w in edges:
            if dist[u] == float("inf"):
                continue

            nd = dist[u] + w

            if nd < dist[v]:
                dist[v] = nd
                prev[v] = u
                updated = True

        if not updated:
            break

    neg_cycle = None

    for u, v, w in edges:
        if dist[u] == float("inf"):
            continue

        if dist[u] + w < dist[v]:
            neg_cycle = _reconstruct_negative_cycle(prev, v, nodes)
            break

    return {"time_sec": time.time() - t0, "dist": dist, "prev": prev, "negative_cycle": neg_cycle}

def _reconstruct_negative_cycle(prev: Dict[str, Optional[str]], start: str, nodes: List[str]) -> Optional[List[str]]:
    v = start

    for _ in range(len(nodes)):
        v = prev.get(v) or v

    cycle = []
    seen = {}
    idx = 0
    cur = v

    while True:
        if cur in seen:
            st = seen[cur]
            return cycle[st:]
        
        seen[cur] = idx
        cycle.append(cur)
        idx += 1
        cur = prev.get(cur)

        if cur is None:
            return None

def floyd_warshall(graph) -> Dict[str, Dict[str, float]]:
    nodes = list(graph.nodes_list())
    idx = {n: i for i, n in enumerate(nodes)}
    n = len(nodes)
    inf = float("inf")

    dist = [[inf] * n for _ in range(n)]

    for i in range(n):
        dist[i][i] = 0.0

    directed = getattr(graph, "directed", False)

    for u in getattr(graph, "adj", {}):
        for v, w in _iter_neighbors(graph, u):
            i = idx[u]; j = idx[v]

            if w < dist[i][j]:
                dist[i][j] = float(w)
            
            if not directed:
                if w < dist[j][i]:
                    dist[j][i] = float(w)
    
    for k in range(n):
        for i in range(n):
            dik = dist[i][k]
            
            if dik == inf:
                continue
            
            row_i = dist[i]
            row_k = dist[k]
            
            for j in range(n):
                nd = dik + row_k[j]
                
                if nd < row_i[j]:
                    row_i[j] = nd
    
    out: Dict[str, Dict[str, float]] = {}
    
    for i, u in enumerate(nodes):
        out[u] = {}
    
        for j, v in enumerate(nodes):
            out[u][v] = dist[i][j]
    
    return out

def reconstruct_path(prev: Dict[str, Optional[str]], target: str) -> List[str]:
    path = []
    cur = target

    while cur is not None:
        path.append(cur)
        cur = prev.get(cur)

    return list(reversed(path))

def reconstruct_path_edges(prev: Dict[str, Optional[str]], prev_edge: Dict[str, Optional[Any]], target: str) -> List[str]:
    path = reconstruct_path(prev, target)

    if not path or len(path) == 1:
        return []

    edges = []

    for v in path[1:]:
        meta = prev_edge.get(v)
        edges.append(meta if meta is not None else "")

    return edges
