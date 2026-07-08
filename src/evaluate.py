from __future__ import annotations

import argparse

import joblib
import pandas as pd
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score

from config import SETTINGS
from labeling import LABEL_COLUMN
from storage import load_parquet, write_report
from train import split_by_date


def evaluate(ticker: str) -> None:
    dataset_path = SETTINGS.data_dir / "processed" / f"{ticker}_dataset.parquet"
    model_path = SETTINGS.model_dir / f"{ticker}_model.joblib"
    df = load_parquet(dataset_path).sort_values("date")
    artifact = joblib.load(model_path)
    model = artifact["model"]
    feature_columns = artifact["feature_columns"]
    model_name = artifact["model_name"]

    _, _, test_df = split_by_date(df)
    x_test = test_df[feature_columns]
    y_test = test_df[LABEL_COLUMN].astype(int)
    pred = model.predict(x_test)

    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(x_test)[:, 1]
        auc = roc_auc_score(y_test, proba)
    else:
        proba = pred
        auc = float("nan")

    cm = confusion_matrix(y_test, pred)
    metrics = {
        "accuracy": accuracy_score(y_test, pred),
        "precision": precision_score(y_test, pred, zero_division=0),
        "recall": recall_score(y_test, pred, zero_division=0),
        "f1": f1_score(y_test, pred, zero_division=0),
        "roc_auc": auc,
    }

    result_df = test_df[["date", "ticker", "close", "future_return_5d", LABEL_COLUMN]].copy()
    result_df["prediction"] = pred
    result_df["probability_up"] = proba
    result_path = SETTINGS.report_dir / f"{ticker}_predictions.csv"
    SETTINGS.report_dir.mkdir(parents=True, exist_ok=True)
    result_df.to_csv(result_path, index=False, encoding="utf-8-sig")

    content = f"""
# Evaluation Summary

## Model

- ticker: `{ticker}`
- selected model: `{model_name}`
- test period: `{test_df['date'].min().date()}` ~ `{test_df['date'].max().date()}`

## Metrics

| metric | value |
|---|---:|
{chr(10).join(f'| {name} | {value:.4f} |' for name, value in metrics.items())}

## Confusion Matrix

```text
{cm}
```

## Prediction file

`{result_path}`

## Notes

- ML 지표는 방향성 분류 성능을 보여준다.
- 실제 투자 성과는 `backtest.py`에서 별도로 확인한다.
"""
    write_report(SETTINGS.report_dir / "model_comparison.md", content.strip() + "\n")
    print(content)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ticker", default=SETTINGS.default_ticker)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    evaluate(args.ticker)


if __name__ == "__main__":
    main()
