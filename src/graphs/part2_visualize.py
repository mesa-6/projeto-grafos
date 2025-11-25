from typing import List, Set, Dict
from src.graphs.graph import Graph
from pyvis.network import Network
from pathlib import Path
import pandas as pd
import argparse
import math
import re

def read_prepare(csv_path: str | Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path, dtype=str, keep_default_na=False)
    
    if "track_a" in df.columns and "track_b" in df.columns:
        df = df.rename(columns={"track_a": "bairro_origem", "track_b": "bairro_destino"})
    
    if "common_genres" in df.columns and "logradouro" not in df.columns:
        df = df.rename(columns={"common_genres": "logradouro"})
    
    if "peso" in df.columns:
        df["peso"] = pd.to_numeric(df["peso"], errors="coerce").fillna(1.0)
    else:
        df["peso"] = 1.0
    
    return df

def largest_component_nodes(graph: Graph) -> List[str]:
    visited = set()
    components: List[List[str]] = []

    for node in graph.nodes_list():
        if node in visited:
            continue

        stack = [node]
        comp = []

        while stack:
            u = stack.pop()

            if u in visited:
                continue
            visited.add(u)
            comp.append(u)

            for nbr in graph.adj.get(u, []):
                if isinstance(nbr, (tuple, list)) and len(nbr) >= 1:
                    v = nbr[0]
                else:
                    continue

                if v not in visited:
                    stack.append(v)

        components.append(comp)

    components.sort(key=len, reverse=True)

    return components[0] if components else []

def top_degree_nodes(graph: Graph, N: int) -> List[str]:
    degs = [(n, len(graph.adj.get(n, []))) for n in graph.nodes_list()]
    degs.sort(key=lambda x: -x[1])
    
    return [n for n, _ in degs[:N]]

def radial_positions(nodes: List[str], radius: int = 400) -> Dict[str, tuple]:
    pos: Dict[str, tuple] = {}
    n = len(nodes)

    if n == 0:
        return pos

    for i, node in enumerate(nodes):
        angle = 2 * math.pi * i / n
        x = int(radius * math.cos(angle))
        y = int(radius * math.sin(angle))
        pos[node] = (x, y)

    return pos

def patch_pyvis_html_with_cdn(html_path: str | Path) -> None:
    p = Path(html_path)

    if not p.exists():
        return

    txt = p.read_text(encoding="utf-8")

    txt = re.sub(r'<script[^>]*utils\.js[^>]*></script>\s*', '', txt, flags=re.IGNORECASE)
    txt = re.sub(r'<script[^>]*require\.js[^>]*></script>\s*', '', txt, flags=re.IGNORECASE)

    if not re.search(r'(vis-network|unpkg.com/vis-network|cdn.jsdelivr.net/npm/vis-network)', txt, flags=re.IGNORECASE):
        head_inject = (
            "\n<!-- patched: ensure vis-network is available via CDN -->\n"
            '<link href="https://unpkg.com/vis-network/styles/vis-network.min.css" rel="stylesheet" />\n'
            '<script src="https://unpkg.com/vis-data@0.11.1/peer/umd/vis-data.min.js"></script>\n'
            '<script src="https://unpkg.com/vis-network@9.1.2/dist/vis-network.min.js"></script>\n'
        )
       
        if "<head" in txt:
            txt = txt.replace("<head>", "<head>" + head_inject, 1)
        else:
            txt = head_inject + txt

    draw_call_pattern = re.compile(r'(^\s*drawGraph\(\)\s*;\s*$)', flags=re.MULTILINE)

    ensure_block = r'''
// patched: wait for vis.Network to be available before calling drawGraph()
(function ensureDraw(){
    var tries = 0;
    var max_tries = 200; // 200 * 50ms = 10 seconds timeout
    function _poll(){
        if (typeof vis !== 'undefined' && typeof vis.Network !== 'undefined'){
            try { drawGraph(); } catch(err){ console.error('drawGraph() failed after vis loaded:', err); }
            return;
        }
        tries += 1;
        if (tries > max_tries){
            console.error('ensureDraw: vis.Network not available after waiting (~10s).');
            return;
        }
        setTimeout(_poll, 50);
    }
    _poll();
})();
'''

    if draw_call_pattern.search(txt):
        txt = draw_call_pattern.sub(ensure_block, txt, count=1)
    else:
        if "</body>" in txt:
            txt = txt.replace("</body>", ensure_block + "\n</body>", 1)
        else:
            txt = txt + "\n" + ensure_block

    p.write_text(txt, encoding="utf-8")
    print(f"[patch] HTML patched with CDN + ensureDraw(): {p.resolve()}")

