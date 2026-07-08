# CURRENT_TASK.md

## 현재 작업

Phase 1-2. 공공데이터포털 주식시세 API를 연동하여 삼성전자 실제 일별 시세 데이터를 수집한다.

## 목표

샘플 데이터가 아니라 실제 공개 API 데이터를 사용해 아래 명령어가 실행되어야 한다.

```bash
python src/data_pipeline.py --ticker 005930 --start 2018-01-01 --end 2025-12-31
python src/train.py --ticker 005930
python src/evaluate.py --ticker 005930
python src/backtest.py --ticker 005930
python src/predict.py --ticker 005930
```

## 작업 범위

* `src/config.py`
* `src/data_sources/fsc_stock_api.py`
* `src/data_pipeline.py`
* `src/features.py`
* `src/labeling.py`
* `.env.example`
* `README.md`
* `reports/data_summary.md`

## 구현 요구사항

### 1. API 키 관리

`.env` 파일에서 공공데이터포털 API 키를 읽도록 구현한다.

필요한 환경변수 예시:

```env
DATA_GO_KR_SERVICE_KEY=your_service_key_here
```

API 키가 없을 경우에는 명확한 에러 메시지를 출력한다.

단, `--use-sample` 옵션을 사용하는 경우에는 API 키가 없어도 실행되어야 한다.

### 2. 실제 주식시세 API 클라이언트 구현

`src/data_sources/fsc_stock_api.py`에 공공데이터포털 주식시세정보 API 호출 로직을 구현한다.

수집 대상 컬럼은 최소한 아래 항목을 포함한다.

* 기준일자
* 종목코드
* 종목명
* 시장구분
* 시가
* 고가
* 저가
* 종가
* 거래량
* 거래대금
* 상장주식수
* 시가총액
* 등락률

### 3. API 응답 스키마 정규화

API 응답 컬럼명이 한글/영문/축약명으로 오더라도 내부에서는 아래 표준 컬럼명으로 변환한다.

```text
date
ticker
name
market
open
high
low
close
volume
trading_value
listed_shares
market_cap
change_rate
```

모든 날짜는 `datetime`으로 변환하고, 가격/거래량/시가총액 관련 컬럼은 숫자형으로 변환한다.

### 4. 원천 데이터 저장

API에서 받은 원천 데이터는 아래 경로에 저장한다.

```text
data/raw/005930_stock_price.parquet
```

정규화된 중간 데이터는 아래 경로에 저장한다.

```text
data/interim/005930_stock_price_normalized.parquet
```

최종 feature/label dataset은 기존과 동일하게 저장한다.

```text
data/processed/005930_dataset.parquet
```

### 5. 기존 파이프라인 유지

실제 API 연동 후에도 아래 명령어는 계속 정상 실행되어야 한다.

```bash
python src/data_pipeline.py --ticker 005930 --start 2018-01-01 --end 2025-12-31 --use-sample
```

즉, 샘플 데이터 실행 경로를 깨뜨리면 안 된다.

## 완료 기준

* `.env`에서 API 키를 읽을 수 있음
* `--use-sample` 없이 실제 API 데이터 수집 가능
* `data/raw/005930_stock_price.parquet` 생성
* `data/interim/005930_stock_price_normalized.parquet` 생성
* `data/processed/005930_dataset.parquet` 생성
* 기존 train/evaluate/backtest/predict 명령어 실행 가능
* README에 실제 API 사용 방법 추가
* reports/data_summary.md에 수집 기간, row 수, 결측치 수, 최신 기준일자 기록

## 주의사항

* API 데이터는 실시간 매매용 데이터로 설명하지 않는다.
* 공공데이터포털 주식시세정보는 일별 분석용 데이터로만 사용한다.
* 미래 데이터를 feature에 섞지 않는다.
* label 계산 시 향후 5영업일 종가를 사용하되, 해당 컬럼은 feature에서 제외한다.
* API 원본 응답과 모델 입력용 정규화 데이터를 구분해서 저장한다.
* API 호출 실패 시 조용히 넘어가지 말고 원인을 알 수 있게 에러를 출력한다.
* 투자 추천 문구를 작성하지 않는다.

## 다음 작업 후보

1. KOSPI 지수 데이터 수집
2. 종목 수익률과 시장 수익률 비교 feature 추가
3. Parquet 캐시 구조 개선
4. API 호출 pagination 처리 고도화
5. 데이터 품질 검증 리포트 자동화
