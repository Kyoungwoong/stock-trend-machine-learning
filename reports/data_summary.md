# Data Summary

## Dataset

- ticker: `005930`
- rows: `2,024`
- start: `2018-03-23`
- end: `2025-12-24`
- source: `sample synthetic data`
- latest feature date: `2025-12-31`

## Label distribution

```text
{0: 1087, 1: 937}
```

## Notes

- `future_return_5d`는 label 생성 및 평가용 컬럼이다.
- `label_up_5d`와 `future_return_5d`는 모델 입력 feature에서 제외해야 한다.
- rolling feature는 장마감 후 예측을 전제로 현재일 OHLCV를 포함한다.
- `data/processed/005930_latest_features.parquet`는 최신 예측용 feature이며 label 생성 가능 여부와 분리해 저장한다.
- 샘플 데이터는 실제 삼성전자/KOSPI 시장 데이터가 아니며 파이프라인 검증용 합성 데이터다.
