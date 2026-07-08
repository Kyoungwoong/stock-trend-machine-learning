from __future__ import annotations

import argparse

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from src.core.config import SETTINGS
from src.core.storage import load_parquet, write_report
from src.domain.features import FEATURE_COLUMNS
from src.domain.labeling import FUTURE_RETURN_COLUMN, LABEL_COLUMN


def split_by_date(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    df = df.sort_values("date").reset_index(drop=True)
    train = df[df["date"] < "2024-01-01"].copy()
    valid = df[(df["date"] >= "2024-01-01") & (df["date"] < "2025-01-01")].copy()
    test = df[df["date"] >= "2025-01-01"].copy()

    if train.empty or valid.empty or test.empty:
        n = len(df)
        train = df.iloc[: int(n * 0.7)].copy()
        valid = df.iloc[int(n * 0.7): int(n * 0.85)].copy()
        test = df.iloc[int(n * 0.85):].copy()
    return train, valid, test


def validate_feature_columns() -> None:
    leakage_columns = {LABEL_COLUMN, FUTURE_RETURN_COLUMN}
    leaked = leakage_columns.intersection(FEATURE_COLUMNS)
    if leaked:
        raise ValueError(f"Leakage columns must not be model features: {sorted(leaked)}")


def build_models(random_state: int = 42) -> dict[str, Pipeline]:
    return {
        "logistic_regression": Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
                ("model", LogisticRegression(max_iter=1000, random_state=random_state)),
            ]
        ),
        "random_forest": Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="median")),
                (
                    "model",
                    RandomForestClassifier(
                        n_estimators=300,
                        min_samples_leaf=10,
                        random_state=random_state,
                        n_jobs=-1,
                    ),
                ),
            ]
        ),
    }


def train(ticker: str) -> None:
    validate_feature_columns()
    dataset_path = SETTINGS.data_dir / "processed" / f"{ticker}_dataset.parquet"
    df = load_parquet(dataset_path).sort_values("date")
    train_df, valid_df, test_df = split_by_date(df)

    x_train = train_df[FEATURE_COLUMNS]
    y_train = train_df[LABEL_COLUMN].astype(int)
    x_valid = valid_df[FEATURE_COLUMNS]
    y_valid = valid_df[LABEL_COLUMN].astype(int)

    models = build_models()
    scores: dict[str, float] = {}
    fitted_models: dict[str, Pipeline] = {}
    for name, model in models.items():
        model.fit(x_train, y_train)
        valid_score = model.score(x_valid, y_valid)
        scores[name] = float(valid_score)
        fitted_models[name] = model

    best_name = max(scores, key=scores.get)
    best_model = fitted_models[best_name]

    SETTINGS.model_dir.mkdir(parents=True, exist_ok=True)
    model_path = SETTINGS.model_dir / f"{ticker}_model.joblib"
    joblib.dump(
        {
            "model_name": best_name,
            "model": best_model,
            "feature_columns": FEATURE_COLUMNS,
            "train_start": str(train_df["date"].min().date()),
            "train_end": str(train_df["date"].max().date()),
            "valid_start": str(valid_df["date"].min().date()),
            "valid_end": str(valid_df["date"].max().date()),
            "test_start": str(test_df["date"].min().date()),
            "test_end": str(test_df["date"].max().date()),
            "validation_scores": scores,
        },
        model_path,
    )

    content = f"""
# Model Comparison

## Training Split

| split | rows | start | end |
|---|---:|---|---|
| train | {len(train_df):,} | {train_df['date'].min().date()} | {train_df['date'].max().date()} |
| validation | {len(valid_df):,} | {valid_df['date'].min().date()} | {valid_df['date'].max().date()} |
| test | {len(test_df):,} | {test_df['date'].min().date()} | {test_df['date'].max().date()} |

## Validation Accuracy

| model | validation accuracy |
|---|---:|
{chr(10).join(f'| {name} | {score:.4f} |' for name, score in scores.items())}

## Selected model

`{best_name}`

## Notes

- validation accuracy는 모델 선택용 참고 지표다.
- 최종 평가는 `evaluate.py`에서 test set 기준으로 수행한다.
- `label_up_5d`와 `future_return_5d`는 모델 입력 feature에서 제외했다.
- split은 날짜 순서를 기준으로 하며 랜덤 shuffle을 사용하지 않는다.
"""
    write_report(SETTINGS.report_dir / "model_comparison.md", content.strip() + "\n")
    print(f"Model saved: {model_path} selected={best_name}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ticker", default=SETTINGS.default_ticker)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    train(args.ticker)


if __name__ == "__main__":
    main()
