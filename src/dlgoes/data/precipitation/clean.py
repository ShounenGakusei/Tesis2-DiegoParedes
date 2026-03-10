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
    df["FECHA_HORA"] = pd.to_datetime(
        df["FECHA"].astype(str) + " " + df["HORA"].astype(str),
        format="%d/%m/%Y %H:%M:%S",
        errors="coerce"
    )



    offset_hours = getattr(getattr(cfg, "goes", cfg), "time_offset_hours", 5)
    min_size_bytes = getattr(getattr(cfg, "goes", cfg), "min_image_size", 4_100_000)

    project_root = Path(cfg.paths.project_root)
    path_images = project_root / Path(cfg.goes.goes_data)

    # Validación básica
    if "FECHA_HORA" not in df.columns:
        raise ValueError("df debe contener la columna FECHA_HORA (datetime).")

    # Reporta inválidos y omítelos
    if df["FECHA_HORA"].isna().any():
        n_bad = int(df["FECHA_HORA"].isna().sum())
        logger.warning(f"Se encontraron {n_bad} filas con FECHA_HORA inválida (NaT). Se omiten.")

    # Tomar horas únicas (floor) y sin NaT
    horas = (
        df["FECHA_HORA"]
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

    df["MISSING_GOES"] = df["FECHA_HORA"].dt.floor("h").isin(faltantes).astype(int)
    return faltantes

