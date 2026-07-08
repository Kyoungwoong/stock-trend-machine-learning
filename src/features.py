from __future__ import annotations

import pandas as pd


FEATURE_COLUMNS = [
    "return_1d",
    "return_3d",
    "return_5d",
    "return_20d",
    "ma_5",
    "ma_20",
    "ma_60",
    "close_vs_ma5",
    "close_vs_ma20",
    "close_vs_ma60",
    "volume_change_1d",
    "volume_ma_5",
    "volume_ma_20",
    "volatility_5d",
    "volatility_20d",
    "market_return_1d",
    "market_return_5d",
    "excess_return_5d",
]


def add_price_features(df: pd.DataFrame) -> pd.DataFrame:
    """오늘 장마감 시점까지 알 수 있는 값으로 feature를 만든다.

    현재일 종가를 포함한 rolling feature를 사용한다. 이 프로젝트의 예측 시점은 장마감 후이므로
    현재일 종가/거래량은 사용할 수 있다.
    """
    out = df.sort_values("date").copy()

    out["return_1d"] = out["close"].pct_change(1)
    out["return_3d"] = out["close"].pct_change(3)
    out["return_5d"] = out["close"].pct_change(5)
    out["return_20d"] = out["close"].pct_change(20)

    out["ma_5"] = out["close"].rolling(5).mean()
    out["ma_20"] = out["close"].rolling(20).mean()
    out["ma_60"] = out["close"].rolling(60).mean()

    out["close_vs_ma5"] = out["close"] / out["ma_5"] - 1
    out["close_vs_ma20"] = out["close"] / out["ma_20"] - 1
    out["close_vs_ma60"] = out["close"] / out["ma_60"] - 1

    out["volume_change_1d"] = out["volume"].pct_change(1)
    out["volume_ma_5"] = out["volume"].rolling(5).mean()
    out["volume_ma_20"] = out["volume"].rolling(20).mean()

    out["volatility_5d"] = out["return_1d"].rolling(5).std()
    out["volatility_20d"] = out["return_1d"].rolling(20).std()

    if "index_close" in out.columns:
        out["market_return_1d"] = out["index_close"].pct_change(1)
        out["market_return_5d"] = out["index_close"].pct_change(5)
        out["excess_return_5d"] = out["return_5d"] - out["market_return_5d"]
    else:
        out["market_return_1d"] = pd.NA
        out["market_return_5d"] = pd.NA
        out["excess_return_5d"] = pd.NA

    return out


def get_feature_frame(df: pd.DataFrame) -> pd.DataFrame:
    missing = [col for col in FEATURE_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"Missing feature columns: {missing}")
    return df[FEATURE_COLUMNS].copy()
