from pathlib import Path
import re
import unicodedata
import pandas as pd

def detect_melt_columns(csv_path):
    csv_path = Path(csv_path)

    if not csv_path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {csv_path}")

    df_head = pd.read_csv(csv_path, nrows=0, dtype=str, encoding='utf-8-sig')

    cols = list(df_head.columns)

    # Padrão para detectar colunas numéricas com ponto decimal (e.g., "1.1", "2.3") via regex
    pattern = re.compile(r'^\d+\.\d+$')

    melt_cols = [c for c in cols if pattern.match(str(c).strip())]

    return melt_cols

def melt_bairros_csv(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)

    melt_cols = detect_melt_columns(csv_path)

    melted = df.melt(
        value_vars=melt_cols,
        var_name="coluna_origem",
        value_name="bairro"
    )

    melted = melted.dropna(subset=["bairro"])
    melted = melted[melted["bairro"].str.strip() != ""]

    melted["microrregiao"] = melted["coluna_origem"].str.split(".").str[0]

    melted["bairro"] = melted["bairro"].str.strip()
    melted["bairro"] = melted["bairro"].apply(
        lambda x: "".join(
            c for c in unicodedata.normalize("NFD", x) 
            if unicodedata.category(c) != "Mn"
            ) if isinstance(x, str) else x
    )

    melted = melted.drop_duplicates(subset=["bairro"])
    melted = melted.sort_values(by=["microrregiao"]).reset_index(drop=True)
    melted = melted.drop(columns=["coluna_origem"])

    out_dir = Path(__file__).resolve().parents[2] / "data"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "bairros_unique.csv"

    melted.to_csv(out_file, index=False)

    print(f"[melt_bairros_csv] arquivo salvo em: {out_file.resolve()}")

    return melted