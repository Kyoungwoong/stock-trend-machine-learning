from __future__ import annotations

import argparse

import joblib

from config import SETTINGS
from storage import load_parquet


def predict_latest(ticker: str) -> None:
    dataset_path = SETTINGS.data_dir / "processed" / f"{ticker}_dataset.parquet"
    model_path = SETTINGS.model_dir / f"{ticker}_model.joblib"
    df = load_parquet(dataset_path).sort_values("date")
    artifact = joblib.load(model_path)
    model = artifact["model"]
    feature_columns = artifact["feature_columns"]

    latest = df.iloc[[-1]].copy()
    x = latest[feature_columns]
    pred = int(model.predict(x)[0])
    probability = float(model.predict_proba(x)[:, 1][0]) if hasattr(model, "predict_proba") else float(pred)

    direction = "up" if pred == 1 else "not_up"
    print("date,ticker,prediction,probability")
    print(f"{latest['date'].iloc[0].date()},{ticker},{direction},{probability:.4f}")
    print("\n주의: 이 출력은 교육용 모델 결과이며 투자 추천이 아닙니다.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ticker", default=SETTINGS.default_ticker)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    predict_latest(args.ticker)


if __name__ == "__main__":
    main()
