# Data Summary

## Dataset

- ticker: `005930`
- rows: `1,409`
- start: `2020-03-27`
- end: `2025-12-22`
- source: `public API data (stock: FSC, index: fsc)`
- stock raw rows: `1,473`
- stock normalized rows: `1,473`
- index raw rows: `1,473`
- index normalized rows: `1,473`
- index source: `fsc`
- stock/index merged rows before feature warm-up: `1,473`
- rows removed by inner join: `0`
- stock-only fallback applied: `False`
- fallback reason: `none`
- uses real KOSPI: `True`
- market feature mode: `real_kospi`
- market feature validation passed: `True`
- latest feature date: `2025-12-30`
- processed rows: `1,409`
- dataset start: `2020-03-27`
- dataset end: `2025-12-22`
- index fetch warnings: `none`

## Index Application Status

| field | value |
|---|---|
| index_source | `fsc` |
| fallback_applied | `False` |
| fallback_reason | `None` |
| index_normalized_rows | `1473` |
| merged_rows | `1473` |
| uses_real_kospi | `True` |
| market_feature_mode | `real_kospi` |

## Files

| type | path |
|---|---|
| stock_raw | `data/raw/005930_stock_price.parquet` |
| stock_normalized | `data/interim/005930_stock_price_normalized.parquet` |
| index_raw | `data/raw/kospi_index.parquet` |
| index_normalized | `data/interim/kospi_index_normalized.parquet` |
| dataset | `data/processed/005930_dataset.parquet` |
| latest_features | `data/processed/005930_latest_features.parquet` |
| run_metadata | `reports/run_metadata.json` |

## Missing values in normalized stock data

```text
{}
```

## Label distribution

```text
{1: 716, 0: 693}
```

## Notes

- `future_return_5d`는 label 생성 및 평가용 컬럼이다.
- `label_up_5d`와 `future_return_5d`는 모델 입력 feature에서 제외해야 한다.
- rolling feature는 장마감 후 예측을 전제로 현재일 OHLCV를 포함한다.
- `data/processed/005930_latest_features.parquet`는 최신 예측용 feature이며 label 생성 가능 여부와 분리해 저장한다.
- 공공데이터포털 데이터는 일별 분석용이며 실시간 매매용 데이터가 아니다.
- KOSPI index data was joined by date; market-relative features use actual index closes.
- fallback에서는 `market_return_*`, `market_volatility_*`을 0으로 두고 `excess_return_*`을 같은 기간의 종목 수익률로 대체한다.
- 샘플 데이터는 실제 삼성전자/KOSPI 시장 데이터가 아니며 파이프라인 검증용 합성 데이터다.
