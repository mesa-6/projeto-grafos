from tempfile import NamedTemporaryFile
from pyvis.network import Network
from math import cos, sin, pi
from pathlib import Path

import pandas as pd
import heapq
import json

data_path = Path(__file__).resolve().parent.parent.parent / 'data'
out_path = Path(__file__).resolve().parent.parent.parent / 'out'

adjacencias_file = data_path / 'adjacencias_bairros.csv'
enderecos_file = data_path / 'enderecos.csv'

df_adjacencias = pd.read_csv(adjacencias_file)
df_enderecos = pd.read_csv(enderecos_file)

# função para normalizar uma string (remover acentuação)
def padronizar_nome(variable: str) -> str:
    traducoes = str.maketrans(
        'áàãâäéèêëíìîïóòõôöúùûüçÁÀÃÂÄÉÈÊËÍÌÎÏÓÒÕÔÖÚÙÛÜÇ',
        'aaaaaeeeeiiiiooooouuuucAAAAAEEEEIIIIOOOOOUUUUC'
    )

    nome_padronizado = variable.translate(traducoes).strip()
    return nome_padronizado

def montar_grafo(df_adjacencias: pd.DataFrame) -> dict:
    graph = {}

    for _, row in df_adjacencias.iterrows():
        origem = padronizar_nome(row['bairro_origem'])
        destino = padronizar_nome(row['bairro_destino'])
        peso = row['peso']

        if origem not in graph:
            graph[origem] = []
        if destino not in graph:
            graph[destino] = []

        graph[origem].append((destino, peso, row['logradouro']))
        graph[destino].append((origem, peso, row['logradouro'])) 

    return graph

# Implementação do algoritmo de Dijkstra para encontrar o caminho mais curto
def dijkstra(df_adjacencias: pd.DataFrame, origem: str, destino: str) -> tuple:
    
    graph = montar_grafo(df_adjacencias)

    fila_prioridade = []

    heapq.heappush(fila_prioridade, (0, origem, [origem], []))  # (peso acumulado, bairro atual, caminho, logradouros)

    visitados = set()

    while fila_prioridade:
        peso_atual, bairro_atual, caminho_atual, logradouros_atual = heapq.heappop(fila_prioridade)

        if bairro_atual in visitados:
            continue

        visitados.add(bairro_atual)

        if bairro_atual == destino:
            return caminho_atual, peso_atual, logradouros_atual

        viz_list = graph.get(bairro_atual, [])

        for vizinho, peso, logradouro in viz_list:
            if vizinho in visitados:
                continue

            # calcula nova distância e empilha
            nova_distancia = peso_atual + peso
            novo_caminho = caminho_atual + [vizinho]
            novos_logradouros = logradouros_atual + [logradouro]
            heapq.heappush(fila_prioridade, (nova_distancia, vizinho, novo_caminho, novos_logradouros))

    return [], float('inf')

df_adjacencias['bairro_origem'] = df_adjacencias['bairro_origem'].apply(padronizar_nome)
df_adjacencias['bairro_destino'] = df_adjacencias['bairro_destino'].apply(padronizar_nome)

# Aplicar Dijkstra para cada par de bairros de endereços
resultados_caminhos = []

for _, row in df_enderecos.iterrows():
    bairro_origem = padronizar_nome(row['bairro_origem'])
    bairro_destino = padronizar_nome(row['bairro_destino'])

    caminho, peso_total, logradouros = dijkstra(df_adjacencias, bairro_origem, bairro_destino)

    if bairro_origem == "Nova Descoberta" and bairro_destino == "Boa Viagem":
        # salvar caminho em out/percurso_nova_descoberta_setubal.json
        percurso_path = out_path / 'percurso_nova_descoberta_setubal.json'

        percurso_data = {
            'bairro_origem': bairro_origem,
            'bairro_destino': bairro_destino,
            'custo': peso_total,
            'caminho': caminho,
            'ruas': logradouros,
        }

        with open(percurso_path, 'w', encoding='utf-8') as f:
            json.dump(percurso_data, f, ensure_ascii=False, indent=4)

    resultados_caminhos.append({
        'bairro_origem': bairro_origem,
        'bairro_destino': bairro_destino,
        'custo': peso_total,
        'caminho': ' -> '.join(caminho),
    })
    
# Salvar resultados em um arquivo csv
resultados_df = pd.DataFrame(resultados_caminhos)
resultados_df.to_csv(out_path / 'distancias_enderecos.csv', index=False)

