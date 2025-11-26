from typing import Dict, Set, Tuple
from itertools import combinations
from pathlib import Path
import pandas as pd
import random
import math
import ast

def _parse_list_string(val):
    if val is None:
        return []
    
    if isinstance(val, list):
        return val
    
    s = str(val).strip()

    if s == "" or s == "[]":
        return []
    
    try:
        parsed = ast.literal_eval(s)
        if isinstance(parsed, (list, tuple, set)):
            return [str(x).strip().lower() for x in parsed if str(x).strip() != ""]
    except Exception:
        s2 = s.strip("[]")
        parts = [p.strip().strip("'\"").lower() for p in s2.split(",") if p.strip() != ""]
    
        return parts
    
    seen = set()
    out = []

    for g in parsed:
        gg = str(g).strip().lower()
    
        if gg and gg not in seen:
            seen.add(gg)
            out.append(gg)
    
    return out

def _safe_int(x, default=0):
    try:
        return int(float(x))
    except Exception:
        return default

def _safe_float(x, default=0.0):
    try:
        return float(x)
    except Exception:
        return default

def _year_from_date(s):
    try:
        if not s or str(s).strip() == "":
            return None
        return int(str(s).split("-")[0])
    except Exception:
        return None

def compute_similarity(meta_a, meta_b, globals_, weights=None):
    if weights is None:
        weights = {
            "genre": 4.0,
            "same_artist": 3.0,
            "same_album": 2.0,
            "track_pop": 1.0,
            "artist_pop": 0.5,
            "followers": 0.5,
            "duration": 0.3,
            "recency": 0.5,
            "explicit": 0.3
        }

    # Gêneros em comum (Jaccard)
    genres_a = set([g.lower() for g in (meta_a.get("genres") or [])])
    genres_b = set([g.lower() for g in (meta_b.get("genres") or [])])
    union = genres_a | genres_b
    inter = genres_a & genres_b
    genre_sim = (len(inter) / len(union)) if union else 0.0

    # Mesmo artista / mesmo álbum
    same_artist = 1.0 if (meta_a.get("artist_name") == meta_b.get("artist_name")) else 0.0
    same_album = 1.0 if (meta_a.get("album_id") and meta_a.get("album_id") == meta_b.get("album_id")) else 0.0

    # Popularidade
    ta = _safe_int(meta_a.get("track_popularity", 0))
    tb = _safe_int(meta_b.get("track_popularity", 0))
    track_pop_sim = 1.0 - (abs(ta - tb) / 100.0)

    aa = _safe_int(meta_a.get("artist_popularity", 0))
    ab = _safe_int(meta_b.get("artist_popularity", 0))
    artist_pop_sim = 1.0 - (abs(aa - ab) / 100.0)

    # Seguidores do artista 
    fa = _safe_float(meta_a.get("artist_followers", 0.0))
    fb = _safe_float(meta_b.get("artist_followers", 0.0))
    maxf = max(1.0, globals_.get("max_followers", 1.0))
    followers_sim = 1.0 - (math.log1p(abs(fa - fb)) / math.log1p(maxf))
    followers_sim = max(0.0, min(1.0, followers_sim))

    # Duração da faixa
    da = _safe_float(meta_a.get("duration_ms", 0.0))
    db = _safe_float(meta_b.get("duration_ms", 0.0))
    maxd = max(1.0, globals_.get("max_duration_diff", 1.0))
    duration_sim = 1.0 - (abs(da - db) / maxd)
    duration_sim = max(0.0, min(1.0, duration_sim))

    # Recência (ano do álbum)
    ya = meta_a.get("album_year")
    yb = meta_b.get("album_year")
    if ya is None or yb is None:
        recency_sim = 0.5
    else:
        maxy = max(1.0, globals_.get("max_year_diff", 1.0))
        recency_sim = 1.0 - (abs(ya - yb) / maxy)
        recency_sim = max(0.0, min(1.0, recency_sim))

    # Explícito
    e_a = bool(meta_a.get("explicit", False))
    e_b = bool(meta_b.get("explicit", False))
    explicit_sim = 1.0 if e_a == e_b else 0.7

    comps = {
        "genre": genre_sim,
        "same_artist": same_artist,
        "same_album": same_album,
        "track_pop": track_pop_sim,
        "artist_pop": artist_pop_sim,
        "followers": followers_sim,
        "duration": duration_sim,
        "recency": recency_sim,
        "explicit": explicit_sim,
    }

    num = sum(weights[k] * comps[k] for k in comps)
    den = sum(weights.values())
    S = num / den if den != 0 else 0.0
    S = max(0.0, min(1.0, S))

    return S, comps

