from fastapi import FastAPI, Depends, HTTPException, Query
from src.graphs.exporters import export_all_pyvis_htmls
from fastapi.middleware.cors import CORSMiddleware
from src.graphs import algorithms as algorithms
from typing import Dict, Any, List, Optional
from src.web.deps import get_graph
from pathlib import Path
import random
import json
import copy

from src.solve import (
    generate_global_summary,
    generate_microrregioes,
    generate_ego_csvs,
    trigger_static_html_generation,
    build_local_graph,
    generate_distancias_enderecos,
    generate_percurso_nova_descoberta,
    generate_top_bairros_summary,
    generate_densidade_conexao_html,
    generate_interactive_bairro_vizinhos_html,
)

app = FastAPI(title="Projeto Grafos - API", version="0.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Endpoint de check da API 
@app.get("/health", tags=["infra"])
def health() -> Dict[str, Any]:
    return {"status": "ok"}

# Endpoint que retorna os nós do grafo
@app.get("/nodes", tags=["graph"])
def api_nodes(graph = Depends(get_graph)):
    # Se for o dataset dos bairros
    if hasattr(graph, "nodes_metadata"):
        nodes = graph.nodes_metadata()

        return {"count": len(nodes), "nodes": nodes}
    
    # Se for o dataset das músicas
    if hasattr(graph, "nodes_list"):
        nodes = graph.nodes_list()

        return {"count": len(nodes), "nodes": nodes}

# Endpoint que retorna todas as arestas do grafo
@app.get("/edges", tags=["graph"])
def api_edges(graph = Depends(get_graph)):
    # Ambos têm o mesmo método
    edges = graph.edges_list()

    return {"count": len(edges), "edges": edges}

# Dijkstra (usa graph.dijkstra se disponível, senão algorithms.dijkstra + reconstruct)
from src.graphs import algorithms as algorithms  # já deve existir no topo

@app.get("/dijkstra", tags=["algorithms"])
def api_dijkstra(orig: str = Query(...), dest: str = Query(...), graph = Depends(get_graph)):
    origem_n = getattr(graph, "normalize_node", lambda x: x)(orig)
    dest_n = getattr(graph, "normalize_node", lambda x: x)(dest)

    if hasattr(graph, "has_node") and (not graph.has_node(origem_n) or not graph.has_node(dest_n)):
        raise HTTPException(status_code=404, detail="origem ou destino não encontrados no grafo")

    res = algorithms.dijkstra(graph, origem_n, dest_n)
    
    if res.get("error"):
        raise HTTPException(status_code=400, detail=res.get("error"))

    prev = res.get("prev", {})
    prev_edge = res.get("prev_edge", {})
    dist = res.get("dist", {})
    path_nodes = algorithms.reconstruct_path(prev, dest_n)
    path_ruas = algorithms.reconstruct_path_edges(prev, prev_edge, dest_n)
    custo = dist.get(dest_n, float("inf"))

    return {"orig": origem_n, "dest": dest_n, "custo": custo, "caminho": path_nodes, "ruas": path_ruas}

# Ego - apenas para Graph (bairros)
@app.get("/ego/{node}", tags=["algorithms"])
def api_ego(node: str, graph = Depends(get_graph)):
    if not hasattr(graph, "ego_metrics"):
        raise HTTPException(status_code=400, detail="endpoint /ego is only available for bairros graph")
    
    n = graph.normalize_node(node)

    if not graph.has_node(n):
        raise HTTPException(status_code=404, detail="nó não encontrado")
    
    metrics = graph.ego_metrics(n)

    return metrics

# Microrregiao - apenas para Graph (bairros)
@app.get("/microrregiao/{mr_id}", tags=["algorithms"])
def api_microrregiao(mr_id: str, graph = Depends(get_graph)):
    if not hasattr(graph, "microrregiao_stats"):
        raise HTTPException(status_code=400, detail="endpoint /microrregiao is only available for bairros graph")
    
    stats = graph.microrregiao_stats(mr_id)

    if stats is None:
        raise HTTPException(status_code=404, detail="microrregião não encontrada")
    
    return stats

# Export static htmls (keeps working for Graph-like)
@app.post("/export/static-html", tags=["export"])
def api_export_static_html(graph = Depends(get_graph)):
    files = export_all_pyvis_htmls(graph)
    
    return {"generated": files}

@app.post("/generate/all", tags=["generate"])
def api_generate_all(graph: str = Query("part1")):
    summary = {"steps": [], "errors": []}

    # Constrói o grafo local de bairros
    try:
        summary["steps"].append("build_local_graph")
        graph_local = build_local_graph()
    except Exception as e:
        summary["errors"].append({"step": "build_local_graph", "error": str(e)})
        return {"summary": summary}

    # Gera o recife_global.json
    try:
        summary["steps"].append("generate_global_summary")
        generate_global_summary()
    except Exception as e:
        summary["errors"].append({"step": "generate_global_summary", "error": str(e)})

    # Gera o microrregioes.json
    try:
        summary["steps"].append("generate_microrregioes")
        generate_microrregioes()
    except Exception as e:
        summary["errors"].append({"step": "generate_microrregioes", "error": str(e)})

    # Gera o ego_bairro.csv
    try:
        summary["steps"].append("generate_ego_csvs")
        generate_ego_csvs()
    except Exception as e:
        summary["errors"].append({"step": "generate_ego_csvs", "error": str(e)})

    # Gera o top_bairros_summary.json
    try:
        summary["steps"].append("generate_top_bairros_summary")
        generate_top_bairros_summary(graph_local)
    except Exception as e:
        summary["errors"].append({"step": "generate_top_bairros_summary", "error": str(e)})

    # Gera o distancias_enderecos.csv
    try:
        summary["steps"].append("generate_distancias_enderecos")
        generate_distancias_enderecos(graph_local)
    except Exception as e:
        summary["errors"].append({"step": "generate_distancias_enderecos", "error": str(e)})

    # Gera o percurso_nova_descoberta_setubal.json e o arvore_percurso.html
    try:
        summary["steps"].append("generate_percurso_nova_descoberta")
        generate_percurso_nova_descoberta(graph_local)
    except Exception as e:
        summary["errors"].append({"step": "generate_percurso_nova_descoberta", "error": str(e)})    

    # Gera o densidade_conexoes_bairros.html
    try:
        summary["steps"].append("generate_densidade_conexao_html")
        generate_densidade_conexao_html(graph_local)
    except Exception as e:
        summary["errors"].append({"step": "generate_densidade_conexao_html", "error": str(e)})

    # Gera o interactive_bairro_vizinhos.html
    try:
        summary["steps"].append("generate_interactive_bairro_vizinhos_html")
        generate_interactive_bairro_vizinhos_html(graph_local)
    except Exception as e:
        summary["errors"].append({"step": "generate_interactive_bairro_vizinhos_html", "error": str(e)})

    # Gera os HTMLs das microrregiões e o grafo_completo.html
    try:
        summary["steps"].append("trigger_static_html_generation")
        trigger_static_html_generation()
    except Exception as e:
        summary["errors"].append({"step": "trigger_static_html_generation", "error": str(e)})

    return {"summary": summary}

@app.get("/bfs", tags=["algorithms"])
def api_bfs(source: str = Query(...), graph = Depends(get_graph)):
    src_n = getattr(graph, "normalize_node", lambda x: x)(source)
    has_node_fn = getattr(graph, "has_node", None)
    
    if has_node_fn and not has_node_fn(src_n):
        raise HTTPException(status_code=404, detail="source not found in graph")
    
    res = algorithms.bfs(graph, src_n)
    
    return {"source": src_n, **res}

@app.get("/dfs", tags=["algorithms"])
def api_dfs(sources: Optional[List[str]] = Query(None), graph = Depends(get_graph)):
    norm_sources = None
    
    if sources:
        norm_sources = [getattr(graph, "normalize_node", lambda x: x)(s) for s in sources]
        
        for s in norm_sources:
            if hasattr(graph, "has_node") and not graph.has_node(s):
                raise HTTPException(status_code=404, detail=f"source '{s}' not found in graph")
    
    res = algorithms.dfs(graph, sources=norm_sources)
    
    return {"sources": norm_sources or [], **res}

@app.get("/bellman-ford", tags=["algorithms"])
def api_bellman_ford(orig: str = Query(...), dest: Optional[str] = Query(None), graph = Depends(get_graph)):
    src_n = getattr(graph, "normalize_node", lambda x: x)(orig)
    
    if hasattr(graph, "has_node") and not graph.has_node(src_n):
        raise HTTPException(status_code=404, detail="origem não encontrada")
    
    res = algorithms.bellman_ford(graph, src_n)
    
    if dest:
        dst_n = getattr(graph, "normalize_node", lambda x: x)(dest)
    
        if hasattr(graph, "has_node") and not graph.has_node(dst_n):
            raise HTTPException(status_code=404, detail="destino não encontrado")
    
        prev = res.get("prev", {})
        path = algorithms.reconstruct_path(prev, dst_n)
        dist = res.get("dist", {}).get(dst_n)
    
        return {"orig": src_n, "dest": dst_n, "time_sec": res.get("time_sec"), "dist": dist, "path": path, "negative_cycle": res.get("negative_cycle")}
    
    return {"orig": src_n, "time_sec": res.get("time_sec"), "negative_cycle": res.get("negative_cycle"), "distances": res.get("dist")}

@app.get("/floyd-warshall", tags=["algorithms"])
def api_floyd_warshall(graph = Depends(get_graph)):
    N = len(graph.nodes_list())
    
    if N > 800:
        raise HTTPException(status_code=400, detail="graph too large for Floyd-Warshall via API; select a smaller subgraph")
    
    dist_map = algorithms.floyd_warshall(graph)
    
    return {"n_nodes": N, "distances": dist_map}

@app.post("/bench", tags=["bench"])
def api_bench(graph = Depends(get_graph)):
    """
    Executa a bateria de benchmarks:
      - 10 BFS
      - 10 DFS
      - 10 Dijkstra
      - 5 Bellman-Ford (com variações de injeção de arestas negativas)
    Salva out/parte2_report.json e retorna um sumário.
    """

    out_dir = Path("out")
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / "parte2_report.json"

    nodes = list(graph.nodes_list())
    N = len(nodes)

    if N == 0:
        raise HTTPException(status_code=400, detail="graph has no nodes")

    random_seed = 12345
    random.seed(random_seed)

    normalizer = getattr(graph, "normalize_node", lambda x: x)

    def sample_sources(k: int) -> List[str]:
        if N >= k:
            return random.sample(nodes, k)
        else:
            return [random.choice(nodes) for _ in range(k)]

    def sample_pairs(k: int) -> List[tuple]:
        pairs = []
        
        if N == 1:
            for _ in range(k):
                pairs.append((nodes[0], nodes[0]))
        
            return pairs
        
        tries = 0
        
        while len(pairs) < k and tries < k * 50:
            a, b = random.sample(nodes, 2)
            pairs.append((a, b))
            tries += 1
        
        while len(pairs) < k:
            a = random.choice(nodes)
            b = random.choice(nodes)
            pairs.append((a, b))
        
        return pairs

    bench_result: Dict[str, Any] = {"meta": {"n_nodes": N, "seed": random_seed, "graph": getattr(graph, '__class__', type(graph)).__name__}, "runs": {}}

    # BFS x10
    bfs_sources = sample_sources(10)
    bfs_runs = []
    
    for s in bfs_sources:
        s_norm = normalizer(s)
    
        try:
            r = algorithms.bfs(graph, s_norm)
            bfs_runs.append({"source": s_norm, "time_sec": r.get("time_sec"), "n_reached": len([v for v in r.get("dist", {}) if r.get("dist", {})[v] is not None])})
        except Exception as e:
            bfs_runs.append({"source": s_norm, "error": str(e)})
    
    bench_result["runs"]["bfs"] = bfs_runs

    # DFS x10
    dfs_sources = sample_sources(10)
    dfs_runs = []
    
    for s in dfs_sources:
        s_norm = normalizer(s)
    
        try:
            res = algorithms.dfs(graph, sources=[s_norm])
            dfs_runs.append({"source": s_norm, "time_sec": res.get("time_sec"), "n_ordered": len(res.get("order", []))})
        except Exception as e:
            dfs_runs.append({"source": s_norm, "error": str(e)})
    
    bench_result["runs"]["dfs"] = dfs_runs

    # Dijkstra x10
    dijkstra_pairs = sample_pairs(10)
    dijkstra_runs = []
    
    for a, b in dijkstra_pairs:
        a_norm = normalizer(a)
        b_norm = normalizer(b)
    
        try:
            res = algorithms.dijkstra(graph, a_norm, b_norm)
    
            if "error" in res:
                dijkstra_runs.append({"orig": a_norm, "dest": b_norm, "error": res.get("error")})
            else:
                dist = res.get("dist", {}).get(b_norm, float("inf"))
                dijkstra_runs.append({"orig": a_norm, "dest": b_norm, "time_sec": res.get("time_sec"), "dist": dist})
        except Exception as e:
            dijkstra_runs.append({"orig": a_norm, "dest": b_norm, "error": str(e)})
    
    bench_result["runs"]["dijkstra"] = dijkstra_runs

    # Bellman-Ford x5 (pares) -- substitua a seção atual por isto
    bf_pairs = sample_pairs(5)
    bf_runs = []

    for i, (a, b) in enumerate(bf_pairs):
        a_norm = normalizer(a)
        b_norm = normalizer(b)

        try:
            # trabalhar em cópia para NÃO alterar o grafo global
            g_copy = copy.deepcopy(graph)

            # cenário decide o que injetar:
            # i == 0..1 -> negativos espalhados (sem ciclo forçado)
            # i == 2   -> negativos com fração maior (chance maior de caminhos negativos)
            # i == 3   -> nenhum negativo (controle)
            # i == 4   -> injetar ciclo negativo explícito
            injected = {"negative_fraction": False, "negative_cycle": False, "notes": ""}

            if hasattr(g_copy, "apply_negative_fraction") and hasattr(g_copy, "inject_negative_cycle"):
                if i in (0, 1):
                    # pequenas frações com shift moderado -> negativos, provavelmente sem ciclo
                    g_copy.apply_negative_fraction(negative_shift=0.6, negative_fraction=0.03, seed=12345 + i)
                    injected["negative_fraction"] = True
                    injected["notes"] = "small_fraction_shift"
                elif i == 2:
                    # maior chance de negativos (ainda sem ciclo forçado)
                    g_copy.apply_negative_fraction(negative_shift=0.8, negative_fraction=0.10, seed=54321 + i)
                    injected["negative_fraction"] = True
                    injected["notes"] = "larger_fraction_shift"
                elif i == 3:
                    # controle: sem negativos
                    injected["notes"] = "no_injection_control"
                else:  # i == 4
                    # força ciclo negativo
                    cycle_nodes = g_copy.inject_negative_cycle(cycle_size=3, cycle_edge_weight=-0.8, seed=999 + i)
                    injected["negative_cycle"] = True
                    injected["notes"] = f"cycle_nodes={cycle_nodes}"
            else:
                # fallback: se graph não tem helpers, tentar modificar manualmente m edges (pode falhar)
                injected["notes"] = "no_injection_methods_available"

            # executar BF na cópia (origem = a_norm)
            res = algorithms.bellman_ford(g_copy, a_norm)
            neg = res.get("negative_cycle")
            dist = res.get("dist", {}).get(b_norm, None)

            bf_runs.append({
                "orig": a_norm,
                "dest": b_norm,
                "time_sec": res.get("time_sec"),
                "dist": dist,
                "negative_cycle": bool(neg),
                "injected": injected
            })
        except Exception as e:
            bf_runs.append({"orig": a_norm, "dest": b_norm, "error": str(e)})

    bench_result["runs"]["bellman_ford"] = bf_runs


    try:
        with open(report_path, "w", encoding="utf-8") as fh:
            json.dump(bench_result, fh, indent=2, ensure_ascii=False)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"failed to write report: {e}")

    return {"report": str(report_path.resolve()), "summary": {k: len(v) for k, v in bench_result["runs"].items()}}
