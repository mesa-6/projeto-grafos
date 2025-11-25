# src/graphs/exporters.py
from pathlib import Path
from typing import List
from pyvis.network import Network
from src.config import OUT_DIR
import json
import math

# garante saída
OUT_DIR.mkdir(parents=True, exist_ok=True)

def _basic_pyvis_network(title: str = "Grafo", height="800px", width="100%", bgcolor="#222222", font_color="white") -> Network:
    net = Network(height=height, width=width, bgcolor=bgcolor, font_color=font_color)

    net.set_options("""
    var options = {
      "nodes": {
        "font": {"size": 14}
      },
      "edges": {
        "smooth": {"enabled": true}
      },
      "physics": {
        "enabled": true,
        "stabilization": {"iterations": 200}
      }
    }
    """)

    return net

# Gera HTML com todo o grafo
def export_full_graph_html(graph, out_file: Path = None) -> str:
    if out_file is None:
        out_file = OUT_DIR / "grafo_completo.html"

    net = _basic_pyvis_network(title="Grafo Completo")
    
    nodes_meta = graph.nodes_metadata()
    
    for n in nodes_meta:
        grau = n.get("grau", 1)
        size = 10 + min(60, int(grau * 3))
        net.add_node(n["id"], label=n["id"], title=f"{n['id']} (grau={n['grau']})", size=size)
    
    for e in graph.edges_list():
        net.add_edge(e["bairro_origem"], e["bairro_destino"], title=f"Rua: {e['logradouro']}\\nPeso: {e['peso']}", value=max(1.0, float(e['peso'])))

    out_file = str(out_file)
    net.write_html(out_file)

    return out_file

# Gera arquivos HTML por microrregião 
def export_per_microrregiao_htmls(graph) -> List[str]:
    generated = []
  
    mr_map = {}

    for b, mr in graph.bairro_to_microrregiao.items():
        mr_map.setdefault(mr, []).append(b)

    for mr, bairros in mr_map.items():
        net = _basic_pyvis_network(title=f"Microrregiao {mr}")
        
        for b in bairros:
            net.add_node(b, label=b, title=b, size=18, color="orange")
        
        for e in graph.edges_list():
            if e["bairro_origem"] in bairros and e["bairro_destino"] in bairros:
                net.add_edge(e["bairro_origem"], e["bairro_destino"], title=f'Rua: {e["logradouro"]}\\nPeso:{e["peso"]}', value=max(1.0, float(e["peso"])))

        fname = OUT_DIR / f'microrregiao_{mr}.html'

        net.write_html(str(fname))
        generated.append(str(fname))
   
    return generated

# Gera um HTML simples que desenha a 'árvore/linha' do percurso Nova Descoberta -> Boa Viagem
def export_route_tree_html(caminho: List[str], logradouros: List[str], out_file: Path) -> str:
    net = _basic_pyvis_network(title="Percurso")
    # Nós na ordem do caminho
    for i, node in enumerate(caminho):
        size = 32 if (i == 0 or i == len(caminho)-1) else 20
        color = "#00ff66" if i == 0 else ("#ff6666" if i == len(caminho)-1 else "orange")
        net.add_node(node, label=node, title=node, physics=False, color=color, size=size)
    
    for i in range(len(caminho)-1):
        u = caminho[i]; v = caminho[i+1]
        rua = logradouros[i] if i < len(logradouros) else ""
        net.add_edge(u, v, title=f'Rua: {rua}', color="red", width=4)

    out_file = str(out_file)
    net.write_html(out_file)

    return out_file

# Função usada pela api para gerar os entregáveis
def export_all_pyvis_htmls(graph) -> List[str]:
    generated = []
    generated.append(export_full_graph_html(graph))
    generated += export_per_microrregiao_htmls(graph)
    
    return generated
