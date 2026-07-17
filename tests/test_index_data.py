import pandas as pd
import pytest
import requests
from types import SimpleNamespace

from src.data_sources.fsc_index_api import normalize_index_items
from src.data_sources.krx_index_api import _raise_for_http_error, normalize_krx_index_items
from src.pipeline.data_pipeline import merge_stock_and_index
import src.pipeline.data_pipeline as data_pipeline


def test_fsc_index_normalization_uses_internal_schema():
    result = normalize_index_items(
        [{"basDt": "20240102", "idxNm": "코스피", "mkp": "2,600", "hipr": "2,620", "lopr": "2,590", "clpr": "2,610", "trqu": "100", "trPrc": "200", "fltRt": "0.4"}]
    )

    assert list(result.columns) == ["date", "index_code", "index_name", "open", "high", "low", "close", "volume", "trading_value", "change_rate"]
    assert result.loc[0, "date"] == pd.Timestamp("2024-01-02")
    assert result.loc[0, "index_code"] == "KOSPI"
    assert result.loc[0, "close"] == 2610


def test_krx_index_normalization_uses_internal_schema():
    result = normalize_krx_index_items(
        [{"BAS_DD": "20240102", "IDX_NM": "코스피", "OPNPRC_IDX": "2,600", "HGPRC_IDX": "2,620", "LWPRC_IDX": "2,590", "CLSPRC_IDX": "2,610", "ACC_TRDVOL": "100", "ACC_TRDVAL": "200", "FLUC_RT": "0.4"}]
    )

    assert result.loc[0, "index_name"] == "KOSPI"
    assert result.loc[0, "close"] == 2610


def test_merge_stock_and_index_is_inner_joined_by_date():
    stock = pd.DataFrame({"date": pd.to_datetime(["2024-01-02", "2024-01-03"]), "close": [70000, 71000], "volume": [10, 20]})
    index = pd.DataFrame({"date": pd.to_datetime(["2024-01-03", "2024-01-04"]), "index_code": ["KOSPI", "KOSPI"], "index_name": ["KOSPI", "KOSPI"], "close": [2600, 2610]})

    result = merge_stock_and_index(stock, index)

    assert list(result["date"]) == [pd.Timestamp("2024-01-03")]
    assert result.loc[0, "close"] == 71000
    assert result.loc[0, "index_close"] == 2600


def test_merge_without_index_keeps_stock_only_rows():
    stock = pd.DataFrame({"date": pd.to_datetime(["2024-01-02", "2024-01-03"]), "close": [70000, 71000], "volume": [10, 20]})
    result = merge_stock_and_index(stock, pd.DataFrame())
    pd.testing.assert_frame_equal(result, stock)


def test_krx_http_error_does_not_expose_auth_key():
    secret = "never-print-this-key"
    response = requests.Response()
    response.status_code = 403
    response.request = requests.Request("GET", "https://data-dbg.krx.co.kr/svc/apis/idx/kospi_dd_trd", headers={"AUTH_KEY": secret}).prepare()

    with pytest.raises(RuntimeError) as error:
        _raise_for_http_error(response)

    assert secret not in str(error.value)


def test_fetch_kospi_index_prefers_fsc(monkeypatch):
    class FscSuccess:
        def __init__(self, service_key):
            pass

        def fetch_range_raw(self, **kwargs):
            return pd.DataFrame([{"basDt": "20240102", "idxNm": "코스피", "clpr": "2,600"}])

    monkeypatch.setattr(data_pipeline, "SETTINGS", SimpleNamespace(data_go_kr_service_key="data-key", krx_auth_key="krx-key"))
    monkeypatch.setattr(data_pipeline, "FscIndexApiClient", FscSuccess)

    _, normalized, source, errors = data_pipeline.fetch_kospi_index("2024-01-01", "2024-01-02")

    assert source == "fsc"
    assert len(normalized) == 1
    assert errors == []


def test_fetch_kospi_index_uses_krx_after_fsc_failure_and_redacts_key(monkeypatch):
    secret = "data+/=secret"

    class FscFailure:
        def __init__(self, service_key):
            pass

        def fetch_range_raw(self, **kwargs):
            raise RuntimeError(f"request failed serviceKey={secret}")

    class KrxSuccess:
        def __init__(self, auth_key):
            pass

        def fetch_range_raw(self, **kwargs):
            return pd.DataFrame([{"BAS_DD": "20240102", "IDX_NM": "코스피", "CLSPRC_IDX": "2,600"}])

    monkeypatch.setattr(data_pipeline, "SETTINGS", SimpleNamespace(data_go_kr_service_key=secret, krx_auth_key="krx-key"))
    monkeypatch.setattr(data_pipeline, "FscIndexApiClient", FscFailure)
    monkeypatch.setattr(data_pipeline, "KrxIndexApiClient", KrxSuccess)

    _, normalized, source, errors = data_pipeline.fetch_kospi_index("2024-01-01", "2024-01-02")

    assert source == "krx"
    assert len(normalized) == 1
    assert secret not in " ".join(errors)
    assert "[REDACTED]" in " ".join(errors)


def test_fetch_kospi_index_falls_back_when_both_sources_fail(monkeypatch):
    class Failure:
        def __init__(self, **kwargs):
            pass

        def fetch_range_raw(self, **kwargs):
            raise RuntimeError("unauthorized")

    monkeypatch.setattr(data_pipeline, "SETTINGS", SimpleNamespace(data_go_kr_service_key="data-key", krx_auth_key="krx-key"))
    monkeypatch.setattr(data_pipeline, "FscIndexApiClient", Failure)
    monkeypatch.setattr(data_pipeline, "KrxIndexApiClient", Failure)

    raw, normalized, source, errors = data_pipeline.fetch_kospi_index("2024-01-01", "2024-01-02")

    assert source == "stock_only_fallback"
    assert raw.empty and normalized.empty
    assert len(errors) == 2
