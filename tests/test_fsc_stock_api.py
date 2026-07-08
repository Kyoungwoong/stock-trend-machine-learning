import pandas as pd

from src.data_sources.fsc_stock_api import normalize_stock_price_items


def test_normalize_stock_price_items_maps_public_api_columns():
    result = normalize_stock_price_items(
        [
            {
                "basDt": "20240102",
                "srtnCd": "005930",
                "itmsNm": "삼성전자",
                "mrktCtg": "KOSPI",
                "mkp": "78,200",
                "hipr": "79,000",
                "lopr": "77,500",
                "clpr": "78,100",
                "trqu": "12,345,678",
                "trPrc": "965,432,100,000",
                "lstgStCnt": "5,969,782,550",
                "mrktTotAmt": "466,250,018,000",
                "fltRt": "-0.13",
            }
        ]
    )

    assert list(result["ticker"]) == ["005930"]
    assert result.loc[0, "date"] == pd.Timestamp("2024-01-02")
    assert result.loc[0, "open"] == 78200
    assert result.loc[0, "volume"] == 12345678
    assert result.loc[0, "listed_shares"] == 5969782550
    assert result.loc[0, "change_rate"] == -0.13


def test_normalize_stock_price_items_keeps_required_columns_when_optional_missing():
    result = normalize_stock_price_items([{"basDt": "20240102", "srtnCd": "005930"}])

    for column in [
        "date",
        "ticker",
        "name",
        "market",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "trading_value",
        "listed_shares",
        "market_cap",
        "change_rate",
    ]:
        assert column in result.columns
