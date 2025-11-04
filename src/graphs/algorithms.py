from pathlib import Path
import pandas as pd
import heapq
import json

data_path = Path(_file_).resolve().parent.parent.parent / 'data'
out_path = Path(_file_).resolve().parent.parent.parent / 'out'

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

# Transforme o percurso em árvore e mostre
# A partir do caminho “Nova Descoberta → Boa Viagem (Setúbal)”, construam
# a árvore de caminho (um subgrafo com as arestas do percurso) e exportem
# uma visualização:
# o out/arvore_percurso.html (interativa, ex.: pyvis/plotly) ou
# Requisito: destacar o caminho (cor, espessura) e mostrar rótulos dos bairros.
# Não usar bibliotecas de visualização de grafos (ex.: networkx, igraph, graph-tool).

from pyvis.network import Network
from math import cos, sin, pi
from pyvis.network import Network

def _radial_positions(nodes: list, radius: int = 300, center=(0,0)):
    """Retorna dicionário {node: (x, y)} com posições radiais uniformes."""
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
    # garantir string para pyvis
    out_file = str(out_file) if isinstance(out_file, Path) else out_file
    if not out_file.lower().endswith('.html'):
        out_file += '.html'

    # coletar nós únicos (ordem do caminho garante sequência)
    nodes = list(dict.fromkeys(caminho))  # preserva ordem e remove duplicatas
    pos = _radial_positions(nodes, radius=380, center=(0,0))

    net = Network(height='800px', width='100%', bgcolor='#222222', font_color='white')
    # opções vis.js para aparência (nó, aresta, física)
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

    # adicionar nós com posições fixas (physics desligado)
    for node in nodes:
        x, y = pos.get(node, (0,0))
        # destacar origem e destino
        if node == caminho[0]:
            color = '#00ff66'  # verde início
            size = 32
        elif node == caminho[-1]:
            color = '#ff6666'  # vermelho fim
            size = 32
        else:
            color = 'orange'
            size = 22

        net.add_node(node, label=node, title=node, x=x, y=y, physics=False, color=color, size=size)

    # adicionar todas as arestas do percurso (com tooltip do logradouro)
    for i in range(len(caminho) - 1):
        origem = caminho[i]
        destino = caminho[i + 1]
        logradouro = logradouros[i] if i < len(logradouros) else ''
        net.add_edge(origem, destino,
                     title=f'Rua: {logradouro}',
                     color='red',
                     width=4,
                     smooth=True)

    # adicionar um nó "invisível" com legenda (simples) — ou você pode inserir HTML manualmente
    # salvar
    net.write_html(out_file)

# Buscar caminho do arquivo salvo
with open(out_path / 'percurso_nova_descoberta_setubal.json', 'r', encoding='utf-8') as f:
    percurso_data = json.load(f)

caminho = percurso_data['caminho']
logradouros = percurso_data['ruas']

# transformar path em string para mandar para a função
path_str = f'{out_path}/arvore_percurso.html'

criar_arvore_percurso(caminho, logradouros, path_str)