def _radial_positions(nodes: list, radius: int = 300, center=(0,0)):
    n = len(nodes)
    cx, cy = center
    positions = {}
    if n == 0:
        return positions
    for i, node in enumerate(nodes):
        angle = 2 * pi * i / n
        x = cx + radius * cos(angle)
        y = cy + radius * sin(angle)
        positions[node] = (int(x), int(y))
    return positions

def criar_arvore_percurso(caminho: list, logradouros: list, out_file: Path):
    out_file = str(out_file) if isinstance(out_file, Path) else out_file

    if not out_file.lower().endswith('.html'):
        out_file += '.html'

    nodes = list(dict.fromkeys(caminho))  
    pos = _radial_positions(nodes, radius=380, center=(0,0))

    net = Network(height='800px', width='100%', bgcolor='#222222', font_color='white')
    
    net.set_options("""
    var options = {
      "physics": {
        "enabled": false
      },
      "nodes": {
        "font": {"size": 16, "face":"Arial"},
        "shape": "dot",
        "scaling": {"min": 10, "max": 40}
      },
      "edges": {
        "smooth": {"type":"cubicBezier"},
        "arrows": {"to": {"enabled": false}}
      }
    }
    """)

    for node in nodes:
        x, y = pos.get(node, (0,0))
        
        if node == caminho[0]:
            color = '#00ff66' 
            size = 32
        elif node == caminho[-1]:
            color = '#ff6666'  
            size = 32
        else:
            color = 'orange'
            size = 22

        net.add_node(node, label=node, title=node, x=x, y=y, physics=False, color=color, size=size)

    for i in range(len(caminho) - 1):
        origem = caminho[i]
        destino = caminho[i + 1]
        logradouro = logradouros[i] if i < len(logradouros) else ''
        net.add_edge(origem, destino,
                     title=f'Rua: {logradouro}',
                     color='red',
                     width=4,
                     smooth=True)

    net.write_html(out_file)

with open(out_path / 'percurso_nova_descoberta_setubal.json', 'r', encoding='utf-8') as f:
    percurso_data = json.load(f)

caminho = percurso_data['caminho']
logradouros = percurso_data['ruas']

# Gerar arquivo do percurso específico pedido pela professora
path_str = f'{out_path}/arvore_percurso.html'

criar_arvore_percurso(caminho, logradouros, path_str)

# Geração dos subgrafos por microrregião
df_bairros_unique = pd.read_csv(data_path / 'bairros_unique.csv')

microrregioes = df_bairros_unique['microrregiao'].unique()

for microrregiao in microrregioes:
    bairros_microrregiao = df_bairros_unique[df_bairros_unique['microrregiao'] == microrregiao]['bairro'].tolist()
    
    # Filtrar adjacências para incluir apenas aquelas entre bairros da microrregião
    df_adjacencias_microrregiao = df_adjacencias[
        (df_adjacencias['bairro_origem'].isin(bairros_microrregiao)) &
        (df_adjacencias['bairro_destino'].isin(bairros_microrregiao))
    ]
    
    # Criar grafo e visualização
    graph = montar_grafo(df_adjacencias_microrregiao)
    
    net = Network(height='800px', width='100%', bgcolor='#222222', font_color='white')
    net.set_options("""
    var options = {
      "physics": {
        "enabled": true
      },
      "nodes": {
        "font": {"size": 16, "face":"Arial"},
        "shape": "dot",
        "scaling": {"min": 10, "max": 40}
      },
      "edges": {
        "smooth": {"type":"cubicBezier"},
        "arrows": {"to": {"enabled": false}}
      }
    }
    """)
    
    for bairro in bairros_microrregiao:
        net.add_node(bairro, label=bairro, title=bairro, color='orange', size=20)
    
    for _, row in df_adjacencias_microrregiao.iterrows():
        net.add_edge(row['bairro_origem'], row['bairro_destino'],
                     title=f'Peso: {row["peso"]}\nRua: {row["logradouro"]}',
                     color='lightblue',
                     width=2,
                     smooth=True)
    
    out_file = out_path / f'out_{str(microrregiao).replace(" ", "_").lower()}.html'
    net.write_html(str(out_file))

# Geração do grafo relativo a densidade de cada bairro
df_ego_bairros = pd.read_csv(out_path / 'ego_bairro.csv')

net = Network(height='800px', width='100%', bgcolor='#222222', font_color='white')

