from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import pandas as pd
import requests


@dataclass(frozen=True)
class KrxIndexApiClient:
    auth_key: str
    base_url: str = "https://data-dbg.krx.co.kr/svc/apis/idx/kospi_dd_trd"
    sleep_seconds: float = 0.05

    def fetch_range_raw(self, start: str, end: str, index_name: str = "KOSPI") -> pd.DataFrame:
        frames: list[pd.DataFrame] = []
        for date in pd.bdate_range(start=start, end=end):
            response = requests.get(
                self.base_url,
                headers={"AUTH_KEY": self.auth_key},
                params={"basDd": date.strftime("%Y%m%d")},
                timeout=30,
            )
            _raise_for_http_error(response)
            rows = _extract_rows(response.json())
            if rows:
                frames.append(pd.DataFrame(rows))
            time.sleep(self.sleep_seconds)

        if not frames:
            raise RuntimeError(f"No KRX index data fetched for {index_name}. Check API permission and date range.")

        raw = pd.concat(frames, ignore_index=True).drop_duplicates()
        name_column = "IDX_NM" if "IDX_NM" in raw.columns else "idxNm"
        if name_column in raw.columns:
            aliases = {"KOSPI", "코스피"}
            selected = raw[raw[name_column].astype(str).str.strip().isin(aliases)]
            if selected.empty:
                raise RuntimeError("KRX response had no exact KOSPI index rows.")
            raw = selected
        return raw.reset_index(drop=True)

    def fetch_range(self, start: str, end: str, index_name: str = "KOSPI") -> pd.DataFrame:
        raw = self.fetch_range_raw(start=start, end=end, index_name=index_name)
        return normalize_krx_index_items(raw.to_dict("records"))


def _extract_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows = payload.get("OutBlock_1", [])
    if isinstance(rows, dict):
        return [rows]
    return rows or []


def _raise_for_http_error(response: requests.Response) -> None:
    if response.ok:
        return
    # AUTH_KEY는 header로 전달되며 오류 메시지에는 상태와 endpoint만 남긴다.
    endpoint = response.request.path_url.split("?")[0]
    raise RuntimeError(f"KRX API HTTP error status={response.status_code} endpoint={endpoint}")


def _to_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series.astype(str).str.replace(",", "", regex=False), errors="coerce")


def normalize_krx_index_items(items: list[dict[str, Any]]) -> pd.DataFrame:
    if not items:
        return pd.DataFrame()

    df = pd.DataFrame(items).rename(
        columns={
            "BAS_DD": "date",
            "IDX_NM": "index_name",
            "OPNPRC_IDX": "open",
            "HGPRC_IDX": "high",
            "LWPRC_IDX": "low",
            "CLSPRC_IDX": "close",
            "ACC_TRDVOL": "volume",
            "ACC_TRDVAL": "trading_value",
            "FLUC_RT": "change_rate",
        }
    )
    df["date"] = pd.to_datetime(df.get("date"), format="%Y%m%d", errors="coerce")
    for column in ["open", "high", "low", "close", "volume", "trading_value", "change_rate"]:
        if column in df.columns:
            df[column] = _to_numeric(df[column])

    df["index_code"] = "KOSPI"
    df["index_name"] = "KOSPI"
    columns = ["date", "index_code", "index_name", "open", "high", "low", "close", "volume", "trading_value", "change_rate"]
    for column in columns:
        if column not in df.columns:
            df[column] = pd.NA
    return df[columns].dropna(subset=["date", "close"]).drop_duplicates("date").sort_values("date").reset_index(drop=True)
