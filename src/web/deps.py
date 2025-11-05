from src.config import ADJACENCIAS_CSV, BAIRROS_UNIQUE_CSV
from src.graphs.graph import Graph
from functools import lru_cache
from pathlib import Path

@lru_cache(maxsize=1)
def get_graph() -> Graph:
    adj_path = Path(ADJACENCIAS_CSV)
    bairros_path = Path(BAIRROS_UNIQUE_CSV)

    graph = Graph.load_from_files(adj_path, bairros_path)
    return graph