net.set_options("""
var options = {
  "layout": {
    "improvedLayout": true
  },
  "physics": {
    "enabled": true,
    "stabilization": {
      "enabled": true,
      "iterations": 2000,
      "updateInterval": 25,
      "onlyDynamicEdges": false
    },
    "barnesHut": {
      "gravitationalConstant": -8000,
      "centralGravity": 0.25,
      "springLength": 200,
      "springConstant": 0.03,
      "avoidOverlap": 1
    },
    "minVelocity": 0.75
  },
  "nodes": {
    "font": {"size": 14, "face":"Arial"},
    "shape": "dot",
    "scaling": {"min": 10, "max": 80}
  },
  "edges": {
    "smooth": {"type":"cubicBezier"},
    "arrows": {"to": {"enabled": false}}
  }
}
""")

for _, row in df_ego_bairros.iterrows():
    bairro = row['bairro']
    densidade = row['densidade_ego']
    valor = max(1, densidade * 100)
    net.add_node(bairro, label=bairro, title=f'{bairro} - densidade: {densidade:.4f}', color='lightgreen', value=valor)

graph_completo = montar_grafo(df_adjacencias)

for origem, viz_list in graph_completo.items():
    for destino, peso, logradouro in viz_list:
        if net.get_node(origem) and net.get_node(destino):
            net.add_edge(origem, destino,
                         title=f'Peso: {peso}\nRua: {logradouro}',
                         color='lightblue',
                         width=1,
                         smooth=True)
            
out_file = out_path / 'densidade_conexoes_bairros.html'
net.write_html(str(out_file))

# Grafo dos vizinhos - interativo
net = Network(height='800px', width='100%', bgcolor='#222222', font_color='white')
net.set_options("""
var options = {
    "physics": {"enabled": true},
    "nodes": {"font": {"size": 14, "face":"Arial"}, "shape": "dot"},
    "edges": {"smooth": {"type":"cubicBezier"}}
}
""")

bairros = sorted(set(df_adjacencias['bairro_origem']).union(set(df_adjacencias['bairro_destino'])))
for bairro in bairros:
        net.add_node(bairro, label=bairro, title=bairro, color='orange', size=20)

for _, row in df_adjacencias.iterrows():
        net.add_edge(row['bairro_origem'], row['bairro_destino'],
                                 title=f'Peso: {row["peso"]}\\nRua: {row["logradouro"]}',
                                 color='lightblue', width=2, smooth=True)

tmp = NamedTemporaryFile(delete=False, suffix='.html')
net.write_html(tmp.name)

with open(tmp.name, 'r', encoding='utf-8') as f:
        html = f.read()

# script que destaca nó selecionado (vermelho), vizinhos (verde) e desatura os outros (cinza)
highlight_script = r"""
<script type="text/javascript">
// aguardar que a variável 'network' exista no escopo gerado pelo pyvis
(function waitForNetwork(){
    if(typeof network === "undefined"){
        setTimeout(waitForNetwork, 50);
        return;
    }

    function resetStyles(){
        var allNodes = network.body.data.nodes.get();
        var allEdges = network.body.data.edges.get();
        var nUpdate = allNodes.map(function(n){ return {id:n.id, color:{background:'orange'}, size:20}; });
        var eUpdate = allEdges.map(function(e){ return {id:e.id, color:{color:'lightblue'}, width:2}; });
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
                nUpdate.push({id:n.id, color:{background:'#ff6666'}, size:36}); // selecionado
            } else if(neighbors.indexOf(n.id) !== -1){
                nUpdate.push({id:n.id, color:{background:'#00ff66'}, size:28}); // vizinhos
            } else {
                nUpdate.push({id:n.id, color:{background:'#777777'}, size:12}); // outros
            }
        });

        var eUpdate = [];
        allEdges.forEach(function(e){
            // destacar arestas que toquem o nó selecionado ou conectem dois vizinhos selecionados
            if(e.from === nodeId || e.to === nodeId || neighbors.indexOf(e.from)!==-1 && neighbors.indexOf(e.to)!==-1){
                eUpdate.push({id:e.id, color:{color:'#ff4444'}, width:4});
            } else {
                eUpdate.push({id:e.id, color:{color:'#cccccc'}, width:1});
            }
        });

        network.body.data.nodes.update(nUpdate);
        network.body.data.edges.update(eUpdate);
    });

    // clique duplo ou tecla Esc reseta
    network.on("doubleClick", function(){ resetStyles(); });
    document.addEventListener('keydown', function(evt){
        if(evt.key === "Escape") resetStyles();
    });

})();
</script>
"""

# inserir o script antes do </body> final
if "</body>" in html:
        html = html.replace("</body>", highlight_script + "\n</body>")
else:
        html = html + highlight_script

out_file = out_path / 'interactive_bairro_vizinhos.html'
with open(out_file, 'w', encoding='utf-8') as f:
        f.write(html)