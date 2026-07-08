from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import pandas as pd
import requests


@dataclass(frozen=True)
class FscIndexApiClient:
    """공공데이터포털 금융위원회_지수시세정보 API client.

    Endpoint:
    https://apis.data.go.kr/1160100/service/GetMarketIndexInfoService/getStockMarketIndex
    """

    service_key: str
    base_url: str = "https://apis.data.go.kr/1160100/service/GetMarketIndexInfoService/getStockMarketIndex"
    sleep_seconds: float = 0.15

    def fetch_by_date(self, bas_dt: str, index_name: str = "코스피", num_rows: int = 1000) -> pd.DataFrame:
        params: dict[str, Any] = {
            "serviceKey": self.service_key,
            "resultType": "json",
            "numOfRows": num_rows,
            "pageNo": 1,
            "basDt": bas_dt.replace("-", ""),
            "idxNm": index_name,
        }
        response = requests.get(self.base_url, params=params, timeout=30)
        response.raise_for_status()
        payload = response.json()
        items = _extract_items(payload)
        time.sleep(self.sleep_seconds)
        return normalize_index_items(items)

    def fetch_range(self, start: str, end: str, index_name: str = "코스피") -> pd.DataFrame:
        dates = pd.bdate_range(start=start, end=end)
        frames: list[pd.DataFrame] = []
        for dt in dates:
            try:
                df = self.fetch_by_date(dt.strftime("%Y%m%d"), index_name=index_name)
            except Exception as exc:  # noqa: BLE001
                print(f"[WARN] index fetch failed: {dt.date()} {exc}")
                continue
            if not df.empty:
                frames.append(df)
        if not frames:
            raise RuntimeError("No index data fetched. Check API key, date range, and index name.")
        return pd.concat(frames, ignore_index=True).drop_duplicates(["date", "index_name"])


def _extract_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    body = payload.get("response", {}).get("body", {})
    items = body.get("items", {}).get("item", [])
    if isinstance(items, dict):
        return [items]
    return items or []


def _to_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series.astype(str).str.replace(",", "", regex=False), errors="coerce")


def normalize_index_items(items: list[dict[str, Any]]) -> pd.DataFrame:
    if not items:
        return pd.DataFrame()

    df = pd.DataFrame(items)
    rename_map = {
        "basDt": "date",
        "idxNm": "index_name",
        "clpr": "index_close",
        "vs": "index_change",
        "fltRt": "index_change_rate",
        "mkp": "index_open",
        "hipr": "index_high",
        "lopr": "index_low",
        "trqu": "index_volume",
        "trPrc": "index_trading_value",
    }
    df = df.rename(columns=rename_map)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], format="%Y%m%d", errors="coerce")

    for col in ["index_open", "index_high", "index_low", "index_close", "index_change", "index_change_rate", "index_volume", "index_trading_value"]:
        if col in df.columns:
            df[col] = _to_numeric(df[col])

    required = ["date", "index_name", "index_open", "index_high", "index_low", "index_close", "index_volume"]
    for col in required:
        if col not in df.columns:
            df[col] = pd.NA
    return df.sort_values("date").reset_index(drop=True)