def patch_fix_container(html_path: str | Path) -> None:
    p = Path(html_path)
    
    if not p.exists():
        print("[patch_fix_container] arquivo nao encontrado:", p)
        return

    txt = p.read_text(encoding="utf-8")

    div_id_match = re.search(r'<div[^>]*\bid\s*=\s*"([^"]+)"', txt)
    
    if div_id_match:
        div_id = div_id_match.group(1)
        print(f"[patch_fix_container] encontrado div id='{div_id}' - usaremos como container preferido")
    else:
        div_id = None
        print("[patch_fix_container] nenhum div com id encontrado — usaremos querySelector('div') como fallback")

    draw_fn_pattern = re.compile(r'(function\s+drawGraph\s*\(\s*\)\s*\{\s*)', flags=re.MULTILINE)
    m = draw_fn_pattern.search(txt)
    
    if not m:
        draw_fn_pattern2 = re.compile(r'(var\s+drawGraph\s*=\s*function\s*\(\s*\)\s*\{\s*)', flags=re.MULTILINE)
        m = draw_fn_pattern2.search(txt)

    if not m:
        print("[patch_fix_container] aviso: não localizei function drawGraph() no HTML. Nenhuma modificação feita.")
        return

    insert_pos = m.end()

    if div_id:
        get_container_snippet = (
            "\n    // patched: obter container dinamicamente (usando id encontrado '" + div_id + "')\n"
            "    var container = document.getElementById('" + div_id + "');\n"
            "    if (!container) {\n"
            "        console.warn(\"container with id '" + div_id + "' not found; falling back to first <div> in document\");\n"
            "        container = document.querySelector('div');\n"
            "    }\n"
        )
    else:
        get_container_snippet = (
            "\n    // patched: nenhum id de div encontrado; usar primeiro <div> como fallback\n"
            "    var container = document.querySelector('div');\n"
        )

    existing_container_pattern = re.compile(
        r"var\s+container\s*=\s*document\.getElementById\s*\(\s*['\"][^'\"]+['\"]\s*\)\s*;",
        flags=re.MULTILINE,
    )

    if existing_container_pattern.search(txt):
        txt = existing_container_pattern.sub(get_container_snippet, txt, count=1)
        print("[patch_fix_container] substituída declaração existente de 'var container = document.getElementById(...)'")
    else:
        txt = txt[:insert_pos] + get_container_snippet + txt[insert_pos:]
        print("[patch_fix_container] snippet defensivo injetado dentro de drawGraph()")

    p.write_text(txt, encoding="utf-8")
    print(f"[patch_fix_container] patch aplicado em: {p.resolve()}")

