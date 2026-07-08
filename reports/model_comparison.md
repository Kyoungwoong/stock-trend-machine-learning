# Model Comparison

## Training Split

| split | rows | start | end |
|---|---:|---|---|
| train | 1,506 | 2018-03-23 | 2023-12-29 |
| validation | 262 | 2024-01-01 | 2024-12-31 |
| test | 256 | 2025-01-01 | 2025-12-24 |

## Validation Accuracy

| model | validation accuracy |
|---|---:|
| logistic_regression | 0.4313 |
| random_forest | 0.3931 |

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
- test period: `2025-01-01` ~ `2025-12-24`

### Metrics

| metric | value |
|---|---:|
| accuracy | 0.4648 |
| precision | 0.4136 |
| recall | 0.9192 |
| f1 | 0.5705 |
| roc_auc | 0.5045 |

### Confusion Matrix

```text
[[ 28 129]
 [  8  91]]
```

### Prediction file

`reports/005930_predictions.csv`

### Notes

- ML 지표는 방향성 분류 성능을 보여준다.
- 실제 투자 성과는 `backtest.py`에서 별도로 확인한다.
- 평가는 날짜 순서 split의 test 구간에서만 수행한다.
