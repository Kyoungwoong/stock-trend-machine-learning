# Study Note: ML 파이프라인 실행 흐름

## What I Should Learn

- 프로그램의 시작점인 CLI 파일과 실제 구현 파일을 구분하는 방법
- 데이터가 `raw → interim → processed → model → report`로 이동하는 과정
- `data_pipeline → train → evaluate → backtest → predict`를 순서대로 실행해야 하는 이유
- 실제 KOSPI, sample index, stock-only fallback 실행의 차이
- 학습 데이터와 최신 예측 데이터가 별도로 저장되는 이유

## Why It Matters

백엔드 서비스에서도 Controller, Service, Repository의 호출 순서를 먼저 이해하면 낯선 코드를 읽기 쉬워진다. 이 프로젝트도 같다. ML 수식부터 시작하기보다 한 번의 실행이 어떤 파일을 읽고 무엇을 저장하는지 이해하면, 이후 feature와 모델 코드를 어디에서 봐야 하는지 알 수 있다.

특히 ML 파이프라인은 이전 단계의 산출물을 다음 단계가 사용한다. 데이터만 다시 만들고 모델을 다시 학습하지 않으면 데이터와 모델이 서로 다른 실행에서 만들어질 수 있다. 현재 코드는 run metadata를 모델 파일에도 넣어 이런 혼동을 탐지한다.

## Key Concepts

현재 구조를 먼저 한눈에 보고 싶다면 `docs/architecture/current_architecture.md`의 계층·데이터 흐름 다이어그램부터 확인한다.

### 1. 어디가 main인가

사용자가 직접 실행하는 최초 진입점은 다음 다섯 파일이다.

| 순서 | 명령 | 최초 진입점 | 실제 구현 |
|---:|---|---|---|
| 1 | `python3 src/data_pipeline.py ...` | `src/data_pipeline.py` | `src/pipeline/data_pipeline.py` |
| 2 | `python3 src/train.py --ticker 005930` | `src/train.py` | `src/pipeline/train.py` |
| 3 | `python3 src/evaluate.py --ticker 005930` | `src/evaluate.py` | `src/pipeline/evaluate.py` |
| 4 | `python3 src/backtest.py --ticker 005930` | `src/backtest.py` | `src/pipeline/backtest.py` |
| 5 | `python3 src/predict.py --ticker 005930` | `src/predict.py` | `src/pipeline/predict.py` |

루트의 진입점은 Python import 경로를 준비하고 `src.pipeline.*.main`을 호출하는 얇은 wrapper다. 따라서 코드를 읽을 때는 다음 순서를 사용한다.

1. `src/data_pipeline.py`에서 어떤 `main`을 가져오는지 확인한다.
2. `src/pipeline/data_pipeline.py`의 `main()`과 `parse_args()`를 확인한다.
3. `main()`이 호출하는 `build_dataset()`을 읽는다.
4. `build_dataset()`이 부르는 `data_sources`, `domain`, `core` 함수로 내려간다.

### 2. 전체 실행 흐름

```text
외부 API 또는 sample 생성기
        │
        ▼
data_pipeline
  수집 → 정규화 → 날짜 병합 → feature → label
        │
        ├─ data/raw, data/interim, data/processed
        └─ reports/run_metadata.json, reports/data_summary.md
        │
        ▼
train
  날짜 분할 → 전처리 → 두 모델 학습 → validation으로 모델 선택
        ├─ models/005930_model.joblib
        └─ reports/model_comparison.md
        │
        ├───────────────┐
        ▼               ▼
evaluate              backtest
test 지표 계산         거래 규칙과 비용 계산
        │               │
        ▼               ▼
predictions.csv       backtest_summary.md
        │
        ▼
predict
최신 feature 한 행으로 상승 확률 출력
```

이 프로젝트에는 하나의 모든 단계를 실행하는 단일 `main`이 없다. 위 다섯 CLI를 순서대로 실행하는 것이 전체 파이프라인이다.