def patch_safe_options_config(html_path: str | Path) -> None:
    p = Path(html_path)
    
    if not p.exists():
        return

    txt = p.read_text(encoding="utf-8")

    pattern = re.compile(
        r'options\.configure\s*\[\s*["\']container["\']\s*\]\s*=\s*document\.getElementById\s*\(\s*["\']config["\']\s*\)\s*;',
        flags=re.MULTILINE,
    )

    safe_block = (
        "try {\n"
        "    if (typeof options.configure === 'undefined' || options.configure === null) {\n"
        "        options.configure = {};\n"
        "    }\n"
        "    // set container for configure UI if present\n"
        "    var cfgContainer = document.getElementById('config');\n"
        "    if (cfgContainer) {\n"
        "        options.configure.container = cfgContainer;\n"
        "    }\n"
        "} catch (err) {\n"
        "    console.warn('patched: could not set options.configure.container', err);\n"
        "}\n"
    )

    if pattern.search(txt):
        txt = pattern.sub(safe_block, txt, count=1)
        p.write_text(txt, encoding="utf-8")
        print(f"[patch_safe_options_config] applied safe options.configure patch to {p.resolve()}")
    else:
        simple_pattern = re.compile(r'options\.configure.*container', flags=re.IGNORECASE)
        if simple_pattern.search(txt):
            txt = simple_pattern.sub(safe_block, txt, count=1)
            p.write_text(txt, encoding="utf-8")
            print(f"[patch_safe_options_config] fallback patch applied to {p.resolve()}")
        else:
            print("[patch_safe_options_config] nothing found to patch")

