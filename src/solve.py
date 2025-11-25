from src.graphs.exporters import export_route_tree_html
from src.graphs import algorithms as algorithms
from tempfile import NamedTemporaryFile
from src.graphs.graph import Graph
from pyvis.network import Network
from pathlib import Path
import requests
import json
import time
import sys
import csv
import os

OUT_DIR = Path(__file__).resolve().parent.parent / "out"
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
OUT_DIR.mkdir(parents=True, exist_ok=True)
API_BASE = os.environ.get("GRAFOS_API_URL", "http://127.0.0.1:3000")

def fetch_nodes():
    r = requests.get(f"{API_BASE}/nodes")
    r.raise_for_status()

    return r.json()

def fetch_edges():
    r = requests.get(f"{API_BASE}/edges")
    r.raise_for_status()

    return r.json()

def fetch_microrregiao(mr_id):
    r = requests.get(f"{API_BASE}/microrregiao/{mr_id}")

    if r.status_code == 404:
        return None
    
    r.raise_for_status()

    return r.json()

def fetch_ego(node):
    r = requests.get(f"{API_BASE}/ego/{node}")

    if r.status_code == 404:
        return None
    
    r.raise_for_status()
    
    return r.json()

def trigger_static_html_generation():
    r = requests.post(f"{API_BASE}/export/static-html")
    r.raise_for_status()
    resp = r.json()
    generated = resp.get("generated", [])
    print(f"[solve] HTMLs gerados via API: {generated}")
    
    return generated

def build_local_graph():
    adj_path = DATA_DIR / "adjacencias_bairros.csv"
    mr_path = DATA_DIR / "bairros_unique.csv"

    if not adj_path.exists():
        raise FileNotFoundError(f"Arquivo de adjacências não encontrado: {adj_path}")
    
    if not mr_path.exists():
        print(f"[solve] AVISO: {mr_path} não existe; o mapeamento microrregiao ficará vazio.")
    
        return Graph.load_from_files(adj_path, None)
    
    return Graph.load_from_files(adj_path, mr_path)

