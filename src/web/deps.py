from fastapi import HTTPException
from typing import Dict

from src.graphs.graph import Graph
from src.graphs.music_graph import MusicGraph

_GRAPHS: Dict[str, object] = {}

_PART1_CSV = "data/adjacencias_bairros.csv"
_PART1_BAIRROS_CSV = "data/bairros_unique.csv"
_PART2_CSV = "data/parte2_adjacencias.csv"

def get_graph(graph: str = "part1"):
    key = (graph or "part1").lower()

    if key in ("part1", "bairros"):
        if "bairros" not in _GRAPHS:
            try:
                g = Graph.load_from_files(_PART1_CSV, bairros_path=_PART1_BAIRROS_CSV)
            except FileNotFoundError:
                g = None

            if g is None:
                raise HTTPException(status_code=404, detail=f"Bairros CSV not found: {_PART1_CSV}")

            _GRAPHS["bairros"] = g

        return _GRAPHS["bairros"]

    if key in ("part2", "musicas", "songs"):
        if "musicas" not in _GRAPHS:
            try:
                mg = MusicGraph.load_from_edges_csv(_PART2_CSV)
            except FileNotFoundError:
                raise HTTPException(status_code=404, detail=f"Musicas CSV not found: {_PART2_CSV}")
            
            _GRAPHS["musicas"] = mg

        return _GRAPHS["musicas"]

    raise HTTPException(status_code=400, detail=f"unknown graph key: {graph}")
