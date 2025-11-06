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
