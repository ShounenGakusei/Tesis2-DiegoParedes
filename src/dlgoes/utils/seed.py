# utils/seed.py
import os, random
import numpy as np
#import tensorflow as tf

_GLOBAL_SEED = None

def set_seed(seed: int):
    global _GLOBAL_SEED
    _GLOBAL_SEED = int(seed)

    random.seed(seed)
    np.random.seed(seed)
    #tf.random.set_seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)

def get_seed(default: int = 42) -> int:
    return _GLOBAL_SEED if _GLOBAL_SEED is not None else default