### 3. 1단계: 데이터 파이프라인

실행 예시:

```bash
python3 src/data_pipeline.py --ticker 005930 --start 2018-01-01 --end 2025-12-31 --use-sample
```

`build_dataset()`의 흐름은 다음과 같다.

1. `--use-sample`이면 합성 주식·지수 데이터를 만든다. 그렇지 않으면 FSC 주식 API를 호출한다.
2. 실제 KOSPI는 FSC 지수 API를 먼저 시도하고 실패하면 KRX를 시도한다.
3. 두 지수 API를 모두 사용할 수 없으면 stock-only fallback으로 계속 실행한다.
4. API 전용 컬럼을 프로젝트 표준 snake_case 컬럼으로 정규화한다.
5. 주식과 지수를 `date` 기준 inner join 한다. fallback이면 주식 행을 그대로 유지한다.
6. 현재일과 과거 데이터만으로 feature를 만든다.
7. 5영업일 뒤 수익률과 상승 여부 label을 만든다.
8. 학습용 dataset, 최신 예측용 feature, metadata와 요약 보고서를 저장한다.

데이터 레이어는 백엔드의 원본 요청, 내부 DTO, 업무용 read model과 비슷하다.

| 레이어 | 의미 | 대표 파일 |
|---|---|---|
| `data/raw` | API가 준 원본에 가까운 데이터 | `005930_stock_price.parquet` |
| `data/interim` | 표준 컬럼과 dtype으로 정규화한 데이터 | `005930_stock_price_normalized.parquet` |
| `data/processed` | feature와 label이 포함된 모델 입력 데이터 | `005930_dataset.parquet` |

현재 저장된 실제 KOSPI 실행은 다음 변환을 보여준다.

| 단계 | 행 수 | 설명 |
|---|---:|---|
| 정규화한 주식 | 1,473 | 2020-01-02부터 2025-12-30까지의 실제 주식 데이터 |
| 정규화한 KOSPI | 1,473 | 같은 기간의 실제 KOSPI 데이터 |
| 최신 feature | 1,414 | 60일 이동평균을 만들 수 없는 초기 구간 제거 |
| 학습 dataset | 1,409 | 마지막 5행은 미래 5영업일 label을 아직 만들 수 없어 추가 제거 |

행 수는 다음 API 실행에서 달라질 수 있다. 위 숫자는 현재 저장소 산출물의 스냅샷이지 고정 규칙이 아니다.

### 4. 2단계: 모델 학습

```bash
python3 src/train.py --ticker 005930
```

학습은 `data/processed/005930_dataset.parquet`와 `reports/run_metadata.json`을 읽는다. 데이터를 날짜순으로 정렬하고 train, validation, test로 분리한다.

- train: 모델 파라미터를 학습한다.
- validation: Logistic Regression과 Random Forest 중 하나를 선택한다.
- test: 학습할 때 건드리지 않고 `evaluate.py`에서 최종 확인한다.

선택된 모델, 전처리 Pipeline, feature 목록, 기간, metadata는 하나의 joblib artifact로 저장된다. 백엔드 관점에서는 모델 파일이 단순 실행 파일이 아니라 모델과 실행 계약을 함께 담은 배포 artifact에 가깝다.

### 5. 3단계: 평가

```bash
python3 src/evaluate.py --ticker 005930
```

평가는 test 기간에 대해 `prediction`과 `probability_up`을 만든다. accuracy 하나만 보지 않고 precision, recall, F1, ROC-AUC, confusion matrix를 함께 계산한다. 결과는 `reports/model_comparison.md`와 `reports/005930_predictions.csv`에 기록된다.

평가가 끝나면 현재 실행의 metadata에 test 지표를 추가하고, fallback과 real KOSPI 실행을 비교할 수 있도록 snapshot을 저장한다.

### 6. 4단계: 백테스트

```bash
python3 src/backtest.py --ticker 005930 --trading-cost 0.0015
```

