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

    print(f"Caminho de {bairro_origem} para {bairro_destino}:")
    print(" -> ".join(caminho))
    print(f"Peso total: {peso_total}")
    print(f"Logradouros: {', '.join(logradouros)}")
    print("-" * 40)