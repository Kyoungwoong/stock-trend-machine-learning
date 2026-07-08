from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from config import SETTINGS
from data_sources.fsc_index_api import FscIndexApiClient
from data_sources.fsc_stock_api import FscStockApiClient
from features import FEATURE_COLUMNS, add_price_features
from labeling import add_forward_return_label, drop_unlabeled_rows
from sample_data import generate_sample_index, generate_sample_stock
from storage import save_parquet, write_report


def build_dataset(ticker: str, start: str, end: str, use_sample: bool) -> pd.DataFrame:
    raw_dir = SETTINGS.data_dir / "raw"
    processed_dir = SETTINGS.data_dir / "processed"

    if use_sample:
        stock_df = generate_sample_stock(ticker=ticker, start=start, end=end)
        index_df = generate_sample_index(index_name="KOSPI_SAMPLE", start=start, end=end)
    else:
        if not SETTINGS.data_go_kr_service_key:
            raise RuntimeError("DATA_GO_KR_SERVICE_KEY is required. Or run with --use-sample.")
        stock_client = FscStockApiClient(service_key=SETTINGS.data_go_kr_service_key)
        index_client = FscIndexApiClient(service_key=SETTINGS.data_go_kr_service_key)
        stock_df = stock_client.fetch_range(start=start, end=end, ticker=ticker)
        index_df = index_client.fetch_range(start=start, end=end, index_name="코스피")

    stock_path = raw_dir / f"{ticker}_stock.parquet"
    index_path = raw_dir / "kospi_index.parquet"
    save_parquet(stock_df, stock_path)
    save_parquet(index_df, index_path)

    merged = merge_stock_and_index(stock_df, index_df)
    featured = add_price_features(merged)
    latest_features = featured.dropna(subset=FEATURE_COLUMNS).reset_index(drop=True)
    labeled = add_forward_return_label(featured, horizon=5)
    dataset = drop_unlabeled_rows(labeled).dropna(subset=FEATURE_COLUMNS).reset_index(drop=True)

    output_path = processed_dir / f"{ticker}_dataset.parquet"
    latest_path = processed_dir / f"{ticker}_latest_features.parquet"
    save_parquet(dataset, output_path)
    save_parquet(latest_features, latest_path)
    write_data_summary(ticker=ticker, dataset=dataset, latest_features=latest_features, use_sample=use_sample)
    return dataset


def merge_stock_and_index(stock_df: pd.DataFrame, index_df: pd.DataFrame) -> pd.DataFrame:
    stock = stock_df.copy()
    index = index_df.copy()
    stock["date"] = pd.to_datetime(stock["date"])
    index["date"] = pd.to_datetime(index["date"])
    merged = pd.merge(stock, index, on="date", how="inner")
    return merged.sort_values("date").reset_index(drop=True)


def write_data_summary(ticker: str, dataset: pd.DataFrame, latest_features: pd.DataFrame, use_sample: bool) -> None:
    label_dist = {int(label): int(count) for label, count in dataset["label_up_5d"].value_counts(dropna=False).items()}
    content = f"""
# Data Summary

## Dataset

- ticker: `{ticker}`
- rows: `{len(dataset):,}`
- start: `{dataset['date'].min().date()}`
- end: `{dataset['date'].max().date()}`
- source: `{'sample synthetic data' if use_sample else 'public API data'}`
- latest feature date: `{latest_features['date'].max().date()}`

## Label distribution

```text
{label_dist}
```

## Notes

- `future_return_5d`는 label 생성 및 평가용 컬럼이다.
- `label_up_5d`와 `future_return_5d`는 모델 입력 feature에서 제외해야 한다.
- rolling feature는 장마감 후 예측을 전제로 현재일 OHLCV를 포함한다.
- `data/processed/{ticker}_latest_features.parquet`는 최신 예측용 feature이며 label 생성 가능 여부와 분리해 저장한다.
- 샘플 데이터는 실제 삼성전자/KOSPI 시장 데이터가 아니며 파이프라인 검증용 합성 데이터다.
"""
    write_report(SETTINGS.report_dir / "data_summary.md", content.strip() + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ticker", default=SETTINGS.default_ticker)
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument("--use-sample", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    dataset = build_dataset(ticker=args.ticker, start=args.start, end=args.end, use_sample=args.use_sample)
    output_path = Path(SETTINGS.data_dir) / "processed" / f"{args.ticker}_dataset.parquet"
    print(f"Dataset saved: {output_path} rows={len(dataset):,}")


if __name__ == "__main__":
    main()
