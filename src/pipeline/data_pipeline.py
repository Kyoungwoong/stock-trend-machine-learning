from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from src.core.config import SETTINGS
from src.core.run_metadata import RunMetadata, build_run_metadata, redact_secrets, write_run_metadata
from src.core.storage import save_parquet, write_report
from src.data_sources.fsc_index_api import FscIndexApiClient, normalize_index_items
from src.data_sources.fsc_stock_api import FscStockApiClient, normalize_stock_price_items
from src.data_sources.krx_index_api import KrxIndexApiClient, normalize_krx_index_items
from src.domain.features import FEATURE_COLUMNS, add_price_features
from src.domain.labeling import add_forward_return_label, drop_unlabeled_rows
from src.domain.sample_data import generate_sample_index, generate_sample_stock


def build_dataset(ticker: str, start: str, end: str, use_sample: bool, force_stock_only: bool = False) -> pd.DataFrame:
    raw_dir = SETTINGS.data_dir / "raw"
    interim_dir = SETTINGS.data_dir / "interim"
    processed_dir = SETTINGS.data_dir / "processed"
    source = "sample synthetic data" if use_sample else "public API data"

    if use_sample and force_stock_only:
        raise ValueError("--use-sample and --force-stock-only cannot be used together.")

    if use_sample:
        stock_df = generate_sample_stock(ticker=ticker, start=start, end=end)
        index_df = generate_sample_index(index_name="KOSPI_SAMPLE", start=start, end=end)
        stock_raw = stock_df.copy()
        index_raw = index_df.copy()
        index_source = "sample"
        index_errors: list[str] = []
    else:
        if not SETTINGS.data_go_kr_service_key:
            raise RuntimeError("DATA_GO_KR_SERVICE_KEY is required. Set it in .env or run with --use-sample.")
        stock_client = FscStockApiClient(service_key=SETTINGS.data_go_kr_service_key)
        stock_raw = stock_client.fetch_range_raw(start=start, end=end, ticker=ticker)
        stock_df = normalize_stock_price_items(stock_raw.to_dict("records"))
        if force_stock_only:
            index_raw = pd.DataFrame()
            index_df = pd.DataFrame()
            index_source = "stock_only_fallback"
            index_errors = ["Stock-only baseline was explicitly requested with --force-stock-only."]
        else:
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
    fallback_applied = index_df.empty
    fallback_reason = "; ".join(index_errors) if fallback_applied else None
    if not index_df.empty and merged.empty:
        fallback_reason = "KOSPI index data had no trading dates overlapping the stock data."
        index_errors.append(fallback_reason)
        merged = merge_stock_and_index(stock_df, pd.DataFrame())
        index_source = "stock_only_fallback"
        fallback_applied = True

    featured = add_price_features(merged)
    market_feature_validation_passed = validate_market_features(featured, expect_real_index=not use_sample and not fallback_applied)
    if not market_feature_validation_passed and not use_sample and not fallback_applied:
        fallback_reason = "Normalized KOSPI rows were present, but real market feature validation failed."
        index_errors.append(fallback_reason)
        index_source = "stock_only_fallback"
        fallback_applied = True
        merged = merge_stock_and_index(stock_df, pd.DataFrame())
        featured = add_price_features(merged)
    if fallback_applied and not use_sample:
        source = "public API data (stock only; KOSPI index unavailable)"
    latest_features = featured.dropna(subset=FEATURE_COLUMNS).reset_index(drop=True)
    labeled = add_forward_return_label(featured, horizon=5)
    dataset = drop_unlabeled_rows(labeled).dropna(subset=FEATURE_COLUMNS).reset_index(drop=True)

    output_path = processed_dir / f"{ticker}_dataset.parquet"
    latest_path = processed_dir / f"{ticker}_latest_features.parquet"
    save_parquet(dataset, output_path)
    save_parquet(latest_features, latest_path)
    metadata = build_run_metadata(
        ticker=ticker,
        start=start,
        end=end,
        use_sample=use_sample,
        index_source=index_source,
        fallback_applied=fallback_applied,
        fallback_reason=fallback_reason,
        index_normalized_rows=len(index_df),
        merged_rows=len(merged),
        stock_raw_rows=len(stock_raw),
        stock_normalized_rows=len(stock_df),
        index_raw_rows=len(index_raw),
        dataset_rows=len(dataset),
        dataset_start=str(dataset["date"].min().date()),
        dataset_end=str(dataset["date"].max().date()),
        latest_feature_date=str(latest_features["date"].max().date()),
        index_fetch_warnings=index_errors,
        market_feature_validation_passed=market_feature_validation_passed,
    )
    metadata_path = SETTINGS.report_dir / "run_metadata.json"
    write_run_metadata(metadata_path, metadata)
    write_data_summary(
        ticker=ticker,
        dataset=dataset,
        latest_features=latest_features,
        source=source,
        stock_raw=stock_raw,
        stock_df=stock_df,
        metadata=metadata,
        paths={
            "stock_raw": stock_raw_path,
            "stock_normalized": stock_normalized_path,
            "index_raw": index_raw_path,
            "index_normalized": index_normalized_path,
            "dataset": output_path,
            "latest_features": latest_path,
            "run_metadata": metadata_path,
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
        return raw, normalized, "fsc", errors
    except Exception as exc:  # noqa: BLE001 - 다음 데이터 소스를 시도하고 원인은 report에 남긴다.
        errors.append(f"FSC index API: {_safe_api_error(exc)}")

    if not SETTINGS.krx_auth_key:
        errors.append("KRX Open API: skipped because KRX_AUTH_KEY or KRX_API_KEY is not set.")
        return pd.DataFrame(), pd.DataFrame(), "stock_only_fallback", errors

    krx_client = KrxIndexApiClient(auth_key=SETTINGS.krx_auth_key)
    try:
        raw = krx_client.fetch_range_raw(start=start, end=end, index_name="KOSPI")
        normalized = normalize_krx_index_items(raw.to_dict("records"))
        if normalized.empty:
            raise RuntimeError("KRX index response had no usable KOSPI rows.")
        return raw, normalized, "krx", errors
    except Exception as exc:  # noqa: BLE001 - stock-only 파이프라인은 계속 실행한다.
        errors.append(f"KRX Open API: {_safe_api_error(exc)}")
        return pd.DataFrame(), pd.DataFrame(), "stock_only_fallback", errors


def _safe_api_error(exc: Exception) -> str:
    return redact_secrets(
        str(exc),
        [SETTINGS.data_go_kr_service_key, SETTINGS.krx_auth_key],
    )


def validate_market_features(featured: pd.DataFrame, expect_real_index: bool) -> bool:
    if not expect_real_index:
        return False

    checks = [
        featured["market_return_1d"].dropna().ne(0).any(),
        featured["market_return_5d"].dropna().ne(0).any(),
        (featured["excess_return_1d"] - featured["return_1d"]).dropna().ne(0).any(),
        (featured["excess_return_5d"] - featured["return_5d"]).dropna().ne(0).any(),
    ]
    return all(bool(check) for check in checks)


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
    metadata: RunMetadata,
    paths: dict[str, Path],
) -> None:
    label_dist = {int(label): int(count) for label, count in dataset["label_up_5d"].value_counts(dropna=False).items()}
    missing_counts = stock_df.isna().sum()
    missing_summary = {col: int(count) for col, count in missing_counts.items() if count > 0}
    fallback_applied = metadata.fallback_applied
    merge_reduction = len(stock_df) - metadata.merged_rows
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
- stock raw rows: `{metadata.stock_raw_rows:,}`
- stock normalized rows: `{metadata.stock_normalized_rows:,}`
- index raw rows: `{metadata.index_raw_rows:,}`
- index normalized rows: `{metadata.index_normalized_rows:,}`
- index source: `{metadata.index_source}`
- stock/index merged rows before feature warm-up: `{metadata.merged_rows:,}`
- rows removed by inner join: `{merge_reduction:,}`
- stock-only fallback applied: `{fallback_applied}`
- fallback reason: `{metadata.fallback_reason or 'none'}`
- uses real KOSPI: `{metadata.uses_real_kospi}`
- market feature mode: `{metadata.market_feature_mode}`
- market feature validation passed: `{metadata.market_feature_validation_passed}`
- latest feature date: `{latest_features['date'].max().date()}`
- processed rows: `{metadata.dataset_rows:,}`
- dataset start: `{metadata.dataset_start}`
- dataset end: `{metadata.dataset_end}`
- index fetch warnings: `{'; '.join(metadata.index_fetch_warnings) or 'none'}`

## Index Application Status

| field | value |
|---|---|
| index_source | `{metadata.index_source}` |
| fallback_applied | `{metadata.fallback_applied}` |
| fallback_reason | `{metadata.fallback_reason}` |
| index_normalized_rows | `{metadata.index_normalized_rows}` |
| merged_rows | `{metadata.merged_rows}` |
| uses_real_kospi | `{metadata.uses_real_kospi}` |
| market_feature_mode | `{metadata.market_feature_mode}` |

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
    parser.add_argument("--force-stock-only", action="store_true", help="Create a controlled stock-only comparison baseline.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    dataset = build_dataset(
        ticker=args.ticker,
        start=args.start,
        end=args.end,
        use_sample=args.use_sample,
        force_stock_only=args.force_stock_only,
    )
    output_path = Path(SETTINGS.data_dir) / "processed" / f"{args.ticker}_dataset.parquet"
    print(f"Dataset saved: {output_path} rows={len(dataset):,}")


if __name__ == "__main__":
    main()
