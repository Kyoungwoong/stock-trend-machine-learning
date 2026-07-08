# vibe-stock-trend-ml

공공/공개 금융 데이터를 수집해 **향후 5영업일 주가 방향성**을 예측하는 머신러닝 프로젝트입니다.

이 프로젝트의 핵심은 “주식 맞히는 AI”가 아니라, 실제 공개 데이터를 사용해 데이터 수집 → feature 생성 → label 생성 → 시간 순서 기반 검증 → 간단한 백테스트까지 연결되는 **주식 ML 파이프라인을 직접 만드는 것**입니다.

## 1. 문제 정의

오늘 장 마감 시점까지 알 수 있는 데이터로, 해당 종목의 **향후 5영업일 수익률이 0%보다 클지** 예측합니다.

- 문제 유형: 이진 분류
- 입력값 X: 오늘까지의 주가, 거래량, 변동성, 이동평균, 시장지수, 거래대금 등
- 예측값 y: 향후 5영업일 수익률이 0%보다 큰가?

```text
label = 1  : 향후 5영업일 수익률 > 0%
label = 0  : 향후 5영업일 수익률 <= 0%
```

## 2. 1차 범위

처음부터 전체 종목, 뉴스 NLP, 딥러닝, 실시간 자동매매까지 넣지 않습니다.

1차 목표는 아래로 고정합니다.

- 대상 종목: 삼성전자 `005930`
- 예측 대상: 향후 5영업일 상승 여부
- 데이터: 개별 종목 일별 OHLCV + KOSPI 지수
- 모델: LogisticRegression, RandomForest
- 검증: 시간 순서 기반 train/validation/test split
- 추가 검증: 모델이 상승이라고 예측한 날만 매수하는 단순 백테스트

## 3. 데이터 출처

### 1차

- 공공데이터포털 금융위원회_주식시세정보
- 공공데이터포털 금융위원회_지수시세정보 또는 KRX Open API 지수 데이터

### 2차

- 금융투자협회 통계: CMA 잔고, 신용공여 잔고 등 시장자금 지표
- OpenDART: 정기보고서 재무정보
- 한국은행 ECOS: 금리, 환율, 물가 등 거시경제 지표

## 4. 설치

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

공공데이터포털 API 키가 아직 없어도 `--use-sample` 옵션으로 전체 흐름을 먼저 실행할 수 있습니다.
`--use-sample` 데이터는 실제 삼성전자/KOSPI 시세가 아니라 실행 흐름 검증용 합성 데이터입니다.

## 5. 실행 예시

### 샘플 데이터로 전체 파이프라인 확인

```bash
python src/data_pipeline.py --ticker 005930 --start 2018-01-01 --end 2025-12-31 --use-sample
python src/train.py --ticker 005930
python src/evaluate.py --ticker 005930
python src/backtest.py --ticker 005930
python src/predict.py --ticker 005930
```

### 실제 API 데이터 사용

`.env`에 공공데이터포털 인증키를 넣은 후 실행합니다. API 키는 코드에 하드코딩하지 않습니다.

```text
DATA_GO_KR_SERVICE_KEY=...
KRX_AUTH_KEY=...
DART_API_KEY=...
BOK_ECOS_API_KEY=...
```

```bash
python src/data_pipeline.py --ticker 005930 --start 2018-01-01 --end 2025-12-31
```

실제 API 실행 시 공공데이터포털 금융위원회_주식시세정보와 금융위원회_지수시세정보를 호출합니다. 원천 응답은 `data/raw/`, 내부 표준 컬럼명으로 정규화한 데이터는 `data/interim/`, feature/label 학습 데이터는 `data/processed/`에 저장합니다.

공공데이터포털 주식시세정보는 일별 분석용 데이터이며 실시간 매매용 데이터가 아닙니다. 기준일자 다음 영업일 오후 1시 이후 갱신될 수 있으므로 최신일 데이터는 비어 있을 수 있습니다.
지수시세정보 API 권한이 없거나 호출이 실패하면 주식시세 데이터만으로 파이프라인을 계속 실행하고, 해당 사유를 `reports/data_summary.md`에 기록합니다.

## 6. 산출물

- `data/processed/{ticker}_dataset.parquet`: 학습용 feature + label 데이터셋
- `data/processed/{ticker}_latest_features.parquet`: label 생성 가능 여부와 분리한 최신 예측용 feature 데이터셋
- `data/raw/{ticker}_stock_price.parquet`: 공공데이터포털 주식시세 API 원천 응답
- `data/interim/{ticker}_stock_price_normalized.parquet`: 내부 표준 컬럼명으로 정규화한 주식시세 데이터
- `data/raw/kospi_index.parquet`: 공공데이터포털 지수시세 API 원천 응답
- `data/interim/kospi_index_normalized.parquet`: 내부 표준 컬럼명으로 정규화한 KOSPI 지수 데이터
- `models/{ticker}_model.joblib`: 학습된 모델
- `reports/model_comparison.md`: 모델 평가 결과
- `reports/backtest_summary.md`: 단순 백테스트 결과
- `reports/final_report.md`: 블로그/포트폴리오용 최종 보고서

## 7. 중요한 원칙

- 미래 데이터가 feature에 섞이면 안 됩니다.
- 랜덤 train/test split을 쓰지 않습니다.
- 재무제표는 결산 기준일이 아니라 공시 제출일 이후부터 사용할 수 있습니다.
- ML 성능과 투자 수익률은 다릅니다.
- 이 프로젝트는 교육/분석 목적이며 투자 자문이나 매매 신호 제공이 아닙니다.

## 8. 추천 블로그 시리즈

1. 바이브 코딩으로 주식 예측 ML 프로젝트 시작하기
2. 공공데이터포털 주식시세 API로 실제 주가 데이터 수집하기
3. 주식 예측에서 데이터 누수가 왜 위험한가
4. OHLCV 데이터로 방향성 예측 feature 만들기
5. 랜덤 분할이 아니라 시간 순서로 모델 검증하기
6. LogisticRegression과 RandomForest로 첫 예측 모델 만들기
7. 예측 정확도와 투자 수익률은 왜 다른가
8. 간단한 백테스트와 거래비용 반영하기
9. DART 재무제표와 시장지표를 추가해 모델 개선하기
10. Codex와 함께 주식 ML 파이프라인 문서화하기
