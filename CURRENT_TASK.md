# CURRENT_TASK.md

## 현재 작업

Phase 1-3. KOSPI 지수 데이터 연동 및 시장 feature 정상화

## 배경

Phase 1-2에서 공공데이터포털 금융위원회 주식시세 API를 연동하여 삼성전자(`005930`) 실제 일별 시세 데이터 기반 파이프라인을 실행했다.

현재 주식 데이터 수집, feature 생성, label 생성, 학습, 평가, 백테스트, 예측은 정상 동작한다.

다만 KOSPI 지수 API 호출이 현재 인증키 기준 `403 Forbidden`으로 실패하여, 임시로 stock-only fallback을 적용했다.

현재 fallback 상태에서는:

* `market_return_1d = 0.0`
* `market_return_5d = 0.0`
* `excess_return_5d = return_5d`

로 처리되고 있다.

이 상태는 파이프라인 유지에는 유용하지만, 시장 대비 종목 움직임을 반영하지 못하므로 다음 단계에서 KOSPI 지수 데이터 연동을 정상화한다.

## 목표

삼성전자 일별 시세 데이터에 KOSPI 지수 데이터를 결합하여 시장 feature를 정상 생성한다.

최종적으로 아래 명령어가 실행되어야 한다.

```bash
python src/data_pipeline.py --ticker 005930 --start 2018-01-01 --end 2025-12-31
python src/train.py --ticker 005930
python src/evaluate.py --ticker 005930
python src/backtest.py --ticker 005930
python src/predict.py --ticker 005930
```

## 작업 범위

* `src/data_sources/krx_index_api.py`
* `src/data_sources/fsc_index_api.py`
* `src/data_pipeline.py`
* `src/features.py`
* `src/config.py`
* `reports/data_summary.md`
* `reports/model_comparison.md`
* `reports/backtest_summary.md`
* `README.md`
* `.env.example`
* `tests/`

기존 주식시세 API 연동과 샘플 데이터 파이프라인은 깨뜨리지 않는다.

## 구현 요구사항

### 1. 지수 데이터 소스 구조 정리

KOSPI 지수 데이터를 가져오는 모듈을 명확히 분리한다.

우선순위는 다음과 같다.

1. 공공데이터포털 금융위원회 지수시세정보 API
2. KRX Open API
3. 권한 또는 API 제한으로 실패할 경우 stock-only fallback 유지

가능하면 기존 `src/data_sources/krx_index_api.py` 또는 신규 `src/data_sources/fsc_index_api.py`에 구현한다.

단, 실제 API 권한이 없어서 호출이 실패할 수 있으므로, 실패 시 파이프라인 전체가 중단되지 않게 한다.

### 2. API 키 및 환경변수 정리

`.env.example`에 지수 API 관련 환경변수를 추가한다.

예시:

```env
DATA_GO_KR_SERVICE_KEY=your_service_key_here
KRX_API_KEY=your_krx_api_key_here
```

공공데이터포털 주식시세 API와 지수시세 API가 같은 인증키를 사용하는 경우에도, 코드와 문서에서 역할을 구분해 설명한다.

API 키는 로그, report, README에 절대 노출하지 않는다.

### 3. 지수 응답 정규화

지수 API 응답은 내부 표준 컬럼명으로 정규화한다.

최소 표준 컬럼은 다음과 같다.

```text
date
index_code
index_name
open
high
low
close
volume
trading_value
change_rate
```

KOSPI 지수는 내부에서 다음 값으로 관리한다.

```text
index_code = KOSPI
index_name = KOSPI
```

날짜는 `datetime`으로 변환하고, 지수 가격/거래량/거래대금 관련 컬럼은 numeric으로 변환한다.

### 4. 저장 경로

원천 지수 데이터는 아래 경로에 저장한다.

```text
data/raw/kospi_index.parquet
```

정규화된 지수 데이터는 아래 경로에 저장한다.

```text
data/interim/kospi_index_normalized.parquet
```

최종 feature/label dataset은 기존과 동일하게 저장한다.

```text
data/processed/005930_dataset.parquet
```

최신 예측용 feature도 기존과 동일하게 저장한다.

```text
data/processed/005930_latest_features.parquet
```

### 5. 주식 데이터와 지수 데이터 결합

주식 데이터와 KOSPI 지수 데이터는 `date` 기준으로 결합한다.

원칙은 다음과 같다.

