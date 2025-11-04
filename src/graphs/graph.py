# graph.py
from pathlib import Path
import pandas as pd
import json
import unicodedata

BASE = Path(__file__).resolve().parents[2]
DATA_DIR = BASE / "data"
OUT_DIR = BASE / "out"
ADJ_FILE = DATA_DIR / "adjacencias_bairros.csv"

def padronizar_nome(s):
    if not isinstance(s, str):
        return s
    s = s.strip()
    s = unicodedata.normalize("NFD", s)
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    return s

def build_graph_struct(df_adjacencias):
    df = df_adjacencias.copy()
    # normaliza
    if 'bairro_origem' in df.columns:
        df['bairro_origem'] = df['bairro_origem'].apply(padronizar_nome)
    if 'bairro_destino' in df.columns:
        df['bairro_destino'] = df['bairro_destino'].apply(padronizar_nome)

    nodes_ordered = []
    seen = set()
    edges = []
    eid = 0
    degree = {}
    for _, r in df.iterrows():
        a = str(r['bairro_origem'])
        b = str(r['bairro_destino'])
        if a not in seen:
            nodes_ordered.append(a); seen.add(a)
        if b not in seen:
            nodes_ordered.append(b); seen.add(b)
        try:
            w = float(r.get('peso', 1.0))
        except Exception:
            w = 1.0
        log = r.get('logradouro', '') if 'logradouro' in r.index else ''
        edges.append({
            "id": f"e{eid}",
            "from": a,
            "to": b,
            "weight": w,
            "label": str(w),
            "logradouro": str(log)
        })
        # degree
        degree[a] = degree.get(a, 0) + 1
        degree[b] = degree.get(b, 0) + 1
        eid += 1

    # compute node sizes from degree for nicer visualization
    nodes = []
    for n in nodes_ordered:
        deg = degree.get(n, 0)
        size = 18 + min(deg * 4, 36)  # between 18 and 54
        nodes.append({"id": n, "label": n, "size": size, "degree": deg})

    return {"nodes": nodes, "edges": edges}

