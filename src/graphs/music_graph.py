from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
import pandas as pd
import unicodedata
import random

Node = str
Peso = float

class MusicGraph:
    # Construtor
    def __init__(self):
        self.adj: Dict[Node, List[Tuple[Node, Peso]]] = {}
        self.nodes: set = set()

    @staticmethod
    def _normalize_name(s: Optional[str]) -> str:
        if s is None:
            return ""
        
        if not isinstance(s, str):
            s = str(s)

        s2 = unicodedata.normalize("NFD", s)
        s2 = "".join(c for c in s2 if unicodedata.category(c) != "Mn")

        return s2.strip()

    def normalize_node(self, name: str) -> str:
        return self._normalize_name(name)

    def has_node(self, node: str) -> bool:
        return self._normalize_name(node) in self.nodes

    def nodes_list(self) -> List[str]:
        return sorted(self.nodes)

    def add_edge(self, a_raw: str, b_raw: str, peso: Any = 1.0) -> None:
        a = self._normalize_name(a_raw)
        b = self._normalize_name(b_raw)

        try:
            w = float(peso)
        except Exception:
            w = 1.0

        if a not in self.adj:
            self.adj[a] = []
        
        if b not in self.adj:
            self.adj[b] = []

        # adicionar ambas as direções (grafo não-direcionado)
        self.adj[a].append((b, w))
        self.adj[b].append((a, w))

        self.nodes.add(a)
        self.nodes.add(b)

    @classmethod
    def load_from_edges_csv(cls, path: str | Path, a_col: str = "track_a", b_col: str = "track_b", peso_col: str = "peso", genres_col: Optional[str] = "common_genres") -> "MusicGraph":
        p = Path(path)
        
        if not p.exists():
            raise FileNotFoundError(f"edges CSV not found: {p}")
        
        df = pd.read_csv(p, dtype=str, encoding="utf-8-sig", keep_default_na=False)
        mg = cls()
        
        # Preserva coluna genres caso exista
        mg._edge_genres = {}
        
        for _, r in df.iterrows():
            a = str(r.get(a_col, "")).strip()
            b = str(r.get(b_col, "")).strip()

            if a == "" or b == "":
                continue
            
            try:
                w = float(r.get(peso_col, 1.0))
            except Exception:
                w = 1.0
            
            mg.add_edge(a, b, w)
            
            if genres_col and genres_col in df.columns:
                g = str(r.get(genres_col, "")).strip()
                key = (mg._normalize_name(a), mg._normalize_name(b))
                mg._edge_genres[key] = g
        
        return mg

    def edges_list(self) -> List[Dict[str, Any]]:
        seen = set()
        out = []
        genres_map = getattr(self, "_edge_genres", {})

        for u, nbrs in self.adj.items():
            for v, w in nbrs:
                if u == v:
                    continue
                
                a, b = (u, v) if u <= v else (v, u)
                key = (a, b)
                
                if key in seen:
                    continue
                
                seen.add(key)
                
                g = genres_map.get((a, b), "") or genres_map.get((b, a), "")
                out.append({"track_a": a, "track_b": b, "common_genres": g, "peso": float(w)})
        
        return out

    def apply_negative_fraction(self, negative_shift: float = 0.6, negative_fraction: float = 0.03, seed: Optional[int] = 12345) -> None:
        random.seed(seed)
        edges = []
        
        for u, nbrs in self.adj.items():
            for v, w in nbrs:
                if u <= v:
                    edges.append((u, v))
        
        m = max(1, int(len(edges) * negative_fraction))
        chosen = set(random.sample(edges, m)) if edges else set()
        
        for (a, b) in chosen:
            for idx, (nb, w) in enumerate(self.adj[a]):
                if nb == b:
                    self.adj[a][idx] = (nb, float(w) - negative_shift)
            
            for idx, (nb, w) in enumerate(self.adj[b]):
                if nb == a:
                    self.adj[b][idx] = (nb, float(w) - negative_shift)

    def inject_negative_cycle(self, cycle_size: int = 3, cycle_edge_weight: float = -0.8, seed: Optional[int] = 12345) -> List[Node]:
        random.seed(seed)
        
        if len(self.nodes) < cycle_size:
            raise ValueError("not enough nodes to build negative cycle")
        
        chosen = random.sample(list(self.nodes), cycle_size)
        norm = [self._normalize_name(x) for x in chosen]
        
        for i in range(cycle_size):
            a = norm[i]
            b = norm[(i + 1) % cycle_size]
            found = False
        
            for idx, (nb, w) in enumerate(self.adj.get(a, [])):
                if nb == b:
                    self.adj[a][idx] = (nb, float(cycle_edge_weight))
                    found = True
                    break
        
            if not found:
                self.adj.setdefault(a, []).append((b, float(cycle_edge_weight)))
                self.adj.setdefault(b, []).append((a, float(cycle_edge_weight)))
                self.nodes.add(a); self.nodes.add(b)
        
            for idx, (nb, w) in enumerate(self.adj.get(b, [])):
                if nb == a:
                    self.adj[b][idx] = (nb, float(cycle_edge_weight))
                    break
        return norm
