from src.data.stations.io import read_station_file


def build_station_file(cfg):
    df_st = read_station_file(cfg)
    