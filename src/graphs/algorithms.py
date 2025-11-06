from typing import List, Dict, Any
from src.graphs.graph import Graph

# Itera  os nós e retorna métricas de cada bairro.
def ego_metrics_all(graph: Graph) -> List[Dict[str, Any]]:
    out = []
    
    for n in graph.nodes_list():
        out.append(graph.ego_metrics(n))
    
    return out

# Retorna métricas do grafo completo
def compute_global_density(graph: Graph) -> Dict[str, Any]:    
    N = len(graph.nodes_list())
    edges = graph.edges_list()
    
    E = len(edges)
    dens = 0.0
    
    if N > 1:
        dens = (2.0 * E) / (N * (N - 1))

    return {"ordem": N, "tamanho": E, "densidade": round(dens, 4)}

# Itera as microrregioes conhecidas no graph e calcula stats via graph.microrregiao_stats
def microrregioes_stats_from_graph(graph: Graph) -> List[Dict[str, Any]]:
    mrs = set(graph.bairro_to_microrregiao.values())
    out = []
    
    for mr in sorted(mrs):
        stats = graph.microrregiao_stats(mr)
       
        if stats:
            out.append(stats)
    
    return out