from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
OUT_DIR = BASE_DIR / "out"

ADJACENCIAS_CSV = DATA_DIR / "adjacencias_bairros.csv"
BAIRROS_UNIQUE_CSV = DATA_DIR / "bairros_unique.csv"

API_HOST = "127.0.0.1"
API_PORT = 3000
