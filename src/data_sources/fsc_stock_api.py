from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import unquote

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

    def fetch_raw_by_date(self, bas_dt: str, ticker: str | None = None, num_rows: int = 1000) -> pd.DataFrame:
        items: list[dict[str, Any]] = []
        page_no = 1

        while True:
            payload = self._request_page(bas_dt=bas_dt, ticker=ticker, page_no=page_no, num_rows=num_rows)
            page_items = _extract_items(payload)
            items.extend(page_items)

            body = payload.get("response", {}).get("body", {})
            total_count = int(body.get("totalCount") or len(items))
            if len(items) >= total_count or not page_items:
                break
            page_no += 1

        time.sleep(self.sleep_seconds)
        return pd.DataFrame(items)

    def fetch_by_date(self, bas_dt: str, ticker: str | None = None, num_rows: int = 1000) -> pd.DataFrame:
        raw = self.fetch_raw_by_date(bas_dt=bas_dt, ticker=ticker, num_rows=num_rows)
        return normalize_stock_price_items(raw.to_dict("records"))

    def fetch_range_raw(self, start: str, end: str, ticker: str) -> pd.DataFrame:
        items: list[dict[str, Any]] = []
        page_no = 1

        while True:
            payload = self._request_range_page(start=start, end=end, ticker=ticker, page_no=page_no, num_rows=1000)
            page_items = _extract_items(payload)
            items.extend(page_items)

            body = payload.get("response", {}).get("body", {})
            total_count = int(body.get("totalCount") or len(items))
            if len(items) >= total_count or not page_items:
                break
            page_no += 1

        if not items:
            raise RuntimeError(f"No stock data fetched for {ticker}. Check API key, date range, and ticker.")

        time.sleep(self.sleep_seconds)
        return pd.DataFrame(items).drop_duplicates()

    def fetch_range(self, start: str, end: str, ticker: str) -> pd.DataFrame:
        raw = self.fetch_range_raw(start=start, end=end, ticker=ticker)
        normalized = normalize_stock_price_items(raw.to_dict("records"))
        return normalized.drop_duplicates(["date", "ticker"])

    def _request_page(self, bas_dt: str, ticker: str | None, page_no: int, num_rows: int) -> dict[str, Any]:
        params: dict[str, Any] = {
            "serviceKey": unquote(self.service_key),
            "resultType": "json",
            "numOfRows": num_rows,
            "pageNo": page_no,
            "basDt": bas_dt.replace("-", ""),
        }
        if ticker:
            params["likeSrtnCd"] = ticker

        response = requests.get(self.base_url, params=params, timeout=30)
        _raise_for_http_error(response)
        payload = response.json()
        _raise_for_api_error(payload)
        return payload

    def _request_range_page(self, start: str, end: str, ticker: str, page_no: int, num_rows: int) -> dict[str, Any]:
        params: dict[str, Any] = {
            "serviceKey": unquote(self.service_key),
            "resultType": "json",
            "numOfRows": num_rows,
            "pageNo": page_no,
            "beginBasDt": start.replace("-", ""),
            "endBasDt": end.replace("-", ""),
            "likeSrtnCd": ticker,
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


def normalize_stock_price_items(items: list[dict[str, Any]]) -> pd.DataFrame:
    if not items:
        return pd.DataFrame()

    df = pd.DataFrame(items)
    rename_map = {
        "basDt": "date",
        "기준일자": "date",
        "srtnCd": "ticker",
        "단축코드": "ticker",
        "종목코드": "ticker",
        "isinCd": "isin_code",
        "ISIN코드": "isin_code",
        "itmsNm": "name",
        "종목명": "name",
        "mrktCtg": "market",
        "시장구분": "market",
        "clpr": "close",
        "종가": "close",
        "vs": "change",
        "대비": "change",
        "fltRt": "change_rate",
        "등락률": "change_rate",
        "mkp": "open",
        "시가": "open",
        "hipr": "high",
        "고가": "high",
        "lopr": "low",
        "저가": "low",
        "trqu": "volume",
        "거래량": "volume",
        "trPrc": "trading_value",
        "거래대금": "trading_value",
        "lstgStCnt": "listed_shares",
        "상장주식수": "listed_shares",
        "mrktTotAmt": "market_cap",
        "시가총액": "market_cap",
    }
    df = df.rename(columns=rename_map)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], format="%Y%m%d", errors="coerce")

    for col in ["open", "high", "low", "close", "change", "change_rate", "volume", "trading_value", "listed_shares", "market_cap"]:
        if col in df.columns:
            df[col] = _to_numeric(df[col])

    required = ["date", "ticker", "name", "market", "open", "high", "low", "close", "volume", "trading_value", "listed_shares", "market_cap", "change_rate"]
    for col in required:
        if col not in df.columns:
            df[col] = pd.NA
    return df.sort_values("date").reset_index(drop=True)
