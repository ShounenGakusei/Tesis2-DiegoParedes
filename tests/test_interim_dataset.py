# tests/test_sanity_pipeline.py
from pathlib import Path
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]  # sube de tests/ a root/

def test_final_dataset_not_empty():
    path = REPO_ROOT / "data" / "interim" / "merged_data.csv"
    assert path.exists(), f"No existe el archivo: {path}"
    df = pd.read_csv(path)
    assert not df.empty, "Final dataset is empty"

def test_required_columns_exist():
    path = REPO_ROOT / "data" / "interim" / "merged_data.csv"
    df = pd.read_csv(path)
    required = {"CODE", "PRECIPITACION", "FLAG", "FLAG_V2"}
    assert required.issubset(df.columns), f"Faltan columnas: {required - set(df.columns)}"