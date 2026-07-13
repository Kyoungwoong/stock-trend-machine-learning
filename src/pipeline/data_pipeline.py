from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from src.core.config import SETTINGS
from src.core.storage import save_parquet, write_report
from src.data_sources.fsc_index_api import FscIndexApiClient, normalize_index_items
from src.data_sources.fsc_stock_api import FscStockApiClient, normalize_stock_price_items
from src.data_sources.krx_index_api import KrxIndexApiClient, normalize_krx_index_items
from src.domain.features import FEATURE_COLUMNS, add_price_features
from src.domain.labeling import add_forward_return_label, drop_unlabeled_rows
from src.domain.sample_data import generate_sample_index, generate_sample_stock


def build_dataset(ticker: str, start: str, end: str, use_sample: bool) -> pd.DataFrame:
    raw_dir = SETTINGS.data_dir / "raw"
    interim_dir = SETTINGS.data_dir / "interim"
    processed_dir = SETTINGS.data_dir / "processed"
    source = "sample synthetic data" if use_sample else "public API data"

    if use_sample:
        stock_df = generate_sample_stock(ticker=ticker, start=start, end=end)
        index_df = generate_sample_index(index_name="KOSPI_SAMPLE", start=start, end=end)
        stock_raw = stock_df.copy()
        index_raw = index_df.copy()
        index_source = "sample synthetic KOSPI data"
        index_errors: list[str] = []
    else:
        if not SETTINGS.data_go_kr_service_key:
            raise RuntimeError("DATA_GO_KR_SERVICE_KEY is required. Set it in .env or run with --use-sample.")
        stock_client = FscStockApiClient(service_key=SETTINGS.data_go_kr_service_key)
        stock_raw = stock_client.fetch_range_raw(start=start, end=end, ticker=ticker)
        stock_df = normalize_stock_price_items(stock_raw.to_dict("records"))
        index_raw, index_df, index_source, index_errors = fetch_kospi_index(start=start, end=end)
        if index_df.empty:
            source = "public API data (stock only; KOSPI index unavailable)"
        else:
            source = f"public API data (stock: FSC, index: {index_source})"

    stock_raw_path = raw_dir / f"{ticker}_stock_price.parquet" if not use_sample else raw_dir / f"{ticker}_stock_sample.parquet"
    stock_normalized_path = interim_dir / f"{ticker}_stock_price_normalized.parquet" if not use_sample else interim_dir / f"{ticker}_stock_sample_normalized.parquet"
    index_raw_path = raw_dir / "kospi_index.parquet" if not use_sample else raw_dir / "kospi_index_sample.parquet"
    index_normalized_path = interim_dir / "kospi_index_normalized.parquet" if not use_sample else interim_dir / "kospi_index_sample_normalized.parquet"
    save_parquet(stock_raw, stock_raw_path)
    save_parquet(stock_df, stock_normalized_path)
    save_parquet(index_raw, index_raw_path)
    save_parquet(index_df, index_normalized_path)

    merged = merge_stock_and_index(stock_df, index_df)
    featured = add_price_features(merged)
    latest_features = featured.dropna(subset=FEATURE_COLUMNS).reset_index(drop=True)
    labeled = add_forward_return_label(featured, horizon=5)
    dataset = drop_unlabeled_rows(labeled).dropna(subset=FEATURE_COLUMNS).reset_index(drop=True)

    output_path = processed_dir / f"{ticker}_dataset.parquet"
    latest_path = processed_dir / f"{ticker}_latest_features.parquet"
    save_parquet(dataset, output_path)
    save_parquet(latest_features, latest_path)
    write_data_summary(
        ticker=ticker,
        dataset=dataset,
        latest_features=latest_features,
        source=source,
        stock_raw=stock_raw,
        stock_df=stock_df,
        index_df=index_df,
        index_source=index_source,
        index_errors=index_errors,
        merged_rows=len(merged),
        paths={
            "stock_raw": stock_raw_path,
            "stock_normalized": stock_normalized_path,
            "index_raw": index_raw_path,
            "index_normalized": index_normalized_path,
            "dataset": output_path,
            "latest_features": latest_path,
        },
    )
    return dataset


