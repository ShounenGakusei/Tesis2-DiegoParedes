# src/satprecip/utils/config.py
from pathlib import Path
from typing import Any, Dict
import yaml

def load_yaml(path: str | Path) -> Dict[str, Any]:
    path = Path(path)
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def deep_update(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Merge override into base recursively."""
    out = dict(base)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = deep_update(out[k], v)
        else:
            out[k] = v
    return out

def load_config(base_path: str | Path, exp_path: str | Path | None = None) -> Dict[str, Any]:
    base = load_yaml(base_path)
    if exp_path is None:
        return base
    exp = load_yaml(exp_path)
    return deep_update(base, exp)   

# src/satprecip/utils/config.py
from types import SimpleNamespace
from pathlib import Path
import yaml

def _to_ns(x):
    if isinstance(x, dict):
        return SimpleNamespace(**{k: _to_ns(v) for k, v in x.items()})
    if isinstance(x, list):
        return [_to_ns(v) for v in x]
    return x

from pathlib import Path

def find_repo_root(start: Path | None = None) -> Path:
    start = start or Path(__file__).resolve()
    for p in [start, *start.parents]:
        if (p / "pyproject.toml").exists() or (p / "README.md").exists():
            return p
    raise RuntimeError("Repo root not found (pyproject.toml or README.md).")

def load_config_ns(path: str | Path):
    with open(path, "r", encoding="utf-8") as f:
        d = yaml.safe_load(f)
    if ('base' in path.name) and 'paths' in list(d.keys()):
        d['paths']['project_root'] = find_repo_root()
    return _to_ns(d)


def check_create_dir(path: str | Path):
    path = Path(path)
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)