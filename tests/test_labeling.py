import pandas as pd

from src.labeling import add_forward_return_label


def test_add_forward_return_label():
    df = pd.DataFrame(
        {
            "date": pd.date_range("2024-01-01", periods=7, freq="B"),
            "close": [100, 101, 102, 103, 104, 110, 90],
        }
    )
    result = add_forward_return_label(df, horizon=5)
    assert round(result.loc[0, "future_return_5d"], 4) == 0.1
    assert result.loc[0, "label_up_5d"] == 1
    assert pd.isna(result.loc[2, "label_up_5d"])
