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
