from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import unquote

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

    def fetch_raw_by_date(self, bas_dt: str, index_name: str = "코스피", num_rows: int = 1000) -> pd.DataFrame:
        items: list[dict[str, Any]] = []
        page_no = 1

        while True:
            payload = self._request_page(bas_dt=bas_dt, index_name=index_name, page_no=page_no, num_rows=num_rows)
            page_items = _extract_items(payload)
            items.extend(page_items)

            body = payload.get("response", {}).get("body", {})
            total_count = int(body.get("totalCount") or len(items))
            if len(items) >= total_count or not page_items:
                break
            page_no += 1

        time.sleep(self.sleep_seconds)
        return pd.DataFrame(items)

    def fetch_by_date(self, bas_dt: str, index_name: str = "코스피", num_rows: int = 1000) -> pd.DataFrame:
        raw = self.fetch_raw_by_date(bas_dt=bas_dt, index_name=index_name, num_rows=num_rows)
        return normalize_index_items(raw.to_dict("records"))

    def fetch_range_raw(self, start: str, end: str, index_name: str = "코스피") -> pd.DataFrame:
        items: list[dict[str, Any]] = []
        page_no = 1

        while True:
            payload = self._request_range_page(start=start, end=end, index_name=index_name, page_no=page_no, num_rows=1000)
            page_items = _extract_items(payload)
            items.extend(page_items)

            body = payload.get("response", {}).get("body", {})
            total_count = int(body.get("totalCount") or len(items))
            if len(items) >= total_count or not page_items:
                break
            page_no += 1

        if not items:
            raise RuntimeError(f"No index data fetched for {index_name}. Check API key, date range, and index name.")

        time.sleep(self.sleep_seconds)
        return pd.DataFrame(items).drop_duplicates()

    def fetch_range(self, start: str, end: str, index_name: str = "코스피") -> pd.DataFrame:
        raw = self.fetch_range_raw(start=start, end=end, index_name=index_name)
        normalized = normalize_index_items(raw.to_dict("records"))
        return normalized.drop_duplicates(["date", "index_name"])

    def _request_page(self, bas_dt: str, index_name: str, page_no: int, num_rows: int) -> dict[str, Any]:
        params: dict[str, Any] = {
            "serviceKey": unquote(self.service_key),
            "resultType": "json",
            "numOfRows": num_rows,
            "pageNo": page_no,
            "basDt": bas_dt.replace("-", ""),
            "idxNm": index_name,
        }
        response = requests.get(self.base_url, params=params, timeout=30)
        _raise_for_http_error(response)
        payload = response.json()
        _raise_for_api_error(payload)
        return payload

    def _request_range_page(self, start: str, end: str, index_name: str, page_no: int, num_rows: int) -> dict[str, Any]:
        params: dict[str, Any] = {
            "serviceKey": unquote(self.service_key),
            "resultType": "json",
            "numOfRows": num_rows,
            "pageNo": page_no,
            "beginBasDt": start.replace("-", ""),
            "endBasDt": end.replace("-", ""),
            "idxNm": index_name,
        }
        response = requests.get(self.base_url, params=params, timeout=30)
        _raise_for_http_error(response)
        payload = response.json()
        _raise_for_api_error(payload)
        return payload


def _extract_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    body = payload.get("response", {}).get("body", {})
    items = body.get("items", {}).get("item", [])
    if isinstance(items, dict):
        return [items]
    return items or []


def _raise_for_api_error(payload: dict[str, Any]) -> None:
    header = payload.get("response", {}).get("header", {})
    result_code = str(header.get("resultCode", "00"))
    result_msg = header.get("resultMsg", "")
    if result_code not in {"00", "0"}:
        raise RuntimeError(f"Public data API error resultCode={result_code} resultMsg={result_msg}")


def _raise_for_http_error(response: requests.Response) -> None:
    if response.ok:
        return
    raise RuntimeError(f"Public data API HTTP error status={response.status_code} endpoint={response.request.path_url.split('?')[0]}")


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
