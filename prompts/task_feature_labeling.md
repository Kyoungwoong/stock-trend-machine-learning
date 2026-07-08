# Task Prompt: feature와 label 생성

## 목표

삼성전자 일별 시세와 KOSPI 지수를 병합한 데이터에서 향후 5영업일 상승 여부 label과 기초 feature를 생성한다.

## 수정 대상

- `src/features.py`
- `src/labeling.py`
- `src/data_pipeline.py`
- `tests/test_labeling.py`
- `tests/test_features.py`

## Feature 목록

- `return_1d`
- `return_3d`
- `return_5d`
- `return_20d`
- `ma_5`
- `ma_20`
- `ma_60`
- `close_vs_ma5`
- `close_vs_ma20`
- `close_vs_ma60`
- `volume_change_1d`
- `volume_ma_5`
- `volume_ma_20`
- `volatility_5d`
- `volatility_20d`
- `market_return_1d`
- `market_return_5d`
- `excess_return_5d`

## Label 정의

```text
future_return_5d = close.shift(-5) / close - 1
label_up_5d = 1 if future_return_5d > 0 else 0
```

## 주의사항

- `future_return_5d`는 feature가 아니다.
- `label_up_5d`는 feature가 아니다.
- 현재 프로젝트는 장마감 후 예측이므로 현재일 종가를 사용하는 rolling feature는 허용한다.
- 마지막 5개 행은 label이 없으므로 학습에서 제외한다.
