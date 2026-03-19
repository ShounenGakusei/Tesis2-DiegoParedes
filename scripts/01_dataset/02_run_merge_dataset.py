
import logging
from pathlib import Path

import pandas as pd

from dlgoes.utils.seed import set_seed
from dlgoes.data.precipitation.io import read_precipitation_dataset
from dlgoes.data.stations.io import read_station_file
from dlgoes.data.stations.threshold import get_umbrales_resumen, join_stations_thresholds
from dlgoes.utils.config import check_create_dir, find_repo_root, load_config_ns
from dlgoes.utils.logging import setup_logging
from dlgoes.data.precipitation.flag import simulate_qc_flags

logger = logging.getLogger(__name__)


def main():
    # Configuracion Inicial
    repo_root = find_repo_root(Path.cwd())
    cfg = load_config_ns(repo_root / 'configs' / 'base.yaml')
    set_seed(cfg.seed)
    
    log_file = repo_root / cfg.paths.outputs.logs / "build_stations.log"
    setup_logging(log_file=log_file, level=cfg.logging.level)
    logger.info("Starting build_stations_dataset")
    logger.debug(f"Repo root: {repo_root}")

    logger.debug("Reading precipitation dataset")
    df_pre = read_precipitation_dataset(cfg)
    
    logger.debug("Reading station dataset")
    df_stations = read_station_file(cfg)

    logger.debug("Generating threshold station dataset")
    df_ths = join_stations_thresholds(cfg)
    umbrales, noMayor, errors = get_umbrales_resumen(cfg)

    logger.debug("Merging all data in one file")
    df_st = pd.concat([df_stations, df_ths], axis=1)
    df_pre['FLAG_V2'] = df_pre.apply(lambda x: simulate_qc_flags(x, umbrales),axis=1)
    df_final = df_pre.merge(df_st, on='CODE')

    logger.debug("Saving final dataset with precipitation y station data")
    processed_path = Path(cfg.paths.project_root) / cfg.paths.data.interim 
    check_create_dir(processed_path)
    df_final.to_csv(processed_path / 'merged_data.csv',index=False)

    logger.info("End build_stations_dataset")

if __name__ == "__main__":
    main()
    







