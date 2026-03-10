
import logging
from pathlib import Path

import pandas as pd

from dlgoes.utils.seed import set_seed
from dlgoes.data.goes.download import GOESImageProcessor
from dlgoes.utils.config import find_repo_root, load_config_ns
from dlgoes.utils.logging import setup_logging

logger = logging.getLogger(__name__)


def main():
    # Configuracion Inicial
    repo_root = find_repo_root(Path.cwd())
    cfg = load_config_ns(repo_root / 'configs' / 'base.yaml')
    set_seed(cfg.seed)
    
    
    log_file = repo_root / cfg.paths.outputs.logs / "dwnload_goes.log"
    setup_logging(log_file=log_file, level=cfg.logging.level)
    logger.info("Starting downloading goes images")

    start = cfg.goes.start
    end = cfg.goes.end
    dates = pd.date_range(start=start, end=end, freq="h")

    descargados = 0
    validos = 0

    for d in dates:
        descargados+=1
        fecha = d.strftime("%Y-%m-%d-%H-%M")
        GoesClass = GOESImageProcessor(cfg)
        path_goes_file = GoesClass.download_image_goes(fecha)
        if path_goes_file == '':
            logger.warning(f'No se pudo descargar fecha: {fecha}')
        validos+=1

    logger.info("End downloading goes images")
    logger.info(f"Total : {descargados} - Validos : {validos}")

if __name__ == "__main__":
    main()
    