test 기간에서 모델이 `1`을 예측한 행만 거래했다고 가정한다. 미래 5일 수익률에서 거래비용을 차감하고 평균 거래 수익률, 승률, 참고용 누적 수익률과 최대 낙폭을 계산한다.

5일 보유 거래를 매일 열 수 있어 포지션이 겹치므로 현재 누적 수익률은 실제 계좌 수익률이 아니다. 이 단계의 목적은 ML 분류 지표와 투자 성과가 서로 다른 질문이라는 점을 확인하는 것이다.

### 7. 5단계: 최신 예측

```bash
python3 src/predict.py --ticker 005930
```

학습 dataset은 마지막 5일의 label을 만들 수 없어 최신 행을 포함하지 못한다. 그래서 예측은 우선 `005930_latest_features.parquet`를 사용한다. 가장 최신 feature 한 행을 모델에 전달하고 `up` 또는 `not_up`, 상승 확률과 시장 feature 모드를 출력한다.

이 출력은 구현 검증과 학습용이며 투자 추천이 아니다.

### 8. 실행 모드 구분

| 모드 | `market_feature_mode` | 의미 |
|---|---|---|
| 실제 지수 | `real_kospi` | FSC 또는 KRX의 실제 KOSPI 종가 사용 |
| 합성 sample | `sample_index` | 파이프라인 실행 확인용 합성 데이터 사용 |
| fallback | `stock_only_fallback` | 실제 시장 feature가 없으며 시장 대비 분석 불가 |

실행 후 `reports/run_metadata.json`에서 `index_source`, `fallback_applied`, `uses_real_kospi`, `market_feature_validation_passed`를 먼저 확인해야 한다.

### 9. 추천 코드 탐색 실습

```bash
rg "def main|def build_dataset" src
rg "FEATURE_COLUMNS|LABEL_COLUMN" src
rg "future_return_5d|label_up_5d" src/domain src/pipeline tests
```

첫 번째 검색은 진입점, 두 번째는 모델의 입력 계약, 세 번째는 정답 컬럼이 어디서 만들어지고 차단되는지 보여준다.

## Related Concepts To Study Next

- pandas의 DataFrame, 정렬, merge, rolling, shift
- CLI argument parsing과 Python module/import 구조
- 학습 artifact와 재현 가능한 run metadata
- time-based split과 walk-forward validation
- feature pipeline과 label pipeline 분리

## Common Mistakes

- `src/data_pipeline.py` 안에 모든 구현이 있다고 생각하고 wrapper에서 탐색을 멈추는 것
- 데이터 파이프라인만 다시 실행한 뒤 이전 모델로 평가하거나 예측하는 것
- sample 실행 결과를 실제 삼성전자나 KOSPI 결과로 해석하는 것
- fallback의 `market_return_* = 0`을 실제 시장이 움직이지 않았다는 뜻으로 해석하는 것
- 최신 예측에 미래 label이 필요하다고 생각하는 것
- test 결과를 보고 다시 모델을 선택해 test를 사실상 validation으로 사용하는 것

## How This Appears In Our Code

- CLI 시작점: `src/data_pipeline.py`, `src/train.py`, `src/evaluate.py`, `src/backtest.py`, `src/predict.py`
- 실제 application flow: `src/pipeline/`
- feature와 label: `src/domain/features.py`, `src/domain/labeling.py`
- API와 정규화: `src/data_sources/`
- 설정, 저장, metadata: `src/core/`
- 현재 실행 문맥: `reports/run_metadata.json`
- 단계별 결과: `reports/data_summary.md`, `reports/model_comparison.md`, `reports/backtest_summary.md`

## Blog Angle

“백엔드 개발자가 ML 저장소의 main을 찾는 법”이라는 주제로 작성할 수 있다. Controller와 Service에 대응하는 CLI/pipeline 구조를 먼저 보여주고, raw 데이터가 feature, model, report로 변하는 흐름을 하나의 요청 처리 과정처럼 설명하면 ML 초보자도 전체 구조를 이해하기 쉽다.
