# Model Comparison

## Data Context

| field | value |
|---|---|
| index_source | `fsc` |
| fallback_applied | `False` |
| fallback_reason | `None` |
| index_normalized_rows | `1473` |
| merged_rows | `1473` |
| uses_real_kospi | `True` |
| market_feature_mode | `real_kospi` |

This run used real KOSPI index data. 실제 KOSPI 지수가 날짜 기준으로 결합되었습니다.

## Training Split

| split | rows | start | end |
|---|---:|---|---|
| train | 928 | 2020-03-27 | 2023-12-28 |
| validation | 244 | 2024-01-02 | 2024-12-30 |
| test | 237 | 2025-01-02 | 2025-12-22 |

## Validation Accuracy

| model | validation accuracy |
|---|---:|
| logistic_regression | 0.5328 |
| random_forest | 0.5041 |

## Selected model

`logistic_regression`

## Notes

- validation accuracy는 모델 선택용 참고 지표다.
- 최종 평가는 `evaluate.py`에서 test set 기준으로 수행한다.
- `label_up_5d`와 `future_return_5d`는 모델 입력 feature에서 제외했다.
- split은 날짜 순서를 기준으로 하며 랜덤 shuffle을 사용하지 않는다.

## Test Evaluation


### Model

- ticker: `005930`
- selected model: `logistic_regression`
- test period: `2025-01-02` ~ `2025-12-22`

### Metrics

| metric | value |
|---|---:|
| accuracy | 0.4599 |
| precision | 0.5794 |
| recall | 0.4276 |
| f1 | 0.4921 |
| roc_auc | 0.4448 |

### Confusion Matrix

```text
[[47 45]
 [83 62]]
```

### Prediction file

`reports/005930_predictions.csv`

### Notes

- ML 지표는 방향성 분류 성능을 보여준다.
- 실제 투자 성과는 `backtest.py`에서 별도로 확인한다.
- 평가는 날짜 순서 split의 test 구간에서만 수행한다.