def build_interactive_html(graph: Graph, nodes_subset: Set[str], out_html: str, title: str = "Parte2 - Interativo", physics_threshold: int = 200) -> int:
    max_edges_per_node = 30
    nodes_list = sorted(nodes_subset)
    degs = {n: len(graph.adj.get(n, [])) for n in nodes_list}
    maxdeg = max(degs.values()) if degs else 1

    def node_size(d: int) -> int:
        return max(6, 6 + int(18 * (d / maxdeg))) if maxdeg > 0 else 8

    use_physics = len(nodes_list) <= physics_threshold
    pos = radial_positions(nodes_list, radius=380) if not use_physics else {}

    net = Network(height="850px", width="100%", bgcolor="#ffffff", font_color="black")

    try:
        if use_physics:
            net.show_buttons(filter_=["physics", "layout", "interaction"])
        else:
            net.show_buttons(filter_=["interaction"])
    except TypeError:
        try:
            if use_physics:
                net.show_buttons(filter=["physics", "layout", "interaction"])
            else:
                net.show_buttons(filter=["interaction"])
        except Exception:
            pass

    id_map = {n: f"n{i}" for i, n in enumerate(nodes_list)}
    inv_map = {v: k for k, v in id_map.items()}

    def short_label(n: str, L: int = 20) -> str:
        return n if len(n) <= L else n[: L - 1] + "…"

    for n in nodes_list:
        size = node_size(degs.get(n, 0))
        x, y = pos.get(n, (0, 0))
        lbl = short_label(n)
        node_kwargs = dict(label=lbl, title=f"{n} (deg={degs.get(n,0)})", size=size)
        
        if not use_physics:
            node_kwargs.update(dict(x=x, y=y, physics=False))
        
        node_kwargs.update(dict(color={"border":"#333","background":"#ff7f0e"}, shape='dot'))
        net.add_node(id_map[n], **node_kwargs)

    seen_pairs = set()
    edge_added = 0
  
    for u in nodes_list:
        added_for_u = 0
        nbrs = graph.adj.get(u, [])
  
        for nbr in nbrs:
            if isinstance(nbr, (list, tuple)):
                v = nbr[0] if len(nbr) >= 1 else None
                peso = nbr[1] if len(nbr) >= 2 else 1.0
                log = nbr[2] if len(nbr) >= 3 else ""
            else:
                continue

            if v is None or v not in nodes_subset:
                continue
  
            if added_for_u >= max_edges_per_node:
                break

            pair_key = tuple(sorted((u, v)))
  
            if pair_key in seen_pairs:
                continue
  
            seen_pairs.add(pair_key)
            added_for_u += 1

            try:
                w = float(peso)
            except Exception:
                w = 1.0
           
            width = 1 + min(3, math.log1p(abs(w)))
            etitle = (str(log) if log is not None else "") + f" | peso={w:.2f}"

            net.add_edge(id_map[pair_key[0]], id_map[pair_key[1]], title=etitle, value=width, width=width, physics=False)
            edge_added += 1

    net.set_options(
        """
    var options = {
      "physics": {"enabled": %s, "stabilization": {"enabled": true}},
      "manipulation": {"enabled": false},
      "nodes": {"font": {"size": 12}, "scaling": {"min":6, "max":32}},
      "edges": {"smooth": false, "scaling": {"min":1, "max": 6}, "arrows": {"to": false}}
    }
    """ % ("true" if use_physics else "false")
    )

    try:
        net.toggle_physics(use_physics)
    except Exception:
        pass

    out_p = Path(out_html)
    out_p.parent.mkdir(parents=True, exist_ok=True)

    try:
        try:
            net.write_html(str(out_p), local=True)
        except TypeError:
            try:
                net.write_html(str(out_p), embed=True)
            except TypeError:
                net.write_html(str(out_p))
    except Exception as e:
        fallback = out_p.with_suffix('.error.html')
        fallback.write_text(
            "<html><body><h2>Erro ao gerar HTML interativo</h2><pre>{}</pre><p>Verifique pyvis/vis-network</p></body></html>".format(
                str(e)
            ),
            encoding="utf-8",
        )
        raise

    try:
        patch_pyvis_html_with_cdn(out_p)
    except Exception:
        print("[warning] patch_pyvis_html_with_cdn failed - HTML may reference local assets")

    try:
        patch_fix_container(out_p)
    except Exception:
        print("[warning] patch_fix_container failed - HTML container guard not applied")

    try:
        patch_safe_options_config(out_p)
    except Exception:
        print("[warning] patch_safe_options_config failed - options.configure may be unsafe")

    try:
        txt = out_p.read_text(encoding='utf-8')
        legend_html = (
            "\n<!-- legend overlay injected by builder -->\n"
            "<style> #pv_legend{position:fixed;right:12px;top:12px;background:rgba(255,255,255,0.95);padding:8px;border-radius:8px;box-shadow:0 2px 6px rgba(0,0,0,0.15);font-family:sans-serif;font-size:12px;z-index:9999;} #pv_legend b{display:block;margin-bottom:4px;} </style>\n"
            "<div id=\"pv_legend\"><b>%s</b>Nodes: %d<br>Edges drawn: %d<br><small>Tip: hover nodes for full title, use the toolbar to zoom.</small></div>\n"
            % (title, len(nodes_list), edge_added)
        )
        
        if '<body' in txt:
            txt = re.sub(r'(<body[^>]*>)', lambda m: m.group(1) + legend_html, txt, count=1, flags=re.IGNORECASE)
        else:
            txt = legend_html + txt
        
        out_p.write_text(txt, encoding='utf-8')
    except Exception:
        pass

    return edge_added

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default="data/parte2_adjacencias.csv")
    parser.add_argument("--mode", choices=["largest_component", "top_degree"], default="largest_component")
    parser.add_argument("--max-nodes", type=int, default=800)
    parser.add_argument("--out", default="out/parte2_interactive.html")
    parser.add_argument("--max-edges-per-node", type=int, default=20)
    parser.add_argument("--physics-threshold", type=int, default=200,
                        help='if number of nodes <= threshold, enable vis physics for nicer layout')
    args = parser.parse_args()

    df = read_prepare(args.csv)
    print("[info] CSV loaded, building graph (this may take some seconds)...")
    g = Graph.build_from_df(df)
    print(f"[info] Graph built: nodes={len(g.nodes)}, approx edges={len(g.edges_list())}")

    if args.mode == "largest_component":
        comp = largest_component_nodes(g)
        print(f"[info] largest component size = {len(comp)}")
        sel = comp[: args.max_nodes] if len(comp) > args.max_nodes else comp
    else:
        sel = top_degree_nodes(g, args.max_nodes)

    print(f"[info] nodes selected = {len(sel)} (max-nodes={args.max_nodes})")
    
    if len(sel) == 0:
        raise SystemExit("No nodes selected for plotting.")

    edges = build_interactive_html(g, set(sel), args.out, physics_threshold=args.physics_threshold)
    print(f"[done] interactive HTML written to: {args.out}  (edges_drawn={edges}, nodes_drawn={len(sel)})")

if __name__ == "__main__":
    main()
