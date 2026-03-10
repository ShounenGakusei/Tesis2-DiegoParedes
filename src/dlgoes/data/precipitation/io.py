import os
from pathlib import Path

import pandas as pd


def read_precipitation_dataset(cfg):
    dir_files = Path(cfg.paths.project_root) / cfg.paths.data.raw
    lista_files = [x for x in os.listdir(dir_files) if ('.csv' in x) and ('REPORTE' in x)]
    dfs_data = []
    for file in lista_files:
        df = pd.read_csv(Path(cfg.paths.project_root) / cfg.paths.data.raw / file, encoding='latin-1')
        dfs_data.append(df)

    # Unimos los dos años de precipitaciones en un solo DataFrame
    dfPrecipitacion = pd.concat(dfs_data, ignore_index=True) 
    dfPrecipitacion['CODIGO'] = 'X' + (dfPrecipitacion['CODIGO']).astype(str)
    dfPrecipitacion.rename(columns={'CODIGO': 'CODE'}, inplace=True)
    return dfPrecipitacion

