# CURRENT_TASK.md

## 현재 작업

Phase 1-4. 실제 KOSPI 지수 데이터 활성화 검증 및 fallback 모델 비교 (완료)

## 배경

Phase 1-3에서 KOSPI 지수 데이터 수집 구조를 구현했다.

현재 구현 상태는 다음과 같다.

* KOSPI 수집 순서: FSC 지수 API → KRX Open API → stock-only fallback
* FSC/KRX 응답을 동일한 지수 스키마로 정규화
* 주식 데이터와 지수 데이터는 `date` 기준 inner join
* `market_return_1d`, `market_return_5d`
* `market_volatility_5d`, `market_volatility_20d`
* `excess_return_1d`, `excess_return_5d`
* 지수 데이터 실패 시 stock-only fallback 유지

2026-07-17 재검증에서 FSC 지수 API가 정상 응답하여 실제 KOSPI 지수 1,473행이 모델 feature에 반영됐다.

controlled stock-only baseline과 실제 KOSPI 모델을 같은 기간으로 실행해 `reports/index_mode_comparison.md`에 결과를 기록했다.

이번 작업의 목적은 실제 KOSPI 지수 데이터가 정상 수집되는지 검증하고, 실제 지수 feature가 붙은 모델과 fallback 모델의 차이를 명확히 기록하는 것이다.

## 완료 결과

```text
index_source = fsc
index_normalized_rows = 1473
merged_rows = 1473
uses_real_kospi = true
market_feature_mode = real_kospi
market_feature_validation_passed = true
```

* stock-only accuracy: `0.4473`
* real-index accuracy: `0.4599`
* stock-only F1: `0.4781`
* real-index F1: `0.4921`
* stock-only ROC-AUC: `0.4525`
* real-index ROC-AUC: `0.4448`

단일 시간 분할 결과이므로 실제 지수 feature가 항상 성능을 개선한다고 해석하지 않는다.

## 목표

실제 KOSPI 지수 데이터가 수집 가능한 환경에서는 지수 feature가 정상 생성되어야 한다.

지수 데이터 수집이 실패하는 환경에서는 fallback이 적용되되, 그 사실이 명확하게 report에 기록되어야 한다.

최종적으로 아래 두 가지 상태를 구분할 수 있어야 한다.

```text
CASE 1. real-index mode
- KOSPI 지수 데이터 수집 성공
- index rows > 0
- market_return_* 값이 실제 KOSPI 기준으로 생성
- excess_return_* 값이 종목 수익률 - 시장 수익률로 계산

CASE 2. stock-only fallback mode
- KOSPI 지수 데이터 수집 실패
- market_return_* 값은 fallback 처리
- 결과를 시장 대비 분석으로 해석하지 않도록 report에 경고
```

## 작업 범위

* `src/pipeline/data_pipeline.py`
* `src/data_sources/fsc_index_api.py`
* `src/data_sources/krx_index_api.py`
* `src/domain/features.py`
* `src/pipeline/train.py`
* `src/pipeline/evaluate.py`
* `src/pipeline/backtest.py`
* `src/core/storage.py`
* `reports/data_summary.md`
* `reports/model_comparison.md`
* `reports/backtest_summary.md`
* `docs/logs/`
* `tests/`

## 구현 요구사항

### 1. 지수 수집 상태를 명확히 판정한다

`data_pipeline.py` 실행 후 다음 상태 중 하나를 명확히 기록한다.

```text
index_source = fsc
index_source = krx
index_source = stock_only_fallback
```

또한 아래 값을 `reports/data_summary.md`에 기록한다.

```text
stock_raw_rows
stock_normalized_rows
index_raw_rows
index_normalized_rows
merged_rows
processed_rows
index_source
fallback_applied
fallback_reason
dataset_start
dataset_end
latest_feature_date
```

### 2. 실제 KOSPI feature 활성화 여부를 검증한다

지수 데이터가 정상 수집된 경우 아래 조건을 검증한다.

```text
index_normalized_rows > 0
market_return_1d가 전부 0.0이 아님
market_return_5d가 전부 0.0이 아님
excess_return_1d != return_1d 인 row가 존재
excess_return_5d != return_5d 인 row가 존재
```

조건을 만족하지 못하면 실제 지수 feature가 활성화되지 않은 것으로 보고 report에 경고를 남긴다.

### 3. fallback 상태에서는 모델 결과를 명확히 구분한다

지수 데이터가 없는 fallback 상태에서는 `reports/model_comparison.md`와 `reports/backtest_summary.md` 상단에 다음 내용을 포함한다.

```text
This run used stock-only fallback because KOSPI index data was unavailable.
Market-relative features are not based on real KOSPI index data.
Do not interpret this result as a market-relative model comparison.
```

한국어 설명도 함께 남긴다.

```text
이번 실행은 KOSPI 지수 데이터가 없어 stock-only fallback으로 수행되었습니다.
따라서 market_return, excess_return feature는 실제 시장 대비 feature로 해석하면 안 됩니다.
```

### 4. fallback 모델과 real-index 모델 비교를 위한 run metadata를 저장한다

각 실행 결과에 metadata를 저장한다.

저장 위치 예시:

```text
reports/run_metadata.json
```

포함 항목:

```json
{
  "ticker": "005930",
  "start": "2018-01-01",
  "end": "2025-12-31",
  "data_mode": "real_api",
  "index_source": "stock_only_fallback",
  "fallback_applied": true,
  "fallback_reason": "FSC index API returned 403 and KRX_AUTH_KEY was not set",
  "model_selected": "logistic_regression",
  "test_accuracy": 0.4473,
  "test_f1": 0.4781,
  "test_roc_auc": 0.4525
}
```

단, API key 값은 절대 저장하지 않는다.

### 5. 지수 데이터 권한 설정 안내를 README에 추가한다

README에 다음 내용을 추가한다.

* `DATA_GO_KR_SERVICE_KEY`는 주식시세 API와 지수시세 API에서 사용할 수 있으나, API별 활용 신청 상태에 따라 403이 발생할 수 있음
* KRX Open API를 사용하려면 `.env`에 `KRX_AUTH_KEY` 또는 `KRX_API_KEY`를 설정해야 함
* 지수 데이터가 없으면 stock-only fallback으로 실행됨
* fallback 결과는 시장 대비 분석으로 해석하면 안 됨

예시:

```env
DATA_GO_KR_SERVICE_KEY=your_data_go_kr_service_key
KRX_AUTH_KEY=your_krx_open_api_auth_key
```

### 6. 실제 지수 데이터 수집 후 재학습 명령어를 문서화한다

README 또는 docs에 아래 흐름을 명시한다.

```bash
python3 src/data_pipeline.py --ticker 005930 --start 2018-01-01 --end 2025-12-31
python3 src/train.py --ticker 005930
python3 src/evaluate.py --ticker 005930
python3 src/backtest.py --ticker 005930
python3 src/predict.py --ticker 005930
```

그리고 결과 확인 포인트를 명시한다.

```text
reports/data_summary.md에서 index_source가 fsc 또는 krx인지 확인
index_normalized_rows가 0보다 큰지 확인
market_return_* 값이 실제로 생성되었는지 확인
reports/model_comparison.md에서 fallback 경고가 사라졌는지 확인
```

### 7. 테스트를 추가한다

아래 테스트를 추가하거나 보강한다.

* 지수 데이터가 있을 때 `index_source`가 `fsc` 또는 `krx`로 기록되는지
* 지수 데이터가 없을 때 `index_source`가 `stock_only_fallback`으로 기록되는지
* fallback 적용 시 report에 경고 문구가 포함되는지
* 실제 지수 데이터가 있을 때 `market_return_1d`, `market_return_5d`가 0으로만 채워지지 않는지
* `run_metadata.json`에 API key가 저장되지 않는지
* `future_return_5d`, `label_up_5d`가 feature column에 포함되지 않는지

## 완료 기준

* `reports/data_summary.md`에서 지수 수집 상태가 명확히 확인 가능
* `reports/run_metadata.json` 생성
* fallback 여부와 원인이 report에 기록
* 실제 KOSPI 지수 데이터 수집 성공 시 real-index mode로 판정
* 지수 수집 실패 시 stock-only fallback mode로 판정
* fallback 상태의 모델 리포트에 해석 주의 문구 포함
* README에 지수 API 권한 및 `.env` 설정 방법 추가
* `python3 -m pytest -q` 통과
* 기존 sample pipeline 유지

## 실행 확인 명령어

### 샘플 데이터 파이프라인

```bash
python3 src/data_pipeline.py --ticker 005930 --start 2018-01-01 --end 2025-12-31 --use-sample
```

### 실제 API 데이터 파이프라인

```bash
python3 src/data_pipeline.py --ticker 005930 --start 2018-01-01 --end 2025-12-31
```

### 학습

```bash
python3 src/train.py --ticker 005930
```

### 평가

```bash
python3 src/evaluate.py --ticker 005930
```

### 백테스트

```bash
python3 src/backtest.py --ticker 005930
```

### 최신 예측

```bash
python3 src/predict.py --ticker 005930
```

### 테스트

```bash
python3 -m pytest -q
python3 -m compileall -q src tests
```

## 주의사항

* API key를 report, log, README, metadata에 노출하지 않는다.
* 지수 데이터 실패를 조용히 숨기지 않는다.
* fallback은 허용하되 fallback 결과를 실제 시장 대비 모델로 해석하지 않는다.
* 모델 성능이 낮다고 해서 feature를 과도하게 추가하지 않는다.
* LightGBM, XGBoost, PyTorch는 이번 작업에서 도입하지 않는다.
* KOSPI 대형주 20개 확장은 이번 작업에서 하지 않는다.
* walk-forward validation은 다음 단계 후보로 남긴다.
* `future_return_5d`, `label_up_5d`는 모델 입력 feature에서 제외한다.
* 날짜 기준 split을 유지한다.
* `train_test_split(shuffle=True)`는 사용하지 않는다.
* 투자 추천 문구를 작성하지 않는다.

## 다음 작업 후보

1. KRX 장기 일별 호출을 위한 Parquet cache 및 증분 수집
2. 실제 KOSPI 지수 feature 기반 모델과 fallback 모델 성능 비교
3. walk-forward validation 추가
4. 데이터 품질 검증 리포트 자동화
5. LightGBM 또는 XGBoost baseline 추가
6. KOSPI 대형주 20개 확장
