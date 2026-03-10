import os
import time
import pandas as pd
from pathlib import Path

import logging
logger = logging.getLogger(__name__)

MONTHS = {
    0: "ENERO", 1: "FEBRERO", 2: "MARZO", 3: "ABRIL",
    4: "MAYO", 5: "JUNIO", 6: "JULIO", 7: "AGOSTO",
    8: "SETIEMBRE", 9: "OCTUBRE", 10: "NOVIEMBRE", 11: "DICIEMBRE"
}

REQUIRED_COLS = {
    "IDESTACION", "DETALLEPERIODO", "DETHORA", "VALORMAXIMO1", "VALORMAXIMO2"
}



def join_stations_thresholds(cfg):
    # Read thresholds data from CSV files in the thresholds directory and create a DataFrame
    dir_ths = Path(cfg.paths.project_root) /  cfg.paths.data.thresholds
    dfUmbrales = {'CODE':[],'THS_1':[], 'THS_2':[], 'MIN_1' :[], 'MIN_2':[]}
    FUmbrales = os.listdir(dir_ths)

    for fileU in FUmbrales:
        tempUmb = pd.read_csv(Path(dir_ths) / fileU, sep=';', encoding='latin-1')
        code = str(tempUmb['IDESTACION'][0])
        if code == 'inf':
            code = fileU.split('-')[1].split('.')[0]

        dfUmbrales['CODE'].append('X' + code)
        dfUmbrales['MIN_1'].append(tempUmb['VALORMINIMO1'].max())
        dfUmbrales['MIN_2'].append(tempUmb['VALORMINIMO2'].max())  
        dfUmbrales['THS_1'].append(tempUmb['VALORMAXIMO1'].max())
        dfUmbrales['THS_2'].append(tempUmb['VALORMAXIMO2'].max())  
        
    df_ths = pd.DataFrame(dfUmbrales)
    df_ths.set_index('CODE', inplace=True)
    return df_ths

def get_umbrales_resumen(cfg, verb: int = 20):
    """
    Lee archivos de umbrales por estación y devuelve:
      - umbrales: dict[codigo] -> [12][24][2] (valmax1, valmax2)
      - noMayor: lista de casos donde valmax2 < valmax1
      - errors: lista de casos donde no coincide (mes/hora) o faltan filas/estructura
    """
    dir_umbrales = Path(cfg.paths.project_root) / cfg.paths.data.thresholds
    if not Path(dir_umbrales).exists():
        raise FileNotFoundError(f"No existe el directorio: {dir_umbrales}")

    files = sorted([p for p in dir_umbrales.iterdir() if p.is_file()])
    total = len(files)

    umbrales: dict[str, list] = {}
    errors: list[str] = []
    noMayor: list[str] = []

    start_time = time.time()
    logger.debug(f"Se procesarán {total} archivos de umbrales desde: {dir_umbrales}")

    processed = 0
    for fpath in files:
        if processed % max(1, verb) == 0:
            elapsed = time.time() - start_time
            pct = (processed / total * 100) if total else 100.0
            logger.debug(f"Progreso: {pct:.2f}% ({processed}/{total}) | {elapsed:.2f}s")

        # 1) Leer archivo robustamente
        try:
            dfUmb = pd.read_csv(fpath, sep=";", encoding="utf-8", engine="python")
        except UnicodeDecodeError:
            # a veces vienen en latin-1
            dfUmb = pd.read_csv(fpath, sep=";", encoding="latin-1", engine="python")
        except Exception:
            logger.exception(f"Error leyendo archivo: {fpath.name}")
            errors.append(f"{fpath.name}-READ_ERROR")
            processed += 1
            continue

        # 2) Validar columnas
        missing_cols = REQUIRED_COLS - set(dfUmb.columns)
        if missing_cols:
            logger.warning(f"Archivo {fpath.name} sin columnas requeridas: {sorted(missing_cols)}")
            errors.append(f"{fpath.name}-MISSING_COLS")
            processed += 1
            continue

        if dfUmb.empty:
            logger.warning(f"Archivo vacío: {fpath.name}")
            errors.append(f"{fpath.name}-EMPTY")
            processed += 1
            continue

        # 3) Código estación
        codigo = 'X' + str(dfUmb["IDESTACION"].iloc[0])

        # Inicializa matriz 12x24x2 con -1
        umbrales[codigo] = [[[-1, -1] for _ in range(24)] for _ in range(12)]

        # 4) Recorrer filas (idealmente deberían ser 288 = 12*24)
        n = 0
        for i in dfUmb.index:
            month = MONTHS[int(n / 24)]
            hour = f"{int(n % 24)}:00:00"

            try:
                if month == dfUmb.at[i, "DETALLEPERIODO"] and hour == dfUmb.at[i, "DETHORA"]:
                    v1 = dfUmb.at[i, "VALORMAXIMO1"]
                    v2 = dfUmb.at[i, "VALORMAXIMO2"]

                    umbrales[codigo][int(n / 24)][int(n % 24)][0] = v1
                    umbrales[codigo][int(n / 24)][int(n % 24)][1] = v2

                    if pd.notna(v1) and pd.notna(v2) and v2 < v1:
                        noMayor.append(f"{codigo}-{i}")
                else:
                    errors.append(f"{codigo}-{i}")
            except Exception:
                logger.exception(f"Error procesando fila {i} en {fpath.name}")
                errors.append(f"{codigo}-{i}-ROW_ERROR")

            n += 1

        # 5) Si no tiene 288 filas, registra warning (no necesariamente falla)
        if n != 288:
            logger.warning(f"{fpath.name} ({codigo}) tiene {n} filas, se esperaban 288 (12*24).")

        processed += 1

    elapsed_total = time.time() - start_time
    logger.info(f"Tiempo total: {elapsed_total:.2f}s")
    logger.info(f"valmax1 > valmax2: {len(noMayor)} casos")
    logger.info(f"inconsistencias mes/hora: {len(errors)} casos")

    return umbrales, noMayor, errors