def build_edges_from_spotify(
    spotify_filtered_csv: str | Path = "data/spotify_filtered.csv",
    out_edges_csv: str | Path = "data/parte2_adjacencias.csv",
    node_col: str = "track_name",
    genres_col: str = "genres_list",
    verbose: bool = True,
    negative_shift: float = 0.0,
    negative_fraction: float = 0.0,
    make_negative_cycle: bool = False,
    negative_cycle_size: int = 3,
    cycle_edge_weight: float = -0.5,
    random_seed: int = 42,
    persist_negative: bool = False
):
    spotify_p = Path(spotify_filtered_csv)
  
    if not spotify_p.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {spotify_p}")

    df = pd.read_csv(spotify_p, dtype=str, encoding="utf-8-sig", keep_default_na=False)

    # Filtrar pelas músicas de Ariana Grande, apenas
    df = df[df["artist_name"].str.strip().str.lower() == "ariana grande"]

    if node_col not in df.columns:
        raise KeyError(f"Coluna de nó '{node_col}' não encontrada no CSV.")
    if genres_col not in df.columns:
        raise KeyError(f"Coluna de gêneros '{genres_col}' não encontrada no CSV.")

    tracks = []

    for _, r in df.iterrows():
        track = str(r[node_col]).strip()
        raw_genres = r.get(genres_col)
        genres = _parse_list_string(raw_genres)

        if not genres:
            continue

        tracks.append((track, genres))

    genre_map: Dict[str, list] = {}

    for track, genres in tracks:
        for g in genres:
            genre_map.setdefault(g, []).append(track)

    if verbose:
        total_tracks = len(tracks)
        total_genres = len(genre_map)
        print(f"[build_edges] tracks com gênero: {total_tracks}")
        print(f"[build_edges] gêneros distintos: {total_genres}")

    edge_map: Dict[Tuple[str, str], Set[str]] = {}

    for g, tlist in genre_map.items():
        n = len(tlist)

        if n < 2:
            continue

        for a, b in combinations(tlist, 2):
            if a == b:
                continue

            key = (a, b) if a <= b else (b, a)

            if key not in edge_map:
                edge_map[key] = set()

            edge_map[key].add(g)

    track_meta: Dict[str, dict] = {}
    all_followers = []
    all_durations = []
    all_years = []

    for _, r in df.iterrows():
        track = str(r.get(node_col, "")).strip()

        if not track:
            continue

        genres = _parse_list_string(r.get(genres_col))
        tp = _safe_int(r.get("track_popularity", 0))
        ap = _safe_int(r.get("artist_popularity", 0))
        af = _safe_float(r.get("artist_followers", 0.0))
        dur = _safe_int(r.get("track_duration_ms", 0))
        year = _year_from_date(r.get("album_release_date", ""))
        artist_name = str(r.get("artist_name") or "").strip()
        album_id = str(r.get("album_id") or "").strip()
        explicit_flag = False
        vexp = r.get("explicit", False)

        if isinstance(vexp, str):
            explicit_flag = vexp.strip().lower() in ("true", "1", "yes", "y", "t")
        else:
            explicit_flag = bool(vexp)

        track_meta[track] = {
            "genres": genres,
            "track_popularity": tp,
            "artist_popularity": ap,
            "artist_followers": af,
            "duration_ms": dur,
            "album_year": year,
            "artist_name": artist_name,
            "album_id": album_id,
            "explicit": explicit_flag
        }
        all_followers.append(af)
        all_durations.append(dur)

        if year:
            all_years.append(year)

    globals_ = {
        "max_followers": max(all_followers) if all_followers else 1,
        "max_duration_diff": (max(all_durations) - min(all_durations)) if all_durations else 1,
        "max_year_diff": (max(all_years) - min(all_years)) if all_years else 1
    }

    edge_weights: Dict[Tuple[str, str], dict] = {}

    for (a, b), genres_set in edge_map.items():
        common = sorted(genres_set)
        n_common = len(common)
        meta_a = track_meta.get(a, {})
        meta_b = track_meta.get(b, {})

        S, comps = compute_similarity(meta_a, meta_b, globals_)
        peso = 1.0 - S

        edge_weights[(a, b)] = {
            "common_genres": ";".join(common),
            "n_common": n_common,
            "sim": S,
            "peso": float(peso),
            "comps": comps
        }

    random.seed(random_seed)

    if persist_negative and negative_shift > 0.0 and negative_fraction > 0.0 and len(edge_weights) > 0:
        k = max(1, int(len(edge_weights) * float(negative_fraction)))
        keys = list(edge_weights.keys())
        chosen = random.sample(keys, k)

        if verbose:
            print(f"[build_edges] aplicando negative_shift={negative_shift} em {len(chosen)} arestas ({negative_fraction*100:.2f}%)")

        for key in chosen:
            edge_weights[key]["peso"] = edge_weights[key]["peso"] - float(negative_shift)

    if persist_negative and make_negative_cycle:
        available_tracks = list(track_meta.keys())

        if len(available_tracks) < negative_cycle_size:
            raise ValueError("Não há tracks suficientes para construir ciclo negativo do tamanho solicitado.")
        
        cycle_nodes = random.sample(available_tracks, negative_cycle_size)

        if verbose:
            print(f"[build_edges] criando ciclo negativo com nodes: {cycle_nodes} e peso por aresta {cycle_edge_weight}")
        
        for i in range(len(cycle_nodes)):
            a = cycle_nodes[i]
            b = cycle_nodes[(i + 1) % len(cycle_nodes)]
            key = (a, b) if a <= b else (b, a)

            if key in edge_weights:
                edge_weights[key]["peso"] = float(cycle_edge_weight)
                edge_weights[key]["common_genres"] = edge_weights[key].get("common_genres", "")
                edge_weights[key]["n_common"] = edge_weights[key].get("n_common", 0)
                edge_weights[key]["sim"] = edge_weights[key].get("sim", 0.0)
            else:
                edge_weights[key] = {
                    "common_genres": "",
                    "n_common": 0,
                    "sim": 0.0,
                    "peso": float(cycle_edge_weight),
                    "comps": {}
                }

    rows = []
    epsilon = 1e-6
    allow_negative = persist_negative

    for (a, b), info in edge_weights.items():
        peso = float(info["peso"])

        if not allow_negative and peso < epsilon:
            peso = epsilon
        
        rows.append({
            "track_a": a,
            "track_b": b,
            "common_genres": info.get("common_genres", ""),
            "n_common": info.get("n_common", 0),
            "peso": round(float(peso), 6),
            "sim": round(float(info.get("sim", 0.0)), 6)
        })

    out_df = pd.DataFrame(rows, columns=["track_a", "track_b", "common_genres", "n_common", "peso", "sim"])
    out_path = Path(out_edges_csv)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(out_path, index=False, encoding="utf-8-sig")

    if verbose:
        print(f"[build_edges] arestas únicas geradas: {len(out_df)}")
        print(f"[build_edges] arquivo salvo em: {out_path.resolve()}")
        if persist_negative and negative_shift > 0.0 and negative_fraction > 0.0:
            print(f"[build_edges] (atenção) pesos negativos foram gerados para {negative_fraction*100:.2f}% das arestas.")
        if persist_negative and make_negative_cycle:
            print(f"[build_edges] (atenção) ciclo negativo criado (tamanho {negative_cycle_size}).")

    return out_df
