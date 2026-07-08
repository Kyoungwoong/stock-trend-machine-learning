# Data Summary

## Dataset

- ticker: `005930`
- rows: `1,409`
- start: `2020-03-27`
- end: `2025-12-22`
- source: `public API data (stock only; KOSPI index unavailable)`
- stock raw rows: `1,473`
- stock normalized rows: `1,473`
- index normalized rows: `0`
- latest feature date: `2025-12-30`
- index fetch warning: `Public data API HTTP error status=403 endpoint=/1160100/service/GetMarketIndexInfoService/getStockMarketIndex`

## Files

| type | path |
|---|---|
| stock_raw | `data/raw/005930_stock_price.parquet` |
| stock_normalized | `data/interim/005930_stock_price_normalized.parquet` |
| index_raw | `data/raw/kospi_index.parquet` |
| index_normalized | `data/interim/kospi_index_normalized.parquet` |
| dataset | `data/processed/005930_dataset.parquet` |
| latest_features | `data/processed/005930_latest_features.parquet` |

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
- KOSPI 지수가 수집되지 않은 경우 `market_return_*`은 0, `excess_return_5d`는 종목 5일 수익률로 대체한다.
- 샘플 데이터는 실제 삼성전자/KOSPI 시장 데이터가 아니며 파이프라인 검증용 합성 데이터다.
