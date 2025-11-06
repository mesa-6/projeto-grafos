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

