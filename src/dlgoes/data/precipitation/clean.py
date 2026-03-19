from __future__ import annotations

from datetime import timedelta
from pathlib import Path
import logging
import time
import pandas as pd

logger = logging.getLogger(__name__)


def comprobar_frames(cfg, df: pd.DataFrame) -> list[pd.Timestamp]:
    """
    Devuelve una lista de horas (Timestamp) para las cuales NO se encontró
    el archivo GOES esperado (YYYY-MM-DD-HH-00.nc) o el archivo es demasiado pequeño.

    Requiere que df tenga columna FECHA_HORA (datetime).
    """
    t0 = time.time()
    # Crear FECHA_HORA (datetime)
    df["_FECHA_HORA"] = pd.to_datetime(
        df["FECHA"].astype(str) + " " + df["HORA"].astype(str),
        format="%d/%m/%Y %H:%M:%S",
        errors="coerce"
    )

    offset_hours = getattr(getattr(cfg, "goes", cfg), "time_offset_hours", 5)
    min_size_bytes = getattr(getattr(cfg, "goes", cfg), "min_image_size", 4_100_000)

    project_root = Path(cfg.paths.project_root)
    path_images = project_root / Path(cfg.goes.goes_data)

    # Validación básica
    if "_FECHA_HORA" not in df.columns:
        raise ValueError("df debe contener la columna FECHA_HORA (datetime).")

    # Reporta inválidos y omítelos
    if df["_FECHA_HORA"].isna().any():
        n_bad = int(df["_FECHA_HORA"].isna().sum())
        logger.warning(f"Se encontraron {n_bad} filas con FECHA_HORA inválida (NaT). Se omiten.")

    # Tomar horas únicas (floor) y sin NaT
    horas = (
        df["_FECHA_HORA"]
        .dropna()
        .dt.floor("h")
        .drop_duplicates()
        .sort_values()
        .to_list()
    )

    faltantes: list[pd.Timestamp] = []

    for hora_dt in horas:
        nueva_hora = hora_dt + timedelta(hours=offset_hours)
        file_path = path_images / f"{nueva_hora.strftime('%Y-%m-%d-%H')}-00.nc"

        try:
            size = file_path.stat().st_size
            if size <= min_size_bytes:
                faltantes.append(hora_dt)
        except FileNotFoundError:
            faltantes.append(hora_dt)
        except Exception:
            logger.exception(f"Error verificando archivo: {file_path}")
            faltantes.append(hora_dt)

    logger.info(
        f"Verificación GOES completada. Horas únicas={len(horas)}, "
        f"faltantes={len(faltantes)}. Tiempo={time.time() - t0:.2f}s"
    )

    df["_MISSING_GOES"] = df["_FECHA_HORA"].dt.floor("h").isin(faltantes).astype(int)
    return df, faltantes

"""
Metodos que permiten en un conjunto de estaciones (dataframe), agrega su posicion XO(longitud), XA(latitud)
"""
# Encuentra las longitudes y latitudes
from netCDF4 import Dataset

def read_lon_lat_goes_image(cfg):    
    try:
        img_file = cfg.paths.project_root /  cfg.goes.goes_test_images / '2021-11-21-01-00.nc'
        goes_data = Dataset(img_file)
    except:
        print("No se pudo leer los archivos de imagen")
        print(img_file)
        return -1,-1

    # obtiene las coordenadas de los pixeles
    lons = goes_data.groups['coordenadas']['longitude'][:].data
    lats = goes_data.groups['coordenadas']['latitude'][:].data
        
    return lons, lats  

#Busca el valor X en el array, devuelve su posicion
def get_pos_map(x,array):    
    pos = -1
    for i in range(len(array)):
        if abs(array[i]-x)<=0.01:
            pos = i
            
    return  pos  

#en el la imagen satelital
def changeOrigenStation(cfg , df):
    df_stats = df[['CODE', 'LON', 'LAT']].drop_duplicates()
    lo,la = read_lon_lat_goes_image(cfg)
    
    print(len(df_stats))
    df_stats['XLO'] = df_stats.apply(lambda x: get_pos_map(float(x['LON']), lo),axis=1)
    df_stats['XLA'] = df_stats.apply(lambda x: get_pos_map(float(x['LAT']), la),axis=1)    
    
    df = df.merge(df_stats[['CODE','XLO', 'XLA']], on='CODE')
    return df


def _as_list(x):
    """Normaliza None/''/scalar/list a lista."""
    if x is None:
        return []
    if isinstance(x, (list, tuple, set)):
        return list(x)
    if isinstance(x, str):
        x = x.strip()
        return [] if x == "" else [x]
    return [x]

def clean_dataset(clean_cfg, df: pd.DataFrame) -> pd.DataFrame:
    conditions = []

    # 1) Precipitación
    conditions.append(
        df["PRECIPITACION"].between(
            clean_cfg.precipitation.min_value,
            clean_cfg.precipitation.max_value,
            inclusive="both",
        )
    )

    # 2) Flags manuales (include/exclude robusto)
    inc = _as_list(clean_cfg.flag.include)
    exc = _as_list(clean_cfg.flag.exclude)
    if inc:
        conditions.append(df["FLAG"].isin(inc))
    if exc:
        conditions.append(~df["FLAG"].isin(exc))

    # 3) Flags automáticos
    inc2 = _as_list(clean_cfg.flag_v2.include)
    exc2 = _as_list(clean_cfg.flag_v2.exclude)
    if inc2:
        conditions.append(df["FLAG_V2"].isin(inc2))
    if exc2:
        conditions.append(~df["FLAG_V2"].isin(exc2))

    # 4) GOES (corrección: no uses isin(0))
    conditions.append(df["_MISSING_GOES"].eq(0))

    # 5) QUitamos datos nulos de estaciones 
    if "ALT" in df.columns:
        conditions.append(df["ALT"].notna())
    

    # 6) Máscara final
    mask = conditions[0]
    for cond in conditions[1:]:
        mask &= cond

    # 7) Marcar validez en el DF original (si te sirve)
    out = df.copy()
    out["valid_data"] = mask

    # 8) Crear df válido si lo necesitas
    df_valid = out.loc[mask].copy()

    # 9) Target (vectorizado, sin apply)
    tgt_src = clean_cfg.target.col
    tgt_dst = clean_cfg.target.name

    if getattr(clean_cfg.target, "good_class", None) is not None:
        good = str(clean_cfg.target.good_class)
        out[tgt_dst] = out[tgt_src].astype(str).eq(good).astype("int8")
        df_valid[tgt_dst] = df_valid[tgt_src].astype(str).eq(good).astype("int8")
    else:
        out[tgt_dst] = pd.to_numeric(out[tgt_src], errors="coerce")
        df_valid[tgt_dst] = pd.to_numeric(df_valid[tgt_src], errors="coerce")

    return out