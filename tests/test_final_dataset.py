from dlgoes.utils.config import load_config_ns
import pandas as pd
from pandas.api.types import is_numeric_dtype
# tests/test_sanity_pipeline.py
from pathlib import Path
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]  # sube de tests/ a root/

def test_final_dataset_clean():
    clean_cfg = load_config_ns(REPO_ROOT / 'configs' / 'cleaning' /'base.yaml')
    path = REPO_ROOT / "data" / "processed" / f"{clean_cfg.name}.csv"

    
    assert path.exists(), f"No existe el archivo: {path}"
    df_final = pd.read_csv(path)
    assert not df_final.empty, "Final dataset is empty"

    # --- columnas requeridas ---
    required = {"_MISSING_GOES", "XLO", "XLA", "valid_data", "split"}
    missing = required - set(df_final.columns)
    assert not missing, f"Faltan columnas: {missing}"

    # --- valid_data debe ser todo True/1 si este DF ya es el filtrado final ---
    assert df_final["valid_data"].isin([0, 1, True, False]).all(), "valid_data tiene valores raros"
    assert df_final["valid_data"].astype(int).eq(1).all(), "No todos los registros son válidos (valid_data != 1)"

    # --- GOES: no deben existir faltantes ---
    # si MISSING_GOES=1 significa falta, entonces debe ser todo 0
    assert df_final["_MISSING_GOES"].isin([0, 1]).all(), "MISSING_GOES tiene valores fuera de {0,1}"
    assert df_final["_MISSING_GOES"].eq(0).all(), "Existen datos con missings GOES (MISSING_GOES != 0)"

    # --- XLO/XLA numéricos ---
    assert is_numeric_dtype(df_final["XLO"]), "XLO no es numérico"
    assert is_numeric_dtype(df_final["XLA"]), "XLA no es numérico"

    # si pueden venir como string, fuerza conversión y valida que no se rompa:
    xlo = pd.to_numeric(df_final["XLO"], errors="coerce")
    xla = pd.to_numeric(df_final["XLA"], errors="coerce")
    assert xlo.notna().all(), "XLO tiene valores no convertibles a número"
    assert xla.notna().all(), "XLA tiene valores no convertibles a número"

    # --- no negativos (según tu lógica) ---
    assert (xlo >= 0).all(), "Hay valores negativos en LongitudX (XLO < 0)"
    assert (xla >= 0).all(), "Hay valores negativos en LatitudX (XLA < 0)"

    # --- split debe contener train y test (y opcionalmente val) ---
    allowed = {"train", "test", "holdout"}
    assert df_final["split"].isin(allowed).all(), f"split tiene valores fuera de {allowed}"

    splits_present = set(df_final["split"].unique())
    assert {"train", "test"}.issubset(splits_present), f"No existe train y test. Presentes: {splits_present}"