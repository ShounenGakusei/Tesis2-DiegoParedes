import logging
from pathlib import Path

def setup_logging(log_file: str | Path, level: str = "INFO"):
    # 1) Root en INFO para evitar ruido de terceros
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[
            logging.FileHandler(str(log_file), encoding="utf-8"),
            logging.StreamHandler(),
        ],
        force=True,  # importante si algo ya configuró logging antes
    )

    # 2) Tu paquete: respeta el level del cfg (DEBUG/INFO/...)
    lvl = getattr(logging, str(level).upper(), logging.INFO)
    logging.getLogger("dlgoes").setLevel(lvl)

    # 3) Tu script/entrypoint también (para que logger.debug en __main__ salga)
    logging.getLogger("__main__").setLevel(lvl)

    # 4) (Opcional) bajar ruido de loggers específicos
    for noisy in [
        "tensorflow",
        "absl",
        "matplotlib",
        "PIL",
        "numexpr",
        "h5py",
        "urllib3",
    ]:
        logging.getLogger(noisy).setLevel(logging.WARNING)