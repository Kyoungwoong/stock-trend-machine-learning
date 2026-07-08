# Phase 1-2 공공데이터포털 실제 API 연동 작업 로그

작성일: 2026-07-09

## 작업 목적

샘플 데이터가 아니라 `.env`의 `DATA_GO_KR_SERVICE_KEY`를 사용해 공공데이터포털 금융위원회 주식시세 API에서 삼성전자(`005930`) 일별 시세를 수집하고, 기존 feature/label/train/evaluate/backtest/predict 흐름을 유지한다.

## 구현 요약

### API 키 처리

- `.env`의 `DATA_GO_KR_SERVICE_KEY`를 `src/config.py`에서 읽는 기존 구조를 그대로 사용했다.
- API 키가 없고 `--use-sample`도 아니면 명확한 에러를 내도록 했다.
- API 키는 코드, README, report에 노출하지 않는다.
- 공공데이터포털 인증키가 URL encoded 형태일 수 있어 API 요청 직전에 `unquote()`로 처리한다.

### 주식시세 API 연동

- `src/data_sources/fsc_stock_api.py`에 실제 HTTP 호출 로직을 보강했다.
- `beginBasDt`, `endBasDt`, `likeSrtnCd`를 사용해 날짜별 반복 호출 대신 기간 조회로 수집한다.
- pagination을 처리한다.
- HTTP/API 오류를 명확히 출력하되, service key가 URL에 노출되지 않도록 에러 메시지를 정리했다.
- 원천 응답과 정규화 데이터를 분리한다.

### 정규화 컬럼

| API column | Standard column |
|---|---|
| `basDt` | `date` |
| `srtnCd` | `ticker` |
| `itmsNm` | `name` |
| `mrktCtg` | `market` |
| `mkp` | `open` |
| `hipr` | `high` |
| `lopr` | `low` |
| `clpr` | `close` |
| `trqu` | `volume` |
| `trPrc` | `trading_value` |
| `lstgStCnt` | `listed_shares` |
| `mrktTotAmt` | `market_cap` |
| `fltRt` | `change_rate` |

날짜는 pandas datetime으로 변환하고, 가격/거래량/거래대금/시가총액 관련 값은 numeric으로 변환한다.

## 저장 경로

| 단계 | 파일 |
|---|---|
| raw stock | `data/raw/005930_stock_price.parquet` |
| normalized stock | `data/interim/005930_stock_price_normalized.parquet` |
| processed dataset | `data/processed/005930_dataset.parquet` |
| latest features | `data/processed/005930_latest_features.parquet` |

지수 API도 호출을 시도했지만, 현재 키에서는 지수시세 API가 `403 Forbidden`으로 실패했다. 이 경우 pipeline은 stock-only 모드로 계속 실행하고, `reports/data_summary.md`에 경고를 남긴다.

## 지수 API 실패 시 fallback

- KOSPI 지수 수집 실패 시 주식 데이터만으로 파이프라인을 계속 실행한다.
- `market_return_1d`, `market_return_5d`는 `0.0`으로 둔다.
- `excess_return_5d`는 종목의 `return_5d`와 동일하게 둔다.
- 이 fallback은 임시 처리이며, KOSPI 지수 API 권한 확보 후 제거 또는 재검토해야 한다.

## 실행 결과

### 샘플 데이터 파이프라인

```bash
python3 src/data_pipeline.py --ticker 005930 --start 2018-01-01 --end 2025-12-31 --use-sample
```

```text
Dataset saved: data/processed/005930_dataset.parquet rows=2,024
```

### 실제 API 데이터 파이프라인

```bash
python3 src/data_pipeline.py --ticker 005930 --start 2018-01-01 --end 2025-12-31
```

```text
Dataset saved: data/processed/005930_dataset.parquet rows=1,409
```

데이터 요약:

- source: `public API data (stock only; KOSPI index unavailable)`
- stock raw rows: `1,473`
- stock normalized rows: `1,473`
- index normalized rows: `0`
- dataset rows: `1,409`
- dataset start: `2020-03-27`
- dataset end: `2025-12-22`
- latest feature date: `2025-12-30`
- label distribution: `{1: 716, 0: 693}`

### 학습

```bash
python3 src/train.py --ticker 005930
```

```text
Model saved: models/005930_model.joblib selected=logistic_regression
```

validation accuracy:

- logistic_regression: `0.5451`
- random_forest: `0.5287`

### 평가

test period: `2025-01-02` ~ `2025-12-22`

| metric | value |
|---|---:|
| accuracy | 0.4473 |
| precision | 0.5660 |
| recall | 0.4138 |
| f1 | 0.4781 |
| roc_auc | 0.4528 |

confusion matrix:

```text
[[46 46]
 [85 60]]
```

### 백테스트

| metric | value |
|---|---:|
| test_rows | 237 |
| trade_count | 106 |
| avg_strategy_trade_return | 0.0078 |
| win_rate | 0.5660 |
| strategy_total_return_reference | 1.0591 |
| buy_and_hold_return | 1.0693 |
| strategy_max_drawdown_reference | -0.4551 |
| buy_and_hold_max_drawdown | -0.1467 |
| trading_cost_per_trade | 0.0015 |

주의:

- 이 백테스트는 교육용 단순 백테스트다.
- 5영업일 보유 거래가 매일 겹칠 수 있어 실제 포트폴리오 수익률로 해석하면 안 된다.
- 투자 추천이나 매매 신호가 아니다.

### 최신 예측

```bash
python3 src/predict.py --ticker 005930
```

```text
date,ticker,prediction,probability,feature_source
2025-12-30,005930,not_up,0.0459,data/processed/005930_latest_features.parquet
```

## 테스트

```bash
python3 -m pytest
```

```text
6 passed
```

확인한 테스트:

- feature 컬럼에 `label_up_5d`, `future_return_5d`가 포함되지 않음
- 지수 데이터가 없을 때 stock-only market feature fallback 동작
- 주식시세 API 응답 컬럼 정규화
- label 생성 시 마지막 horizon 구간 label 제외

## 데이터 누수 방지 처리

- `future_return_5d`는 label 생성, 평가, 백테스트용으로만 사용한다.
- `label_up_5d`, `future_return_5d`는 모델 입력 feature에서 제외한다.
- rolling feature는 장마감 후 예측을 전제로 현재일 OHLCV를 포함한다고 명시했다.
- train/validation/test는 날짜 순서 기준으로 분리한다.
- `train_test_split(shuffle=True)`는 사용하지 않는다.
- API raw 응답과 모델 입력용 normalized/interim 데이터를 분리 저장한다.

## 남은 TODO

- 공공데이터포털 금융위원회_지수시세정보 API 활용신청 또는 권한 활성화 확인.
- KOSPI 지수 데이터가 정상 수집되면 stock-only fallback 성능과 비교.
- 실제 API 수집 기간이 2020년 이후부터 반환되는 이유 확인.
- API 응답 스키마 변경 시 `reports/data_summary.md`에 자동 기록 강화.
- API 호출 캐시 또는 Parquet cache 구조 개선.
- walk-forward validation 추가.