def generate_distancias_enderecos(graph: Graph):
    enderecos_file = DATA_DIR / "enderecos.csv"
    out_file = OUT_DIR / "distancias_enderecos.csv"

    if not enderecos_file.exists():
        print(f"[solve] Aviso: {enderecos_file} não existe. Pulando geração de distancias_enderecos.csv")
        return

    rows_out = []
    normalizer = getattr(graph, "normalize_node", lambda x: x)

    with open(enderecos_file, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for r in reader:
            origem_raw = r.get("bairro_origem")
            destino_raw = r.get("bairro_destino")

            if not origem_raw or not destino_raw:
                continue

            origem = normalizer(origem_raw)
            destino = normalizer(destino_raw)

            res = algorithms.dijkstra(graph, origem, destino)

            if res.get("error"):
                custo_val = float("inf")
                caminho = []
            else:
                prev = res.get("prev", {}) or {}
                caminho = algorithms.reconstruct_path(prev, destino)
                custo_val = float(res.get("dist", {}).get(destino, float("inf")))

            caminho_str = " -> ".join(caminho) if caminho else ""
            rows_out.append({
                "bairro_origem": origem_raw,
                "bairro_destino": destino_raw,
                "custo": round(custo_val, 4) if custo_val != float("inf") else "",
                "caminho": caminho_str
            })

    keys = ["bairro_origem", "bairro_destino", "custo", "caminho"]

    with open(out_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()

        for r in rows_out:
            writer.writerow(r)

    print(f"[solve] distancias_enderecos.csv gerado: {out_file}")

def generate_percurso_nova_descoberta(graph: Graph):
    origem = "NOVA DESCOBERTA"
    destino = "BOA VIAGEM"
    
    res = algorithms.dijkstra(graph, origem, destino)

    prev = res.get("prev", {})
    prev_edge = res.get("prev_edge", {})
    dist = res.get("dist", {})
    path_nodes = algorithms.reconstruct_path(prev, destino)
    path_ruas = algorithms.reconstruct_path_edges(prev, prev_edge, destino)
    custo = dist.get(destino, float("inf"))

    custo, caminho, ruas = custo, path_nodes, path_ruas

    out_json = OUT_DIR / "percurso_nova_descoberta_setubal.json"
    data = {
        "bairro_origem": origem,
        "bairro_destino": destino,
        "custo": round(float(custo), 4) if custo != float("inf") else None,
        "caminho": caminho,
        "ruas": ruas
    }

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    print(f"[solve] percurso JSON gerado: {out_json}")
    out_html = OUT_DIR / "arvore_percurso.html"

    try:
        export_route_tree_html(caminho, ruas, out_html)
        print(f"[solve] arvore_percurso.html gerado: {out_html}")
    except Exception as e:
        print(f"[solve] ERRO ao gerar arvore_percurso.html: {e}")

def generate_top_bairros_summary(graph: Graph):
    nodes_meta = graph.nodes_metadata()

    if not nodes_meta:
        print("[solve] AVISO: graph.nodes_metadata() vazio. Pulando top summary.")
        return

    maior_grau = max(nodes_meta, key=lambda x: x.get("grau", 0))
    melhor_dens = None

    for n in graph.nodes_list():
        m = graph.ego_metrics(n)

        if melhor_dens is None or m["densidade_ego"] > melhor_dens["densidade_ego"]:
            melhor_dens = m

    out = {
        "maior_grau": maior_grau,
        "maior_densidade_ego": melhor_dens
    }
    out_file = OUT_DIR / "top_bairros_summary.json"

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=4)
    print(f"[solve] top_bairros_summary.json gerado: {out_file}")

def generate_densidade_conexao_html(graph: Graph):
    out_html = OUT_DIR / "densidade_conexoes_bairros.html"
    dens_map = {}

    for n in graph.nodes_list():
        m = graph.ego_metrics(n)
        dens_map[n] = float(m["densidade_ego"])

    dens_values = list(dens_map.values()) if dens_map else [0.0]
    min_dens = min(dens_values)
    max_dens = max(dens_values)

    min_size = 8
    max_size = 36   
    
    if max_size < min_size:
        max_size = min_size + 10

    net = Network(height="900px", width="100%", bgcolor="#222222", font_color="white")
    net.set_options("""
    var options = {
      "physics": {
        "enabled": true,
        "barnesHut": {
          "gravitationalConstant": -3000,
          "centralGravity": 0.2,
          "springLength": 200,
          "springConstant": 0.04,
          "avoidOverlap": 1
        },
        "stabilization": {"iterations": 250, "updateInterval": 50}
      },
      "nodes": {
        "font": {"size": 12, "face":"Arial"},
        "shape": "dot",
        "scaling": {"min": %d, "max": %d}
      },
      "edges": {
        "smooth": {"enabled": true}
      }
    }
    """ % (min_size, max_size)
    )

    def dens_to_size(d):
        try:
            d = float(d)
        except Exception:
            d = 0.0
    
        if max_dens == min_dens:
            return int((min_size + max_size) / 2)
    
        frac = (d - min_dens) / (max_dens - min_dens)
        size = min_size + frac * (max_size - min_size)
    
        if size < min_size:
            size = min_size
    
        if size > max_size:
            size = max_size
    
        return int(size)

    all_edges = graph.edges_list()
    peso_vals = [float(e.get("peso", 1.0) or 0.0) for e in all_edges] if all_edges else [1.0]
    max_peso = max(peso_vals) if peso_vals else 1.0
    
    if max_peso <= 0:
        max_peso = 1.0

    for n, dens in dens_map.items():
        size = dens_to_size(dens)
        net.add_node(n, label=n, title=f"{n} - densidade: {dens:.4f}", size=size, color="lightgreen")

    for e in all_edges:
        origem = e["bairro_origem"]
        destino = e["bairro_destino"]
        log = e.get("logradouro", "")
        peso = float(e.get("peso", 1.0) or 0.0)
        width = 1 + (peso / max_peso) * 3.0
    
        if width < 1:
            width = 1
    
        if width > 5:
            width = 5
    
        net.add_edge(origem, destino, title=f"Rua: {log}\\nPeso: {peso}", value=max(1.0, float(peso)), width=width)

    net.write_html(str(out_html))
    print(f"[solve] densidade_conexao_bairros.html gerado: {out_html} (nodes sizes in [{min_size},{max_size}])")

def generate_interactive_bairro_vizinhos_html(graph: Graph):
    out_html = OUT_DIR / "interactive_bairro_vizinhos.html"

    net = Network(height="900px", width="100%", bgcolor="#222222", font_color="white")
    net.set_options("""
    var options = {
      "layout": {"improvedLayout": true},
      "physics": {"enabled": true, "stabilization": {"iterations": 200}},
      "nodes": {"font": {"size": 14}, "shape": "dot"},
      "edges": {"smooth": {"enabled": true}}
    }
    """)

    for n in graph.nodes_list():
        net.add_node(n, label=n, title=n, color="orange", size=18)

    for e in graph.edges_list():
        net.add_edge(e["bairro_origem"], e["bairro_destino"], title=f"Peso: {e['peso']}\\nRua: {e['logradouro']}", color="lightblue", width=1)

    tmp = NamedTemporaryFile(delete=False, suffix=".html")
    net.write_html(tmp.name)

    highlight_script = r"""
<script type="text/javascript">
(function waitForNetwork(){
    if(typeof network === "undefined"){
        setTimeout(waitForNetwork, 50);
        return;
    }

    function resetStyles(){
        var allNodes = network.body.data.nodes.get();
        var allEdges = network.body.data.edges.get();
        var nUpdate = allNodes.map(function(n){ return {id:n.id, color:{background:'orange'}, size:18}; });
        var eUpdate = allEdges.map(function(e){ return {id:e.id, color:{color:'lightblue'}, width:1}; });
        network.body.data.nodes.update(nUpdate);
        network.body.data.edges.update(eUpdate);
    }

    network.on("click", function(params){
        if(!params.nodes || params.nodes.length === 0){
            resetStyles();
            return;
        }
        var nodeId = params.nodes[0];
        var neighbors = network.getConnectedNodes(nodeId);
        var allNodes = network.body.data.nodes.get();
        var allEdges = network.body.data.edges.get();

        var nUpdate = [];
        allNodes.forEach(function(n){
            if(n.id === nodeId){
                nUpdate.push({id:n.id, color:{background:'#ff6666'}, size:36});
            } else if(neighbors.indexOf(n.id) !== -1){
                nUpdate.push({id:n.id, color:{background:'#00ff66'}, size:28});
            } else {
                nUpdate.push({id:n.id, color:{background:'#777777'}, size:12});
            }
        });

        var eUpdate = [];
        allEdges.forEach(function(e){
            if(e.from === nodeId || e.to === nodeId || (neighbors.indexOf(e.from)!==-1 && neighbors.indexOf(e.to)!==-1)){
                eUpdate.push({id:e.id, color:{color:'#ff4444'}, width:4});
            } else {
                eUpdate.push({id:e.id, color:{color:'#cccccc'}, width:1});
            }
        });

        network.body.data.nodes.update(nUpdate);
        network.body.data.edges.update(eUpdate);
    });

    network.on("doubleClick", function(){ resetStyles(); });
    document.addEventListener('keydown', function(evt){
        if(evt.key === "Escape") resetStyles();
    });

})();
</script>
"""

    with open(tmp.name, "r", encoding="utf-8") as f:
        html = f.read()

    if "</body>" in html:
        html = html.replace("</body>", highlight_script + "\n</body>")
    else:
        html = html + highlight_script

    with open(out_html, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"[solve] interactive_bairro_vizinhos.html gerado: {out_html}")

def generate_global_summary():
    nodes_resp = fetch_nodes()
    edges_resp = fetch_edges()

    N = nodes_resp["count"]
    E = edges_resp["count"]
    dens = 0.0
    
    if N > 1:
        dens = (2.0 * E) / (N * (N - 1))
    
    dens = round(dens, 4)
    payload = {"ordem": N, "tamanho": E, "densidade": dens}
    out_file = OUT_DIR / "recife_global.json"
    
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=4, ensure_ascii=False)
    print(f"[solve] recife_global.json gerado: {out_file}")
    
    return payload

