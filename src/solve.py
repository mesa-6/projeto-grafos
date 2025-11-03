from pathlib import Path
import pandas as pd
import json

data_path = Path(__file__).resolve().parent.parent / 'data'
out_path = Path(__file__).resolve().parent.parent / 'out'

adjacencias_file = data_path / 'adjacencias_bairros.csv'
microrregiao_file = data_path / 'bairros_unique.csv'

df_adjacencias = pd.read_csv(adjacencias_file)
df_microrregiao = pd.read_csv(microrregiao_file)

# Aplicar padronização nos nomes dos bairros (remover acentos e colocar em maiúsculas)
def padronizar_nome_bairro(nome: str) -> str:
    traducoes = str.maketrans(
        'áàãâäéèêëíìîïóòõôöúùûüçÁÀÃÂÄÉÈÊËÍÌÎÏÓÒÕÔÖÚÙÛÜÇ',
        'aaaaaeeeeiiiiooooouuuucAAAAAEEEEIIIIOOOOOUUUUC'
    )
    nome_padronizado = nome.translate(traducoes).strip()
    return nome_padronizado

df_adjacencias['bairro_origem'] = df_adjacencias['bairro_origem'].apply(padronizar_nome_bairro)
df_adjacencias['bairro_destino'] = df_adjacencias['bairro_destino'].apply(padronizar_nome_bairro)

def densidade_cidade(df_adjacencias: pd.DataFrame, df_microrregiao: pd.DataFrame) -> float:
    E = len(df_adjacencias)
    N = len(df_microrregiao)
    D = (2 * E) / (N * (N - 1))

    return D

cidade_densidade = densidade_cidade(df_adjacencias, df_microrregiao)
cidade_densidade = round(cidade_densidade, 4)

output_data = {
    "ordem": len(df_microrregiao),
    "tamanho": len(df_adjacencias),
    "densidade": cidade_densidade
}

with open(out_path / 'recife_global.json', 'w') as f:
    json.dump(output_data, f, indent=4)

# Função para calcular a densidade por microrregião
def densidade_microrregiao(df_adjacencias: pd.DataFrame, df_microrregiao: pd.DataFrame) -> list:
    densidades = []

    for mr in df_microrregiao['microrregiao'].unique():
        bairros_na_microrregiao = df_microrregiao[df_microrregiao['microrregiao'] == mr]['bairro']

        N = len(bairros_na_microrregiao)

        subgraph = df_adjacencias[
            (df_adjacencias['bairro_origem'].isin(bairros_na_microrregiao)) &
            (df_adjacencias['bairro_destino'].isin(bairros_na_microrregiao))
        ]

        E = len(subgraph)
        D = (2 * E) / (N * (N - 1)) if N > 1 else 0

        microrregiao_data = {
            "microrregiao": int(mr),
            "ordem": N,
            "tamanho": E,
            "densidade": round(D, 4)
        }

        densidades.append(microrregiao_data)

    return densidades


# Exportar dados para um arquivo microrregioes.json
densidades_microrregiao = densidade_microrregiao(df_adjacencias, df_microrregiao)

with open(out_path / 'microrregioes.json', 'w') as f:
    json.dump(densidades_microrregiao, f, indent=4)

def ego_subrede_bairros(df_adjacencias: pd.DataFrame) -> list:
    ego_data = []

    bairros = pd.unique(df_adjacencias[['bairro_origem', 'bairro_destino']].values.ravel('K'))

    for bairro in bairros:

        vizinhos_origem = df_adjacencias[df_adjacencias['bairro_origem'] == bairro]['bairro_destino'].tolist()
        vizinhos_destino = df_adjacencias[df_adjacencias['bairro_destino'] == bairro]['bairro_origem'].tolist()

        # Transformar em uma lista única de vizinhos
        vizinhos = list(set(vizinhos_origem + vizinhos_destino))

        vizinhos.append(bairro) 

        N = len(vizinhos)

        subgraph = df_adjacencias[
            (df_adjacencias['bairro_origem'].isin(vizinhos)) &
            (df_adjacencias['bairro_destino'].isin(vizinhos))
        ]

        E = len(subgraph)
        D = (2 * E) / (N * (N - 1)) if N > 1 else 0

        grau = len(vizinhos) - 1

        bairro_data = {
            "bairro": bairro,
            "grau": grau,
            "ordem_ego": N,
            "tamanho_ego": E,
            "densidade_ego": round(D, 4)
        }

        ego_data.append(bairro_data)

    return ego_data

# Exportar dados para um arquivo ego_bairro.csv
ego_bairros = ego_subrede_bairros(df_adjacencias)
ego_bairros_df = pd.DataFrame(ego_bairros)
ego_bairros_df.to_csv(out_path / 'ego_bairro.csv', index=False)

# Arquivo graus.csv
graus_df = ego_bairros_df[['bairro', 'grau']]
graus_df.to_csv(out_path / 'graus.csv', index=False)

ego_bairros_df.sort_values(by='densidade_ego', ascending=False, inplace=True)
print(f'O bairro mais denso é {ego_bairros_df.iloc[0]["bairro"]} com densidade {ego_bairros_df.iloc[0]["densidade_ego"]}')

ego_bairros_df.sort_values(by='grau', ascending=False, inplace=True)
print(f'O bairro com maior grau é {ego_bairros_df.iloc[0]["bairro"]} com grau {ego_bairros_df.iloc[0]["grau"]}')