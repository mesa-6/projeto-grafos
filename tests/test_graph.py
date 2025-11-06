# scripts/test_graph.py
import sys
from pathlib import Path

# garantir que o src está no path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.web.deps import get_graph

def print_section(title: str):
    print("\n" + "=" * 80)
    print(f"🧭 {title}")
    print("=" * 80 + "\n")

def main():
    g = get_graph()

    # 1️⃣ Estrutura geral
    print_section("1️⃣ Estrutura geral do grafo")
    print(f"Total de nós: {len(g.nodes)}")
    total_arestas = sum(len(v) for v in g.adj.values())
    print(f"Total de adjacências: {total_arestas}")

    # 2️⃣ Amostra de adjacências
    print_section("2️⃣ Amostra de adjacências")
    for u in list(g.adj)[:5]:
        print(f"{u} → {g.adj[u][:3]}")

    # 3️⃣ Dijkstra entre Nova Descoberta e Boa Viagem
    print_section("3️⃣ Caminho mínimo: Nova Descoberta → Boa Viagem")
    try:
        caminho = g.dijkstra("Nova Descoberta", "Boa Viagem")
        print(caminho)
    except Exception as e:
        print(f"Erro ao executar Dijkstra: {e}")

    # 4️⃣ Mapeamento de microrregiões
    print_section("4️⃣ Mapeamento de microrregiões (amostra)")
    if hasattr(g, "bairro_to_microrregiao"):
        print(list(g.bairro_to_microrregiao.items())[:10])
    else:
        print("⚠️ Grafo não possui atributo 'bairro_to_microrregiao'.")

    # 5️⃣ Teste de cache
    print_section("5️⃣ Teste de cache (lru_cache)")
    from src.web.deps import get_graph as get_graph_cached

    g2 = get_graph_cached()
    print("Mesmo objeto em memória?", g is g2)


if __name__ == "__main__":
    main()
