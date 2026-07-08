import pandas as pd

from src.features import FEATURE_COLUMNS, add_price_features


def test_add_price_features_contains_expected_columns():
    df = pd.DataFrame(
        {
            "date": pd.date_range("2024-01-01", periods=80, freq="B"),
            "close": range(100, 180),
            "volume": range(1000, 1080),
            "index_close": range(2500, 2580),
        }
    )
    result = add_price_features(df)
    assert "return_5d" in result.columns
    assert "ma_60" in result.columns
    assert "market_return_5d" in result.columns
    assert "excess_return_5d" in result.columns


def test_feature_columns_do_not_include_label_columns():
    assert "label_up_5d" not in FEATURE_COLUMNS
    assert "future_return_5d" not in FEATURE_COLUMNS


def test_add_price_features_without_index_uses_stock_only_market_defaults():
    df = pd.DataFrame(
        {
            "date": pd.date_range("2024-01-01", periods=80, freq="B"),
            "close": range(100, 180),
            "volume": range(1000, 1080),
        }
    )

    result = add_price_features(df)

    assert result["market_return_1d"].dropna().eq(0).all()
    assert result["market_return_5d"].dropna().eq(0).all()
    assert result["excess_return_5d"].equals(result["return_5d"])
