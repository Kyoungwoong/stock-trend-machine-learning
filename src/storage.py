from __future__ import annotations

from pathlib import Path

import pandas as pd


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def save_parquet(df: pd.DataFrame, path: Path) -> None:
    """Save a dataframe as parquet.

    Parquet requires pyarrow or fastparquet. The project requirements include pyarrow,
    but this fallback keeps the skeleton runnable in minimal environments.
    """
    ensure_parent(path)
    try:
        df.to_parquet(path, index=False)
    except ImportError:
        df.to_pickle(path)


def load_parquet(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    try:
        return pd.read_parquet(path)
    except ImportError:
        return pd.read_pickle(path)


def write_report(path: Path, content: str) -> None:
    ensure_parent(path)
    path.write_text(content, encoding="utf-8")
