from __future__ import annotations

import os 

import pandas as pd
import plotly.express as px

from dlgoes.data.precipitation.flag import simulate_qc_flags
from dlgoes.data.precipitation.io import read_precipitation_dataset
from dlgoes.data.stations.threshold import get_umbrales_resumen, join_stations_thresholds
from dlgoes.utils.config import check_create_dir


import time
from pathlib import Path
import pandas as pd

import logging
logger = logging.getLogger(__name__)


def clean_station_dataset(cfg):
    # Analize stations thresholds and save the describe in a csv file
    df_ths = join_stations_thresholds(cfg)
    path_output = Path(cfg.paths.project_root) / cfg.paths.outputs.root / 'eda' /  'stations_thresholds_describe.csv'
    check_create_dir(path_output)
    df_ths.describe().to_csv(path_output)

    # Join the final dataset of stations with thresholds and metada and save it as csv file
    stations_path = Path(cfg.paths.project_root) / cfg.paths.data.stations / 'stations_data.csv'
    df_stations = pd.read_csv(stations_path, index_col=0, usecols=[
        'CODE', 'ESTACION', 'LON', 'LAT', 'ALT'
    ])
    df = pd.concat([df_stations, df_ths], axis=1)

    # Plot stations and Thresholds in a map and save it as html file
    fig = px.scatter_mapbox(df, lat="LAT", lon="LON", hover_data=['ESTACION'],                            
                            color = 'THS_2',
                            zoom=5, height=400)
    fig.update_layout(
    mapbox_style="open-street-map")

    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    figure_path = Path(cfg.paths.project_root) / cfg.paths.outputs.root / 'eda' / 'stations_map.html'
    check_create_dir(figure_path)
    fig.write_html(figure_path)


    # Save the final dataset with thresholds and metadata as csv file
    processed_path = Path(cfg.paths.project_root) / cfg.paths.data.processed / 'stations_data.csv'
    check_create_dir(processed_path)
    df.to_csv(processed_path)

    

def merge_precipiation_stations_data(cfg):
    # Precipitation dataset
    df_pre = read_precipitation_dataset(cfg)
    
    # Stations Dataset
    processed_path = Path(cfg.paths.project_root) / cfg.paths.data.processed / 'stations_data.csv'
    df_sts = pd.read_csv(processed_path)

    # Flag V2 Dataset
    umbrales, noMayor, errors = get_umbrales_resumen(cfg)
    df_pre['FLAGV2'] = df_pre.apply(lambda x: simulate_qc_flags(x, umbrales),axis=1)

    


