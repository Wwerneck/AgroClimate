from __future__ import annotations

from pathlib import Path

import pandas as pd


def read_parquet_files(path: Path) -> pd.DataFrame:
    files = sorted(path.rglob("*.parquet")) if path.exists() else []
    frames = [pd.read_parquet(file) for file in files]
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
