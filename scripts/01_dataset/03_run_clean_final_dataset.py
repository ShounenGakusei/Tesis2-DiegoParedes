
import logging
from pathlib import Path

from dlgoes.data.precipitation.clean import changeOrigenStation, clean_dataset, comprobar_frames
from dlgoes.data.precipitation.split import split_dataset
import pandas as pd

from dlgoes.utils.seed import set_seed
from dlgoes.utils.config import check_create_dir, find_repo_root, load_config_ns
from dlgoes.utils.logging import setup_logging

logger = logging.getLogger(__name__)

def log_dataset_summary(logger, df, target_col, split_col="split", group_col="group_id", prefix=""):
    n = len(df)
    logger.info("%sFilas totales: %d", prefix, n)

    if "valid_data" in df.columns:
        valid_rate = df["valid_data"].astype(int).mean()
        logger.info("%sValid_data=1: %.2f%% (%d/%d)", prefix, 100*valid_rate, int(df["valid_data"].sum()), n)

    if "_MISSING_GOES" in df.columns:
        missing = int(df["_MISSING_GOES"].sum()) if df["_MISSING_GOES"].dropna().isin([0,1]).all() else int((df["_MISSING_GOES"] != 0).sum())
        logger.info("%sMissing GOES (flag!=0): %d", prefix, missing)

    if target_col in df.columns:
        bad_rate = df[target_col].mean()
        logger.info("%sBad rate (%s): %.4f (%.2f%%)", prefix, target_col, bad_rate, 100*bad_rate)

    if split_col in df.columns:
        counts = df[split_col].value_counts(dropna=False).to_dict()
        logger.info("%sDistribución por split: %s", prefix, counts)

        if target_col in df.columns:
            bad_by_split = df.groupby(split_col)[target_col].mean().to_dict()
            logger.info("%sBad rate por split: %s", prefix, {k: round(v, 6) for k,v in bad_by_split.items()})

        if group_col in df.columns:
            groups_by_split = df.groupby(split_col)[group_col].nunique().to_dict()
            logger.info("%s#groups únicos por split: %s", prefix, groups_by_split)

def main():
    # Configuracion Inicial
    repo_root = find_repo_root(Path.cwd())
    cfg = load_config_ns(repo_root / 'configs' / 'base.yaml')
    clean_cfg = load_config_ns(repo_root / 'configs' / 'cleaning' /'base.yaml')
    set_seed(cfg.seed)
    
    log_file = repo_root / cfg.paths.outputs.logs / "final_dataset.log"
    setup_logging(log_file=log_file, level=cfg.logging.level)
    logger.info("Starting build final dataset")
    logger.debug(f"Repo root: {repo_root}")

    logger.debug("Reading interim dataset")
    df = pd.read_csv(cfg.paths.project_root / cfg.paths.data.interim/clean_cfg.input_data, index_col=0)

    logger.debug(f"Check for missing goes images")
    df, faltantes = comprobar_frames(cfg, df)

    logger.debug(f"Parsing lon,lat points to X,Y")
    df = changeOrigenStation(cfg, df)

    logger.debug(f"Cleaning and filtering dataset")
    df = clean_dataset(clean_cfg, df)

    valid_data = df[df['valid_data']==True]
    len_valid_data = len(valid_data)

    logger.debug(f"Splitting dataset with {clean_cfg.name}")
    df_final = split_dataset(clean_cfg, valid_data)

    
    log_dataset_summary(
        logger,
        df_final,
        target_col=clean_cfg.target.name,
        split_col="split",
        group_col="_group_id",
        prefix="[FINAL] "
    )


    logger.debug("Saving final dataset for developing models")
    processed_path = Path(cfg.paths.project_root) / cfg.paths.data.processed
    check_create_dir(processed_path)
    df_final.to_csv(processed_path / f'{clean_cfg.name}.csv', index=False)

    logger.info("End build_stations_dataset")

if __name__ == "__main__":
    main()
    







