from pathlib import Path

import pandas as pd


def read_station_file(cfg):
    stations_path = Path(cfg.paths.project_root) / cfg.paths.data.stations / 'stations_data.csv'
    df_stations = pd.read_csv(stations_path, index_col=0, usecols=[
        'CODE', 'ESTACION', 'LON', 'LAT', 'ALT'
    ])

    return df_stations

