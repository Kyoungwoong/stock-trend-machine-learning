from __future__ import annotations

import pandas as pd


LABEL_COLUMN = "label_up_5d"
FUTURE_RETURN_COLUMN = "future_return_5d"


def add_forward_return_label(df: pd.DataFrame, horizon: int = 5) -> pd.DataFrame:
    """향후 horizon 영업일 수익률과 상승 여부 label을 만든다.

    future_return은 평가/백테스트에는 사용할 수 있지만 모델 feature로 쓰면 안 된다.
    """
    out = df.sort_values("date").copy()
    out[FUTURE_RETURN_COLUMN] = out["close"].shift(-horizon) / out["close"] - 1
    out[LABEL_COLUMN] = (out[FUTURE_RETURN_COLUMN] > 0).astype("Int64")
    out.loc[out[FUTURE_RETURN_COLUMN].isna(), LABEL_COLUMN] = pd.NA
    return out


def drop_unlabeled_rows(df: pd.DataFrame) -> pd.DataFrame:
    return df.dropna(subset=[LABEL_COLUMN]).copy()