def gerar_html_interativo(df_adjacencias, out_file: Path, title: str = "Grafo de Bairros - Fullscreen"):
    out_file = Path(out_file)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    graph_struct = build_graph_struct(df_adjacencias)
    graph_json = json.dumps(graph_struct, ensure_ascii=False)

    # Template NÃO é f-string — vamos substituir placeholders para evitar conflitos com '{ }' do JS
    template = r"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>__TITLE__</title>

  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&display=swap" rel="stylesheet">

  <style>
    :root{
      --bg:#0f1720;
      --panel:#0b1220;
      --muted:#9aa4b2;
      --accent:#7c3aed;
      --accent-2:#ff6b6b;
      --card:#0e1722;
      --glass: rgba(255,255,255,0.03);
      --radius:14px;
    }
    *{box-sizing:border-box;font-family:Inter, Arial, sans-serif}
    html,body,#root{height:100%}
    body{margin:0;background:linear-gradient(180deg,#071024 0%, #0a1220 100%);color:#e6eef6;overflow:hidden}
    .app{
      display:grid;
      grid-template-columns: 360px 1fr;
      grid-template-rows: auto 1fr;
      height:100vh;
      gap:12px;
      padding:14px;
      align-items:start;
    }

    /* header (full width across grid) */
    header.app-header{
      grid-column: 1 / span 2;
      display:flex;
      align-items:center;
      justify-content:space-between;
      gap:12px;
      padding:12px;
      background:linear-gradient(180deg, rgba(255,255,255,0.02), transparent);
      border-radius:var(--radius);
      border: 1px solid rgba(255,255,255,0.03);
      box-shadow: 0 6px 24px rgba(2,6,23,0.6);
    }
    .title{
      display:flex;gap:12px;align-items:center;
    }
    .logo{
      width:44px;height:44px;border-radius:10px;background:linear-gradient(135deg,var(--accent), #4c51bf);
      display:flex;align-items:center;justify-content:center;font-weight:800;color:white;font-size:18px;box-shadow:0 6px 18px rgba(124,58,237,0.18)
    }
    h1{margin:0;font-size:18px;letter-spacing:-0.2px}
    p.sub{margin:0;color:var(--muted);font-size:13px}

    /* left panel */
    .panel{
      background: linear-gradient(180deg, rgba(255,255,255,0.02), transparent);
      border-radius:12px;
      padding:16px;
      border:1px solid rgba(255,255,255,0.03);
      height: calc(100vh - 130px);
      overflow:auto;
      box-shadow: 0 6px 24px rgba(2,6,23,0.5);
    }

    .controls-group{display:flex;flex-direction:column;gap:10px;margin-bottom:12px}
    label.small{font-size:12px;color:var(--muted);margin-bottom:6px;display:block}
    input[type="text"], select{
      background:var(--glass);border:1px solid rgba(255,255,255,0.03);padding:10px 12px;border-radius:10px;color:#fff;
      outline:none;font-size:14px;
    }
    .row{display:flex;gap:8px}
    button.btn{
      border:0;padding:10px 12px;border-radius:12px;background:linear-gradient(90deg,var(--accent), #4c51bf);color:#fff;font-weight:600;
      box-shadow: 0 8px 20px rgba(124,58,237,0.12);cursor:pointer;
    }
    button.ghost{background:transparent;border:1px solid rgba(255,255,255,0.04);color:var(--muted)}
    .small-btn{padding:8px 10px;border-radius:10px;font-weight:600}

    .controls-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px}

    .meta{
      margin-top:8px;padding:10px;border-radius:10px;background:linear-gradient(180deg, rgba(255,255,255,0.01), transparent);border:1px solid rgba(255,255,255,0.02);
      color:var(--muted);font-size:13px
    }

    .legend{display:flex;gap:8px;flex-wrap:wrap;align-items:center;font-size:13px}
    .legend .item{display:flex;gap:8px;align-items:center}
    .dot{width:12px;height:12px;border-radius:6px;display:inline-block}

    /* graph container */
    .canvas-wrap{position:relative;height: calc(100vh - 110px);border-radius:12px;overflow:hidden;border:1px solid rgba(255,255,255,0.03);background:linear-gradient(180deg,#071227, #081124)}
    #mynetwork{width:100%;height:100%}

    /* Right-side floating info card */
    .info-card{
      position:absolute;right:18px;top:18px;z-index:999;min-width:260px;background:linear-gradient(180deg, rgba(0,0,0,0.35), rgba(255,255,255,0.02));
      border-radius:12px;padding:12px;border:1px solid rgba(255,255,255,0.03);color:#e6eef6;backdrop-filter: blur(6px);
    }
    .info-card h3{margin:0 0 6px 0;font-size:14px}
    .path-list{margin:8px 0;padding:8px;background:rgba(255,255,255,0.02);border-radius:8px;max-height:220px;overflow:auto}
    .path-list li{padding:6px 4px;border-bottom:1px dashed rgba(255,255,255,0.02);font-size:13px}
    .controls-footer{display:flex;gap:8px;align-items:center;justify-content:space-between;margin-top:10px}

    /* responsive */
    @media (max-width:900px){
      .app{grid-template-columns: 1fr;grid-template-rows:auto 1fr;}
      .panel{height:auto;max-height:320px}
      .info-card{position:static;margin-top:8px}
    }

  </style>
  <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
</head>
<body>
  <div class="app" id="root">
    <header class="app-header">
      <div class="title">
        <div class="logo">G</div>
        <div>
          <h1>Grafo de Bairros — Interativo</h1>
          <p class="sub">Escolha dois bairros ou clique em nós — o menor caminho é destacado.</p>
        </div>
      </div>
      <div style="display:flex;gap:8px;align-items:center">
        <button class="ghost small-btn" id="btnFit">Ajustar</button>
        <button class="ghost small-btn" id="btnZoomIn">+</button>
        <button class="ghost small-btn" id="btnZoomOut">−</button>
        <button class="ghost small-btn" id="btnToggleLabels">Peso</button>
        <button class="ghost small-btn" id="btnTogglePhysics">Physics</button>
      </div>
    </header>

    <div class="panel">
      <div class="controls-group">
        <div>
          <label class="small">Buscar bairro</label>
          <input id="inpSearch" list="nodesList" placeholder="Digite para buscar..." />
          <datalist id="nodesList"></datalist>
        </div>

        <div class="controls-grid">
          <div>
            <label class="small">Origem</label>
            <select id="selSource"></select>
          </div>
          <div>
            <label class="small">Destino</label>
            <select id="selTarget"></select>
          </div>
        </div>

        <div class="row">
          <button class="btn" id="btnCalc">Calcular caminho</button>
          <button class="ghost small-btn" id="btnClear">Limpar</button>
        </div>

        <div style="display:flex;gap:8px;margin-top:6px">
          <button class="ghost small-btn" id="btnRadial">Layout Radial</button>
          <button class="ghost small-btn" id="btnRandom">Layout Aleatório</button>
        </div>

      </div>

      <div class="meta">
        <div style="display:flex;justify-content:space-between;align-items:center">
          <div><strong id="nodesCount">0</strong> nós</div>
          <div><strong id="edgesCount">0</strong> arestas</div>
        </div>
        <div style="margin-top:8px" class="legend">
          <div class="item"><span class="dot" style="background: #00ff66"></span> Origem</div>
          <div class="item"><span class="dot" style="background: #ff6666"></span> Destino</div>
          <div class="item"><span class="dot" style="background: orange"></span> Nós</div>
          <div class="item"><span style="color:red">—</span> Percurso</div>
        </div>
      </div>

      <div style="margin-top:12px">
        <div style="font-size:13px;color:var(--muted);margin-bottom:6px">Informações do percurso</div>
        <div class="path-info">
          <div style="display:flex;gap:8px;align-items:center">
            <div style="font-size:12px;color:var(--muted)">Custo total:</div>
            <div style="font-weight:700" id="totalCost">—</div>
          </div>
          <div style="margin-top:8px;font-size:13px;color:var(--muted)">Ruas (hover nas arestas para ver):</div>
          <ul class="path-list" id="streetsList"></ul>
        </div>
      </div>

    </div>

    <div class="canvas-wrap">
      <div id="mynetwork"></div>

      <div class="info-card" id="infoCard" style="display:none">
        <h3>Percurso</h3>
        <div><strong id="infoCost">Custo: —</strong></div>
        <ol id="pathNodes" style="margin:8px 0 0 0;padding-left:16px"></ol>
        <div class="controls-footer">
          <button class="ghost small-btn" id="cardClear">Limpar</button>
          <button class="ghost small-btn" id="cardFit">Ajustar</button>
        </div>
      </div>

    </div>

  </div>

<script>
const GRAPH = __GRAPH_JSON__;

// --- construir datasets vis ---
const nodes = new vis.DataSet(GRAPH.nodes.map(n => ({
  id: n.id, label: n.label, title: n.label, size: n.size || 20, color: 'orange'
})));

const edges = new vis.DataSet(GRAPH.edges.map(e => ({
  id: e.id, from: e.from, to: e.to, label: String(e.weight), title: (e.logradouro || '') + " — peso: " + e.weight, color: '#4b5563', width:1
})));

const container = document.getElementById('mynetwork');
const data = { nodes: nodes, edges: edges };
let options = {
  physics: { enabled: true, stabilization:{ iterations: 150, fit: true } },
  nodes: {
    font: {size:14, face:'Inter'},
    borderWidth: 2,
    shape: 'dot'
  },
  edges: {
    color: {inherit: false},
    smooth: {type:'dynamic'},
    arrows: { to: {enabled:false} },
    font: {align:'middle'}
  },
  interaction: { hover:true, tooltipDelay: 100, multiselect:false, navigationButtons:true }
};
const network = new vis.Network(container, data, options);

// preencher contadores e selects e datalist
document.getElementById('nodesCount').innerText = GRAPH.nodes.length;
document.getElementById('edgesCount').innerText = GRAPH.edges.length;

const selSource = document.getElementById('selSource');
const selTarget = document.getElementById('selTarget');
const nodesList = document.getElementById('nodesList');

GRAPH.nodes.forEach(n => {
  const o = document.createElement('option'); o.value = n.id; o.text = n.label;
  selSource.appendChild(o.cloneNode(true));
  selTarget.appendChild(o.cloneNode(true));
  const d = document.createElement('option'); d.value = n.id; d.text = n.label;
  nodesList.appendChild(d);
});

// clicar em nó: normal -> origem, shift+click -> destino
network.on("click", function(params) {
  if(params.nodes && params.nodes.length) {
    const nodeId = params.nodes[0];
    if(params.event.srcEvent.shiftKey) selTarget.value = nodeId;
    else selSource.value = nodeId;
  }
});

// permitir duplo clique para centralizar
network.on("doubleClick", function(params) {
  if(params.nodes && params.nodes.length) {
    network.focus(params.nodes[0], {scale:1.4, animation:{duration:400}});
  }
});

// construir adj list com edgeId para retornar arestas do percurso
const adj = {};
GRAPH.edges.forEach(e => {
  if(!(e.from in adj)) adj[e.from] = [];
  if(!(e.to in adj)) adj[e.to] = [];
  adj[e.from].push({to: e.to, weight: Number(e.weight), edgeId: e.id});
  adj[e.to].push({to: e.from, weight: Number(e.weight), edgeId: e.id});
});

// --- Função Dijkstra (JS) retornando também edgeIds ---
function dijkstra(start, goal) {
  const nodesList = GRAPH.nodes.map(n => n.id);
  const dist = {}; const prev = {}; const Q = new Set(nodesList);
  nodesList.forEach(n => { dist[n] = Infinity; prev[n] = null; });
  if(!(start in adj) || !(goal in adj)) return {path:[], cost:Infinity, edges:[]};
  dist[start] = 0;
  while(Q.size > 0) {
    let u = null; let min = Infinity;
    Q.forEach(n => { if(dist[n] < min) { min = dist[n]; u = n; } });
    if(u === null || min === Infinity) break;
    Q.delete(u);
    if(u === goal) break;
    const neigh = adj[u] || [];
    for(const nb of neigh) {
      if(!Q.has(nb.to)) continue;
      const alt = dist[u] + nb.weight;
      if(alt < dist[nb.to]) { dist[nb.to] = alt; prev[nb.to] = {node: u, edgeId: nb.edgeId}; }
    }
  }
  if(dist[goal] === Infinity) return {path:[], cost:Infinity, edges:[]};
  const pathNodes = []; const pathEdges = [];
  let cur = goal;
  while(cur) {
    pathNodes.unshift(cur);
    if(prev[cur]) { pathEdges.unshift(prev[cur].edgeId); cur = prev[cur].node; } else break;
  }
  return {path: pathNodes, cost: dist[goal], edges: pathEdges};
}

// reset estilos
function resetStyles() {
  edges.forEach(e => edges.update({id:e.id, color:'#4b5563', width:1}));
  nodes.forEach(n => nodes.update({id:n.id, color:'orange'}));
  document.getElementById('totalCost').innerText = "—";
  document.getElementById('streetsList').innerHTML = "";
  document.getElementById('infoCard').style.display = 'none';
  document.getElementById('pathNodes').innerHTML = "";
  document.getElementById('infoCost').innerText = "Custo: —";
}

// highlight do caminho e preencher painel
function highlightPath(res) {
  resetStyles();
  if(!res.path || res.path.length === 0) return;
  // destacar arestas
  res.edges.forEach(eid => {
    edges.update({id: eid, color: '#ff6b6b', width:4});
  });
  // destacar nós
  res.path.forEach((nid, i) => {
    const isStart = (i === 0);
    const isEnd = (i === res.path.length -1);
    nodes.update({id: nid, color: isStart ? '#00ff66' : (isEnd ? '#ff6666' : '#ffd580')});
  });

  // exibir custo e ruas
  document.getElementById('totalCost').innerText = res.cost.toFixed(3);
  const streetsEl = document.getElementById('streetsList');
  streetsEl.innerHTML = "";
  // obter ruas a partir dos edge ids (GRAPH.edges contém logradouro)
  const streetNames = res.edges.map(eid => {
    const e = GRAPH.edges.find(x => x.id === eid);
    return (e && e.logradouro) ? e.logradouro : ('aresta ' + eid);
  });
  // dedup & append
  const seen = new Set();
  streetNames.forEach(s => { if(!seen.has(s)){ seen.add(s); const li = document.createElement('li'); li.innerText = s; streetsEl.appendChild(li); }});

  // preencher info card
  const info = document.getElementById('infoCard');
  const ol = document.getElementById('pathNodes');
  ol.innerHTML = "";
  res.path.forEach((n,i) => {
    const li = document.createElement('li'); li.innerText = n; ol.appendChild(li);
  });
  document.getElementById('infoCost').innerText = "Custo: " + res.cost.toFixed(3);
  info.style.display = 'block';

  // ajustar viewport
  try { network.fit({nodes: res.path, animation: {duration:400}}); } catch(e) {}
}

// UI handlers
document.getElementById('btnCalc').addEventListener('click', () => {
  const s = selSource.value; const t = selTarget.value;
  if(!s || !t) return alert('Escolha origem e destino');
  const r = dijkstra(s,t);
  if(!r.path || r.path.length === 0) return alert('Não há caminho entre os nós selecionados.');
  highlightPath(r);
});

document.getElementById('btnClear').addEventListener('click', resetStyles);
document.getElementById('cardClear').addEventListener('click', resetStyles);
document.getElementById('btnFit').addEventListener('click', () => { network.fit({animation:{duration:300}}); });
document.getElementById('cardFit').addEventListener('click', () => { network.fit({animation:{duration:300}}); });
document.getElementById('btnZoomIn').addEventListener('click', () => { const scale = network.getScale(); network.moveTo({scale: Math.min(scale * 1.2, 2) }); });
document.getElementById('btnZoomOut').addEventListener('click', () => { const scale = network.getScale(); network.moveTo({scale: Math.max(scale / 1.2, 0.25) }); });

let labelsOn = true;
document.getElementById('btnToggleLabels').addEventListener('click', () => {
  labelsOn = !labelsOn;
  edges.forEach(e => edges.update({id:e.id, label: labelsOn ? e.label : ''}));
});

let physicsOn = true;
document.getElementById('btnTogglePhysics').addEventListener('click', () => {
  physicsOn = !physicsOn;
  network.setOptions({physics:{enabled:physicsOn}});
});

document.getElementById('inpSearch').addEventListener('change', (ev) => {
  const v = ev.target.value;
  if(!v) return;
  // focus on node if exists
  const node = GRAPH.nodes.find(n => n.id === v || n.label === v);
  if(node) {
    network.focus(node.id, {scale:1.6, animation:{duration:400}});
    // flash highlight
    nodes.update({id: node.id, color: '#7c3aed'});
    setTimeout(()=> nodes.update({id: node.id, color: 'orange'}), 900);
  } else {
    // try fuzzy: find first with includes
    const found = GRAPH.nodes.find(n => n.label.toLowerCase().includes(v.toLowerCase()));
    if(found) {
      network.focus(found.id, {scale:1.5, animation:{duration:400}});
      nodes.update({id: found.id, color: '#7c3aed'});
      setTimeout(()=> nodes.update({id: found.id, color: 'orange'}), 900);
    } else {
      alert('Bairro não encontrado.');
    }
  }
});

// Layout helpers: radial / random
function radialLayout() {
  const nodesArr = GRAPH.nodes.map(n => n.id);
  const N = nodesArr.length;
  const cx = 0, cy = 0; const radius = Math.min(window.innerWidth, window.innerHeight) * 0.35;
  const positions = {};
  nodesArr.forEach((id,i) => {
    const angle = 2 * Math.PI * i / N;
    positions[id] = {x: Math.round(radius * Math.cos(angle)), y: Math.round(radius * Math.sin(angle))};
  });
  const update = nodesArr.map(id => ({id, ...positions[id], fixed:true}));
  nodes.update(update);
  network.setOptions({physics:{enabled:false}});
  setTimeout(()=> network.fit({animation:{duration:400}}), 120);
}
function randomLayout() {
  const nodesArr = GRAPH.nodes.map(n => n.id);
  const update = nodesArr.map(id => ({id, x: Math.round((Math.random()-0.5)*1200), y: Math.round((Math.random()-0.5)*800), fixed:true}));
  nodes.update(update);
  network.setOptions({physics:{enabled:false}});
  setTimeout(()=> network.fit({animation:{duration:400}}), 120);
}

document.getElementById('btnRadial').addEventListener('click', radialLayout);
document.getElementById('btnRandom').addEventListener('click', randomLayout);

// initialize: fit view
setTimeout(()=> network.fit({animation:{duration:600}}), 300);

</script>
</body>
</html>
"""

    html = template.replace("__GRAPH_JSON__", graph_json).replace("__TITLE__", title)
    out_file.write_text(html, encoding='utf-8')
    print(f"[graph.py] HTML interativo gerado em: {out_file.resolve()}")

if __name__ == "__main__":
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if not ADJ_FILE.exists():
        raise FileNotFoundError(f"Arquivo de adjacências não encontrado: {ADJ_FILE}")
    df_adj = pd.read_csv(ADJ_FILE)
    gerar_html_interativo(df_adj, OUT_DIR / "grafo_interativo_fullscreen.html", title="Grafo de Bairros — Fullscreen")
