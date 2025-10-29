from pathlib import Path
import re
import unicodedata
import pandas as pd

# Função para detectar colunas no formato N.M em um arquivo CSV
def detect_melt_columns(csv_path):
    # 1. Converte o caminho em um objeto Path
    csv_path = Path(csv_path)

    # 2. Garante que o arquivo realmente existe
    if not csv_path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {csv_path}")

    # 3. Lê apenas o cabeçalho (primeira linha)
    df_head = pd.read_csv(csv_path, nrows=0, dtype=str, encoding='utf-8-sig')
    cols = list(df_head.columns)

    # 4. Define um padrão de expressão regular: um ou mais dígitos, ponto, um ou mais dígitos
    pattern = re.compile(r'^\d+\.\d+$')

    # 5. Filtrar apenas as colunas que batem com esse padrão
    melt_cols = [c for c in cols if pattern.match(str(c).strip())]

    # 6. Retornar a lista final de colunas detectadas
    return melt_cols

# Função para ler o CSV completo e realizar o melt
def melt_bairros_raw(csv_path):
    # 1. Detecta as colunas que serão derretidas
    melt_cols = detect_melt_columns(csv_path)

    # 2. Lê o CSV completo
    df = pd.read_csv(csv_path, dtype=str, encoding='utf-8-sig')

    # 3. Aplicar o melt
    df_melted = df.melt(value_vars=melt_cols, var_name='microrregiao_raw', value_name='bairro')

    # 4. Retornar o DataFrame resultante
    return df_melted

# Função para ler o CSV de bairros e aplicar o melt
def melt_bairros_csv(csv_path: str) -> pd.DataFrame:
    # 1. Lê o CSV
    df = pd.read_csv(csv_path)

    # 2. Detecta as colunas numeradas (1.1, 1.2, etc.)
    melt_cols = detect_melt_columns(csv_path)

    # 3. Aplica o melt
    melted = df.melt(
        value_vars=melt_cols,
        var_name="coluna_origem",
        value_name="bairro"
    )

    # 4. Remove linhas vazias (sem bairro)
    melted = melted.dropna(subset=["bairro"])
    melted = melted[melted["bairro"].str.strip() != ""]

    # 5. Cria coluna de microrregião
    melted["microrregiao"] = melted["coluna_origem"].str.split(".").str[0]

    # 6. Normaliza o texto dos bairros
    melted["bairro"] = melted["bairro"].str.strip()
    melted["bairro"] = melted["bairro"].apply(
        lambda x: "".join(
            c for c in unicodedata.normalize("NFD", x) 
            if unicodedata.category(c) != "Mn"
            ) if isinstance(x, str) else x
    )

    # 7. Remove duplicatas e ordena
    melted = melted.drop_duplicates(subset=["bairro"])
    melted = melted.sort_values(by=["microrregiao"]).reset_index(drop=True)

    # Remove a coluna de origem
    melted = melted.drop(columns=["coluna_origem"])

    # 8. Salva o resultado em um novo CSV
    out_dir = Path(__file__).resolve().parents[2] / "data"
    out_dir.mkdir(parents=True, exist_ok=True)

    # define o arquivo final
    out_file = out_dir / "bairros_unique.csv"

    # salva o CSV
    melted.to_csv(out_file, index=False)

    print(f"[melt_bairros_csv] arquivo salvo em: {out_file.resolve()}")

    return melted