* 주식 거래일과 지수 거래일이 모두 존재하는 날짜만 사용한다.
* 기본 결합 방식은 `inner join`으로 한다.
* 결합 후 날짜 오름차순으로 정렬한다.
* 결합 후 row 수가 줄어든 경우 `reports/data_summary.md`에 기록한다.
* 지수 데이터가 없거나 API 호출이 실패하면 기존 stock-only fallback을 유지한다.

### 6. 시장 feature 생성

지수 데이터가 정상 결합되면 아래 feature를 생성한다.

```text
market_return_1d
market_return_5d
market_volatility_5d
market_volatility_20d
excess_return_1d
excess_return_5d
```

정의는 다음과 같다.

```text
market_return_1d = KOSPI close 기준 1영업일 수익률
market_return_5d = KOSPI close 기준 5영업일 수익률
excess_return_1d = stock_return_1d - market_return_1d
excess_return_5d = stock_return_5d - market_return_5d
```

주의:

* `excess_return_5d`는 과거 5영업일 기준 feature여야 한다.
* label 생성에 사용하는 `future_return_5d`와 혼동하면 안 된다.
* 미래 KOSPI 수익률을 feature에 넣으면 데이터 누수다.

### 7. fallback 정책 유지

지수 API가 실패하는 경우 파이프라인은 중단하지 않는다.

대신 아래 내용을 명확히 기록한다.

* 지수 API 호출 실패 여부
* 실패 원인
* stock-only fallback 적용 여부
* market feature가 0.0 또는 종목 수익률 기준으로 대체되었는지 여부

`reports/data_summary.md`에는 다음 문구를 포함한다.

```text
KOSPI index data was unavailable, so stock-only fallback was applied. Market return features should not be interpreted as real market-relative features in this run.
```

### 8. README 업데이트

README에 다음 내용을 추가한다.

* KOSPI 지수 데이터가 왜 필요한지
* 지수 API 권한이 없을 때 fallback이 어떻게 동작하는지
* `market_return_*`, `excess_return_*` feature의 의미
* 지수 데이터가 없는 상태의 모델 결과는 시장 대비 분석으로 해석하면 안 된다는 점

### 9. 테스트 추가

아래 테스트를 추가하거나 보강한다.

* 지수 데이터가 있을 때 주식 데이터와 `date` 기준으로 정상 결합되는지
* 지수 데이터가 없을 때 stock-only fallback이 유지되는지
* `market_return_1d`, `market_return_5d`가 과거 데이터로만 계산되는지
* `future_return_5d`, `label_up_5d`가 feature 컬럼에 포함되지 않는지
* 지수 API 실패 시 API 키가 로그에 노출되지 않는지

## 완료 기준

* KOSPI 지수 API 클라이언트 또는 fallback 가능한 지수 데이터 수집 구조 구현
* `data/raw/kospi_index.parquet` 생성 가능
* `data/interim/kospi_index_normalized.parquet` 생성 가능
* 주식 데이터와 지수 데이터가 `date` 기준으로 결합 가능
* `market_return_1d`, `market_return_5d`, `excess_return_1d`, `excess_return_5d` 생성
* 지수 데이터가 없어도 기존 stock-only 파이프라인 정상 실행
* `python3 -m pytest` 통과
* README에 지수 데이터와 fallback 정책 설명 추가
* `reports/data_summary.md`에 지수 데이터 수집 여부와 결합 결과 기록
* `reports/model_comparison.md` 갱신
* `reports/backtest_summary.md` 갱신

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
python3 -m pytest
```

## 주의사항

* 지수 데이터 권한 문제를 코드로 숨기지 않는다.
* API 호출 실패를 조용히 무시하지 않는다.
* 단, 지수 데이터 실패 때문에 전체 파이프라인이 중단되지는 않게 한다.
* stock-only fallback은 임시 처리임을 report와 README에 명시한다.
* 미래 지수 수익률을 feature에 사용하지 않는다.
* `future_return_5d`, `label_up_5d`는 모델 feature에서 제외한다.
* 랜덤 split을 사용하지 않는다.
* 투자 추천 문구를 작성하지 않는다.
* 모델 성능이 낮아도 임의로 feature를 과도하게 추가하지 않는다.

## 다음 작업 후보

1. 실제 API 수집 기간이 2020년 이후부터 반환되는 이유 확인
2. Parquet cache 구조 개선
3. walk-forward validation 추가
4. KOSPI 대형주 20개로 종목 범위 확장
5. LightGBM 또는 XGBoost baseline 추가
6. 데이터 품질 검증 리포트 자동화
