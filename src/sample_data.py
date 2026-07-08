from __future__ import annotations

import numpy as np
import pandas as pd


def make_business_dates(start: str, end: str) -> pd.DatetimeIndex:
    """월~금 기준의 단순 영업일 index를 만든다.

    한국 휴장일은 반영하지 않은 샘플용 calendar다. 실제 API 연동 후에는 거래소 calendar 또는
    원천 데이터의 날짜를 기준으로 inner join 하는 방식으로 보정한다.
    """
    return pd.bdate_range(start=start, end=end)


def generate_sample_stock(ticker: str, start: str, end: str, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    dates = make_business_dates(start, end)
    n = len(dates)

    daily_returns = rng.normal(loc=0.00025, scale=0.018, size=n)
    close = 70000 * np.cumprod(1 + daily_returns)
    open_ = close * (1 + rng.normal(0, 0.004, size=n))
    high = np.maximum(open_, close) * (1 + np.abs(rng.normal(0, 0.006, size=n)))
    low = np.minimum(open_, close) * (1 - np.abs(rng.normal(0, 0.006, size=n)))
    volume = rng.integers(8_000_000, 28_000_000, size=n)
    trading_value = close * volume
    shares_outstanding = np.full(n, 5_969_782_550)
    market_cap = close * shares_outstanding

    df = pd.DataFrame(
        {
            "date": dates,
            "ticker": ticker,
            "name": "삼성전자_SAMPLE",
            "market": "KOSPI",
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
            "trading_value": trading_value,
            "shares_outstanding": shares_outstanding,
            "market_cap": market_cap,
        }
    )
    df["change_rate"] = df["close"].pct_change().fillna(0) * 100
    return df.round({"open": 0, "high": 0, "low": 0, "close": 0, "trading_value": 0, "market_cap": 0})


def generate_sample_index(index_name: str, start: str, end: str, seed: int = 7) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    dates = make_business_dates(start, end)
    n = len(dates)

    daily_returns = rng.normal(loc=0.00015, scale=0.012, size=n)
    close = 2500 * np.cumprod(1 + daily_returns)
    open_ = close * (1 + rng.normal(0, 0.003, size=n))
    high = np.maximum(open_, close) * (1 + np.abs(rng.normal(0, 0.004, size=n)))
    low = np.minimum(open_, close) * (1 - np.abs(rng.normal(0, 0.004, size=n)))
    volume = rng.integers(300_000_000, 900_000_000, size=n)

    df = pd.DataFrame(
        {
            "date": dates,
            "index_name": index_name,
            "index_open": open_,
            "index_high": high,
            "index_low": low,
            "index_close": close,
            "index_volume": volume,
        }
    )
    df["index_change_rate"] = df["index_close"].pct_change().fillna(0) * 100
    return df.round({"index_open": 2, "index_high": 2, "index_low": 2, "index_close": 2})
