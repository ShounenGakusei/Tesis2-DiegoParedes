import pandas as pd
from sklearn.model_selection import train_test_split

def add_group_id_station_day(df: pd.DataFrame, fix_hour: int = 10) -> pd.DataFrame:
    df = df.sort_values(["CODE", "_FECHA_HORA"]).copy()
    if not pd.api.types.is_datetime64_any_dtype(df["_FECHA_HORA"]):
        df["_FECHA_HORA"] = pd.to_datetime(df["_FECHA_HORA"])

    day_group = (df["_FECHA_HORA"] - pd.Timedelta(hours=fix_hour)).dt.floor("D")
    df["_day_group"] = day_group
    df["_group_id"] = df["CODE"].astype(str) + "-" + day_group.dt.strftime("%Y%m%d")
    return df


def build_group_table(df: pd.DataFrame, target_col: str) -> pd.DataFrame:
    g = (df.groupby("_group_id")
           .agg(
               CODE=("CODE", "first"),
               start=("_FECHA_HORA", "min"),
               n_rows=("_group_id", "size"),
               n_bad=(target_col, "sum"),
               group_y=(target_col, "max"),  # 1 si hubo al menos un "malo" en el grupo
           )
           .reset_index()
        )
    return g


def stratified_take(groups_df: pd.DataFrame, take_frac: float, seed: int = 42):
    """
    Toma 'take_frac' de groups_df para 'take' (estratificado por group_y) y devuelve:
    - take_groups (df de grupos)
    - rest_groups (df de grupos)
    """
    if take_frac <= 0:
        return groups_df.iloc[0:0].copy(), groups_df.copy()
    if take_frac >= 1:
        return groups_df.copy(), groups_df.iloc[0:0].copy()

    y = groups_df["group_y"].values
    can_stratify = (pd.Series(y).nunique() == 2) and (pd.Series(y).value_counts().min() >= 2)

    strat = y if can_stratify else None

    take_g, rest_g = train_test_split(
        groups_df,
        train_size=take_frac,
        random_state=seed,
        shuffle=True,
        stratify=strat
    )
    return take_g.copy(), rest_g.copy()


def split_dataset(clean_cfg, df: pd.DataFrame, fix_hour: int = 10, seed: int | None = None):
    """
    clean_cfg.splits: algo como {train:0.7, val:0.1, test:0.2}
    Retorna dict con dataframes: {'train':..., 'val':..., 'test':...}
    """
    seed = seed if seed is not None else getattr(clean_cfg, "seed", 42)

    df = add_group_id_station_day(df, fix_hour=fix_hour)
    group_tbl = build_group_table(df, clean_cfg.target.name)

    # obtén splits en orden
    split_items = list(vars(clean_cfg.splits).items())  # o clean_cfg.splits.__dict__ si es dataclass
    # filtra los que tienen ratio>0
    split_items = [(n, r) for n, r in split_items if r and r > 0]

    if not split_items:
        raise ValueError("No hay splits definidos (todos en 0).")

    remaining_groups = group_tbl.copy()
    remaining_ratio = 1.0
    result = {}

    # asigna todos menos el último
    for name, ratio in split_items[:-1]:
        take_frac = ratio / remaining_ratio  # fracción dentro de lo que queda
        take_g, remaining_groups = stratified_take(remaining_groups, take_frac=take_frac, seed=seed)

        take_ids = set(take_g["_group_id"])
        result[name] = df[df["_group_id"].isin(take_ids)].copy()

        remaining_ratio -= ratio

    # el último se queda con lo que resta
    last_name = split_items[-1][0]
    last_ids = set(remaining_groups["_group_id"])
    result[last_name] = df[df["_group_id"].isin(last_ids)].copy()

    # sanity-check anti leakage
    keys = list(result.keys())
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            a = set(result[keys[i]]["_group_id"].unique())
            b = set(result[keys[j]]["_group_id"].unique())
            assert a.isdisjoint(b), f"Leakage: groups repetidos entre {keys[i]} y {keys[j]}"

    # concat con etiqueta de split (evita colisión con 'base' original)
    split_col = "split"  # mejor que "base"
    dfs = []
    for split_name, part_df in result.items():
        part_df = part_df.copy()
        part_df[split_col] = split_name
        dfs.append(part_df)

    final_df = pd.concat(dfs, ignore_index=True)

    return final_df