def generate_microrregioes():
    nodes_resp = fetch_nodes()
    nodes = nodes_resp["nodes"]

    mrs = sorted({str(n.get("microrregiao")) for n in nodes if n.get("microrregiao") not in (None, "", float("nan"))})
    out_list = []
    
    for mr in mrs:
        try:
            stats = fetch_microrregiao(int(mr))
        except Exception:
            stats = None
    
        if stats:
            out_list.append(stats)
        else:
            print(f"[solve] Aviso: microrregiao {mr} retornou None/404")

    out_file = OUT_DIR / "microrregioes.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(out_list, f, indent=4, ensure_ascii=False)
    print(f"[solve] microrregioes.json gerado: {out_file}")
    
    return out_list

def generate_ego_csvs():
    nodes_resp = fetch_nodes()
    nodes = nodes_resp["nodes"]
    out_rows = []
    
    for n in nodes:
        bairro = n["id"]
        metrics = fetch_ego(bairro)
        
        if metrics is None:
            continue
        
        out_rows.append(metrics)

    ego_file = OUT_DIR / "ego_bairro.csv"
    keys = ["bairro", "grau", "ordem_ego", "tamanho_ego", "densidade_ego"]
    
    with open(ego_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        
        for row in out_rows:
            writer.writerow({k: row.get(k, "") for k in keys})
    
    print(f"[solve] ego_bairro.csv gerado: {ego_file}")
    graus_file = OUT_DIR / "graus.csv"
    
    with open(graus_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["bairro", "grau"])
        writer.writeheader()
    
        for row in out_rows:
            writer.writerow({"bairro": row.get("bairro"), "grau": row.get("grau")})
    
    print(f"[solve] graus.csv gerado: {graus_file}")
    
    return out_rows

def main():
    print("[solve] esperando a API estar disponível...", end="", flush=True)

    for i in range(10):
        try:
            r = requests.get(f"{API_BASE}/health", timeout=2.0)
            if r.status_code == 200:
                print(" OK")
                break
        except Exception:
            print(".", end="", flush=True)
            time.sleep(0.7)
    else:
        print("\n[solve] erro: não consegui conectar na API. Rode `python -m src.cli` em outro terminal e tente de novo.")
        sys.exit(1)

    generate_global_summary()
    generate_microrregioes()
    generate_ego_csvs()
    trigger_static_html_generation()

    try:
        graph = build_local_graph()
    except Exception as e:
        print(f"[solve] ERRO: nao consegui construir grafo local: {e}")
        return

    generate_distancias_enderecos(graph)
    generate_percurso_nova_descoberta(graph)
    generate_top_bairros_summary(graph)
    generate_densidade_conexao_html(graph)
    generate_interactive_bairro_vizinhos_html(graph)
    print("[solve] todos os entregáveis gerados (ver pasta out/)")

if __name__ == "__main__":
    main()
