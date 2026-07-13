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
    assert "market_volatility_20d" in result.columns
    assert "excess_return_1d" in result.columns
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
    assert result["market_volatility_5d"].eq(0).all()
    assert result["market_volatility_20d"].eq(0).all()
    assert result["excess_return_1d"].equals(result["return_1d"])
    assert result["excess_return_5d"].equals(result["return_5d"])


def test_market_features_use_only_current_and_past_index_closes():
    df = pd.DataFrame(
        {
            "date": pd.date_range("2024-01-01", periods=80, freq="B"),
            "close": range(100, 180),
            "volume": range(1000, 1080),
            "index_close": range(2500, 2580),
        }
    )
    baseline = add_price_features(df)
    changed = df.copy()
    changed.loc[changed.index[-1], "index_close"] = 9999
    changed_result = add_price_features(changed)

    columns = ["market_return_1d", "market_return_5d", "market_volatility_5d", "market_volatility_20d"]
    pd.testing.assert_frame_equal(baseline.loc[:-2, columns], changed_result.loc[:-2, columns])
