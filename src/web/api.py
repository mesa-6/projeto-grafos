from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, List

from src.graphs.exporters import export_all_pyvis_htmls
from src.graphs.graph import Graph
from src.web.deps import get_graph

app = FastAPI(title="Projeto Grafos - API", version="0.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", tags=["infra"])
def health() -> Dict[str, Any]:
    return {"status": "ok"}

@app.get("/nodes", tags=["graph"])
def api_nodes(graph: Graph = Depends(get_graph)):
    # Retorna os bairros com metadados (id, grau, microrregiao)
    nodes = graph.nodes_metadata()

    return {"count": len(nodes), "nodes": nodes}

@app.get("/edges", tags=["graph"])
def api_edges(graph: Graph = Depends(get_graph)):
    # Retorna arestas: origem,destino,logradouro,peso
    edges = graph.edges_list()

    return {"count": len(edges), "edges": edges}

@app.get("/dijkstra", tags=["algorithms"])
def api_dijkstra(orig: str = Query(...), dest: str = Query(...), graph: Graph = Depends(get_graph)):
    # Dijkstra: /dijkstra?orig=A&dest=B
    origem_n = graph.normalize_node(orig)
    dest_n = graph.normalize_node(dest)

    if not graph.has_node(origem_n) or not graph.has_node(dest_n):
        raise HTTPException(status_code=404, detail="origem ou destino não encontrados no grafo")

    path_nodes, path_ruas, custo = graph.dijkstra(origem_n, dest_n)

    return {"orig": origem_n, "dest": dest_n, "custo": custo, "caminho": path_nodes, "ruas": path_ruas}

@app.get("/ego/{node}", tags=["algorithms"])
def api_ego(node: str, graph: Graph = Depends(get_graph)):
    # Retorna métricas a respeito da ego-network de um bairro
    n = graph.normalize_node(node)

    if not graph.has_node(n):
        raise HTTPException(status_code=404, detail="nó não encontrado")
    
    metrics = graph.ego_metrics(n)

    return metrics

@app.get("/microrregiao/{mr_id}", tags=["algorithms"])
def api_microrregiao(mr_id: str, graph: Graph = Depends(get_graph)):
    # Retorna métricas a respeito de uma microrregião
    stats = graph.microrregiao_stats(mr_id)

    if stats is None:
        raise HTTPException(status_code=404, detail="microrregião não encontrada")
    
    return stats

@app.post("/export/static-html", tags=["export"])
def api_export_static_html(graph: Graph = Depends(get_graph)):
    # Endpoint que gera todos os entregáveis que são automatizados
    files = export_all_pyvis_htmls(graph)
    
    return {"generated": files}