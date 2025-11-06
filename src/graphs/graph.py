from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
import pandas as pd
import unicodedata
import heapq

# Definição dos tipos das variáveis
Node = str
Peso = float
Logradouro = str
Edge = Tuple[Node, Node, Peso, Logradouro]

class Graph:
    # Construtor
    def __init__(self):
        self.adj: Dict[Node, List[Tuple[Node, Peso, Logradouro]]] = {}
        self.nodes: set = set()
        self.bairro_to_microrregiao: Dict[Node, Any] = {}

    # Método que constrói o grafo a partir dos datframes já EM MEMÓRIA
    @classmethod
    def build_from_df(cls, df_adjacencias: pd.DataFrame, df_microrregiao: Optional[pd.DataFrame] = None) -> "Graph":
        g = cls()

        # Caso exista bairros_unique.csv, constrói as informações relativas as microrregiões
        if df_microrregiao is not None:
            g.set_microrregiao_from_df(df_microrregiao)

        # conveniência: função local para normalizar nomes (chama o método da classe)
        normalize = cls._normalize_name 

        for _, r in df_adjacencias.iterrows():
            u_raw = r.get('bairro_origem')
            v_raw = r.get('bairro_destino')
            log = r.get('logradouro', '') if 'logradouro' in r.index else ''
            peso_raw = r.get('peso', 1.0)

            u = normalize(u_raw)
            v = normalize(v_raw)

            try:
                peso = float(peso_raw)
            except Exception:
                peso = float('inf')

            if u not in g.adj:
                g.adj[u] = []
            if v not in g.adj:
                g.adj[v] = []

            # adicionar ambas as direções (grafo não-direcionado)
            g.adj[u].append((v, peso, log))
            g.adj[v].append((u, peso, log))

            g.nodes.add(u)
            g.nodes.add(v)

        return g
    
    # Método que constrói o grafo a partir dos datframes a partir dos csvs
    @classmethod
    def load_from_files(cls, adj_path: str | Path, bairros_path: Optional[str | Path] = None) -> "Graph":
        adj_p = Path(adj_path)

        if not adj_p.exists():
            raise FileNotFoundError(f"Arquivo de adjacências não encontrado: {adj_p}")

        df_adj = pd.read_csv(adj_p)

        df_mr = None

        if bairros_path is not None:
            mr_p = Path(bairros_path)

            if mr_p.exists():
                df_mr = pd.read_csv(mr_p)
            else:
                # não dá erro — só não popula microrregiao
                df_mr = None

        return cls.build_from_df(df_adj, df_mr)

    # Método para popular o grafo com as informações do dataframe de microrregiões
    def set_microrregiao_from_df(self, df_microrregiao: pd.DataFrame, bairro_col: str = "bairro", micror_col: str = "microrregiao") -> None:
        if df_microrregiao is None:
            return
        
        if bairro_col not in df_microrregiao.columns or micror_col not in df_microrregiao.columns:
            return
        
        for _, r in df_microrregiao.iterrows():
            bn = self._normalize_name(r[bairro_col])
            self.bairro_to_microrregiao[bn] = r[micror_col]

    # Método para normalizar uma string
    @staticmethod
    def _normalize_name(s: str) -> str:
        if s is None:
            return ""
        
        if not isinstance(s, str):
            s = str(s)

        s2 = unicodedata.normalize("NFD", s)
        s2 = "".join(c for c in s2 if unicodedata.category(c) != "Mn")

        return s2.strip().upper()

    # Método para normalizar o nome de um nó
    def normalize_node(self, name: str) -> str:
        return self._normalize_name(name)

    # Método para conferir a exist^ncia de um nó
    def has_node(self, node: str) -> bool:
        return self._normalize_name(node) in self.nodes

    # Método para retornar os nós
    def nodes_list(self) -> List[str]:
        return sorted(self.nodes)

    # Método para retornar as arestas
    def edges_list(self) -> List[Dict[str, Any]]:
        seen = set()

        out = []

        for u, nbrs in self.adj.items():
            for v, peso, log in nbrs:
                if u == v:
                    continue

                a, b = (u, v) if u <= v else (v, u)

                key = (a, b, log)

                if key in seen:
                    continue

                seen.add(key)

                out.append({"bairro_origem": a, "bairro_destino": b, "logradouro": log, "peso": float(peso)})

        return out

    # Método para retornar os nós com informação do grau 
    def nodes_metadata(self) -> List[Dict[str, Any]]:
        out = []

        for n in sorted(self.nodes):
            grau = len(self.adj.get(n, []))

            out.append({"id": n, "grau": int(grau), "microrregiao": self.bairro_to_microrregiao.get(n)})

        return out

    # Algoritmo de dijkstra
    def dijkstra(self, origem: str, destino: str) -> Tuple[List[str], List[str], float]:
        origem_n = self._normalize_name(origem)
        destino_n = self._normalize_name(destino)

        if origem_n not in self.nodes or destino_n not in self.nodes:
            return [], [], float('inf')

        INF = float('inf')

        dist: Dict[Node, float] = {n: INF for n in self.nodes}
        prev: Dict[Node, Optional[Node]] = {n: None for n in self.nodes}
        prev_edge: Dict[Node, Optional[Logradouro]] = {n: None for n in self.nodes}

        dist[origem_n] = 0.0
        heap = [(0.0, origem_n)]

        while heap:
            d, u = heapq.heappop(heap)
            
            if d > dist[u]:
                continue
            
            if u == destino_n:
                break
            
            for v, w, log in self.adj.get(u, []):
                nd = d + (float(w) if w is not None else INF)
                
                if nd < dist[v]:
                    dist[v] = nd
                    prev[v] = u
                    prev_edge[v] = log
                    heapq.heappush(heap, (nd, v))

        if dist[destino_n] == INF:
            return [], [], INF

        path_nodes = []
        path_logs = []
        cur = destino_n
        
        while cur is not None and cur != origem_n:
            path_nodes.append(cur)
            path_logs.append(prev_edge[cur])
            cur = prev[cur]
        
        path_nodes.append(origem_n)
        path_nodes.reverse()
        path_logs.reverse()

        return path_nodes, [l if l is not None else "" for l in path_logs], float(dist[destino_n])

    # Calcula métricas para ego-network radius=1 do bairro:
    def ego_metrics(self, bairro: str) -> Dict[str, Any]:
        b = self._normalize_name(bairro)
        
        if b not in self.nodes:
            return {"bairro": bairro, "grau": 0, "ordem_ego": 0, "tamanho_ego": 0, "densidade_ego": 0.0}

        # vizinhos diretos
        vizs = {v for v, _, _ in self.adj.get(b, [])}
        vizs.add(b)
        N = len(vizs)

        m_count = 0
        seen_pairs = set()
        
        for u in vizs:
            for v in self.adj.get(u, []):
                if v in vizs:
                    a, c = (u, v) if u <= v else (v, u)
                    
                    key = (a, c)

                    if key not in seen_pairs:
                        seen_pairs.add(key)
                        m_count += 1
                        
        E = m_count
        dens = 0.0
        
        if N > 1:
            dens = (2.0 * E) / (N * (N - 1))
            
        grau = max(0, len(vizs) - 1)
        
        return {"bairro": b, "grau": int(grau), "ordem_ego": int(N), "tamanho_ego": int(E), "densidade_ego": round(dens, 4)}

    # Calcula ordem/tamanho/densidade para uma microrregião.
    def microrregiao_stats(self, microrregiao_id: Any) -> Optional[Dict[str, Any]]:        
        target = str(microrregiao_id).strip()

        bairros = [b for b, mr in self.bairro_to_microrregiao.items() if str(mr).strip() == target]

        if not bairros:
            return None

        N = len(bairros)

        seen = set()
        E = 0

        for u in bairros:
            for v in self.adj.get(u, []):
                if v in bairros:
                    a, b_ = (u, v) if u <= v else (v, u)

                    key = (a, b_)

                    if key not in seen:
                        seen.add(key)
                        E += 1

        dens = 0.0
        
        if N > 1:
            dens = (2.0 * E) / (N * (N - 1))

        return {
            "microrregiao": microrregiao_id, 
            "ordem": N, 
            "tamanho": E, 
            "densidade": round(dens, 4)
        }