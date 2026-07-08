from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import pandas as pd
import requests


@dataclass(frozen=True)
class FscStockApiClient:
    """공공데이터포털 금융위원회_주식시세정보 API client.

    Endpoint:
    https://apis.data.go.kr/1160100/service/GetStockSecuritiesInfoService/getStockPriceInfo

    주의:
    - 서비스키는 `.env`에서 주입한다.
    - 공공데이터포털 응답 컬럼은 문자열 숫자가 많으므로 normalize 단계에서 변환한다.
    - 금융위원회 데이터는 실시간이 아니라 기준일자 다음 영업일 오후 1시 이후 갱신되는 것으로 안내되어 있다.
    """

    service_key: str
    base_url: str = "https://apis.data.go.kr/1160100/service/GetStockSecuritiesInfoService/getStockPriceInfo"
    sleep_seconds: float = 0.15

    def fetch_by_date(self, bas_dt: str, ticker: str | None = None, num_rows: int = 5000) -> pd.DataFrame:
        params: dict[str, Any] = {
            "serviceKey": self.service_key,
            "resultType": "json",
            "numOfRows": num_rows,
            "pageNo": 1,
            "basDt": bas_dt.replace("-", ""),
        }
        if ticker:
            params["likeSrtnCd"] = ticker

        response = requests.get(self.base_url, params=params, timeout=30)
        response.raise_for_status()
        payload = response.json()
        items = _extract_items(payload)
        time.sleep(self.sleep_seconds)
        return normalize_stock_price_items(items)

    def fetch_range(self, start: str, end: str, ticker: str) -> pd.DataFrame:
        dates = pd.bdate_range(start=start, end=end)
        frames: list[pd.DataFrame] = []
        for dt in dates:
            try:
                df = self.fetch_by_date(dt.strftime("%Y%m%d"), ticker=ticker)
            except Exception as exc:  # noqa: BLE001 - API skeleton에서 날짜별 실패를 기록하고 넘어간다.
                print(f"[WARN] stock fetch failed: {dt.date()} {exc}")
                continue
            if not df.empty:
                frames.append(df)
        if not frames:
            raise RuntimeError("No stock data fetched. Check API key, date range, and ticker.")
        return pd.concat(frames, ignore_index=True).drop_duplicates(["date", "ticker"])


def _extract_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    body = payload.get("response", {}).get("body", {})
    items = body.get("items", {}).get("item", [])
    if isinstance(items, dict):
        return [items]
    return items or []


def _to_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series.astype(str).str.replace(",", "", regex=False), errors="coerce")


def normalize_stock_price_items(items: list[dict[str, Any]]) -> pd.DataFrame:
    if not items:
        return pd.DataFrame()

    df = pd.DataFrame(items)
    rename_map = {
        "basDt": "date",
        "srtnCd": "ticker",
        "isinCd": "isin_code",
        "itmsNm": "name",
        "mrktCtg": "market",
        "clpr": "close",
        "vs": "change",
        "fltRt": "change_rate",
        "mkp": "open",
        "hipr": "high",
        "lopr": "low",
        "trqu": "volume",
        "trPrc": "trading_value",
        "lstgStCnt": "shares_outstanding",
        "mrktTotAmt": "market_cap",
    }
    df = df.rename(columns=rename_map)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], format="%Y%m%d", errors="coerce")

    for col in ["open", "high", "low", "close", "change", "change_rate", "volume", "trading_value", "shares_outstanding", "market_cap"]:
        if col in df.columns:
            df[col] = _to_numeric(df[col])

    required = ["date", "ticker", "name", "market", "open", "high", "low", "close", "volume", "trading_value"]
    for col in required:
        if col not in df.columns:
            df[col] = pd.NA
    return df.sort_values("date").reset_index(drop=True)
