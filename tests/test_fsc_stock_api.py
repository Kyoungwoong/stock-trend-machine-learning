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


def test_normalize_stock_price_items_accepts_korean_columns():
    result = normalize_stock_price_items(
        [
            {
                "기준일자": "20240103",
                "종목코드": "005930",
                "종목명": "삼성전자",
                "시장구분": "KOSPI",
                "시가": "77,000",
                "고가": "78,000",
                "저가": "76,500",
                "종가": "77,800",
                "거래량": "10,000",
                "거래대금": "778,000,000",
                "상장주식수": "5,969,782,550",
                "시가총액": "464,000,000,000",
                "등락률": "1.20",
            }
        ]
    )

    assert result.loc[0, "date"] == pd.Timestamp("2024-01-03")
    assert result.loc[0, "ticker"] == "005930"
    assert result.loc[0, "close"] == 77800
    assert result.loc[0, "change_rate"] == 1.20