def fetch_kospi_index(start: str, end: str) -> tuple[pd.DataFrame, pd.DataFrame, str, list[str]]:
    errors: list[str] = []
    fsc_client = FscIndexApiClient(service_key=SETTINGS.data_go_kr_service_key or "")
    try:
        raw = fsc_client.fetch_range_raw(start=start, end=end, index_name="코스피")
        normalized = normalize_index_items(raw.to_dict("records"))
        if normalized.empty:
            raise RuntimeError("FSC index response had no usable KOSPI rows.")
        return raw, normalized, "FSC index API", errors
    except Exception as exc:  # noqa: BLE001 - 다음 데이터 소스를 시도하고 원인은 report에 남긴다.
        errors.append(f"FSC index API: {exc}")

    if not SETTINGS.krx_auth_key:
        errors.append("KRX Open API: skipped because KRX_AUTH_KEY or KRX_API_KEY is not set.")
        return pd.DataFrame(), pd.DataFrame(), "stock-only fallback", errors

    krx_client = KrxIndexApiClient(auth_key=SETTINGS.krx_auth_key)
    try:
        raw = krx_client.fetch_range_raw(start=start, end=end, index_name="KOSPI")
        normalized = normalize_krx_index_items(raw.to_dict("records"))
        if normalized.empty:
            raise RuntimeError("KRX index response had no usable KOSPI rows.")
        return raw, normalized, "KRX Open API", errors
    except Exception as exc:  # noqa: BLE001 - stock-only 파이프라인은 계속 실행한다.
        errors.append(f"KRX Open API: {exc}")
        return pd.DataFrame(), pd.DataFrame(), "stock-only fallback", errors


def merge_stock_and_index(stock_df: pd.DataFrame, index_df: pd.DataFrame) -> pd.DataFrame:
    stock = stock_df.copy()
    if index_df.empty:
        stock["date"] = pd.to_datetime(stock["date"])
        return stock.sort_values("date").reset_index(drop=True)

    index = index_df.copy()
    stock["date"] = pd.to_datetime(stock["date"])
    index["date"] = pd.to_datetime(index["date"])
    index = index.rename(
        columns={
            "open": "index_open",
            "high": "index_high",
            "low": "index_low",
            "close": "index_close",
            "volume": "index_volume",
            "trading_value": "index_trading_value",
            "change_rate": "index_change_rate",
        }
    )
    merged = pd.merge(stock, index, on="date", how="inner", validate="one_to_one")
    return merged.sort_values("date").reset_index(drop=True)


def write_data_summary(
    ticker: str,
    dataset: pd.DataFrame,
    latest_features: pd.DataFrame,
    source: str,
    stock_raw: pd.DataFrame,
    stock_df: pd.DataFrame,
    index_df: pd.DataFrame,
    index_source: str,
    index_errors: list[str],
    merged_rows: int,
    paths: dict[str, Path],
) -> None:
    label_dist = {int(label): int(count) for label, count in dataset["label_up_5d"].value_counts(dropna=False).items()}
    missing_counts = stock_df.isna().sum()
    missing_summary = {col: int(count) for col, count in missing_counts.items() if count > 0}
    fallback_applied = index_df.empty
    merge_reduction = len(stock_df) - merged_rows
    fallback_note = (
        "KOSPI index data was unavailable, so stock-only fallback was applied. "
        "Market return features should not be interpreted as real market-relative features in this run."
        if fallback_applied
        else "KOSPI index data was joined by date; market-relative features use actual index closes."
    )
    content = f"""
# Data Summary

## Dataset

- ticker: `{ticker}`
- rows: `{len(dataset):,}`
- start: `{dataset['date'].min().date()}`
- end: `{dataset['date'].max().date()}`
- source: `{source}`
- stock raw rows: `{len(stock_raw):,}`
- stock normalized rows: `{len(stock_df):,}`
- index normalized rows: `{len(index_df):,}`
- index source: `{index_source}`
- stock/index merged rows before feature warm-up: `{merged_rows:,}`
- rows removed by inner join: `{merge_reduction:,}`
- stock-only fallback applied: `{fallback_applied}`
- latest feature date: `{latest_features['date'].max().date()}`
- index fetch warnings: `{'; '.join(index_errors) or 'none'}`

## Files

| type | path |
|---|---|
{chr(10).join(f'| {name} | `{path}` |' for name, path in paths.items())}

## Missing values in normalized stock data

```text
{missing_summary}
```

## Label distribution

```text
{label_dist}
```

## Notes

- `future_return_5d`는 label 생성 및 평가용 컬럼이다.
- `label_up_5d`와 `future_return_5d`는 모델 입력 feature에서 제외해야 한다.
- rolling feature는 장마감 후 예측을 전제로 현재일 OHLCV를 포함한다.
- `data/processed/{ticker}_latest_features.parquet`는 최신 예측용 feature이며 label 생성 가능 여부와 분리해 저장한다.
- 공공데이터포털 데이터는 일별 분석용이며 실시간 매매용 데이터가 아니다.
- {fallback_note}
- fallback에서는 `market_return_*`, `market_volatility_*`을 0으로 두고 `excess_return_*`을 같은 기간의 종목 수익률로 대체한다.
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
