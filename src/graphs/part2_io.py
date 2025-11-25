from pathlib import Path
import pandas as pd
from typing import List

def _parse_genres_field(raw) -> List[str]:
    if raw is None:
        return []

    s = str(raw).strip()

    if s == "[]":
        return []

    if s.startswith("[") and s.endswith("]"):
        s = s[1:-1].strip()

    if not s:
        return []

    parts = [p.strip().strip("'\"") for p in s.split(",") if p.strip().strip("'\"")]

    seen = set()
    genres = []

    for p in parts:
        p_lower = p.lower()

        if p_lower not in seen:
            seen.add(p_lower)
            genres.append(p_lower)

    return genres

def prepare_spotify(input_csv: str | Path) -> pd.DataFrame:
    input_p = Path(input_csv)
    output_p = Path(input_csv).resolve().parent / "spotify_filtered.csv"

    if not input_p.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {input_p}")

    df = pd.read_csv(input_p, dtype=str, encoding="utf-8-sig", keep_default_na=False, na_values=["", " ", "nan", "NaN", "None"])

    if "track_name" not in df.columns:
        raise KeyError("Coluna 'track_name' não encontrada no CSV. Verifique o arquivo.")

    if "artist_name" not in df.columns:
        raise KeyError("Coluna 'artist_name' não encontrada no CSV. Verifique o arquivo.")

    df["artist_genres"] = df["artist_genres"].fillna("")
    df["genres_list"] = df["artist_genres"].apply(_parse_genres_field)
    df["n_genres"] = df["genres_list"].apply(len)

    df_filtered = df[df["n_genres"] > 0].copy()

    df_filtered["track_name"] = df_filtered["track_name"].astype(str).str.strip()
    df_filtered["artist_name"] = df_filtered["artist_name"].astype(str).str.strip()

    df_filtered = df_filtered[df_filtered["genres_list"].apply(lambda x: x == ["pop"])]

    dup_series = df_filtered["track_name"].duplicated(keep='first')
    n_duplicates = int(dup_series.sum())

    if n_duplicates > 0:
        if True:
            print(f"[prepare_spotify] duplicatas detectadas (track_name): {n_duplicates} — serão removidas (mantendo a primeira ocorrência).")
        df_filtered = df_filtered[~dup_series].copy()
    else:
        if True:
            print("[prepare_spotify] nenhuma duplicata de 'track_name' encontrada.")

    output_p.parent.mkdir(parents=True, exist_ok=True)
    df_filtered.to_csv(output_p, index=False, encoding="utf-8-sig")

    return df_filtered
