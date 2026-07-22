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

실제 API 실행 시 주식은 공공데이터포털 금융위원회_주식시세정보에서 수집합니다. KOSPI 지수는 금융위원회_지수시세정보를 먼저 호출하고, 실패하면서 `KRX_AUTH_KEY`(또는 `KRX_API_KEY`)가 설정되어 있으면 KRX Open API를 두 번째로 시도합니다. 원천 응답은 `data/raw/`, 내부 표준 컬럼명으로 정규화한 데이터는 `data/interim/`, feature/label 학습 데이터는 `data/processed/`에 저장합니다.

`DATA_GO_KR_SERVICE_KEY`는 주식시세와 지수시세 API에 사용할 수 있지만 공공데이터포털에서 각 API의 활용 신청이 승인되어야 합니다. 주식 API가 동작해도 지수 API 권한이 없으면 `403 Forbidden`이 발생할 수 있습니다. KRX 보조 수집에는 `.env`의 `KRX_AUTH_KEY` 또는 `KRX_API_KEY`를 사용하며 키 값은 report나 metadata에 저장하지 않습니다.

공공데이터포털 주식시세정보는 일별 분석용 데이터이며 실시간 매매용 데이터가 아닙니다. 기준일자 다음 영업일 오후 1시 이후 갱신될 수 있으므로 최신일 데이터는 비어 있을 수 있습니다.
KOSPI 지수는 개별 종목의 움직임이 시장 전체 움직임보다 강했는지 구분하기 위해 필요합니다. 지수 종가로 `market_return_1d`, `market_return_5d`와 5일/20일 시장 변동성을 계산하고, 같은 과거 구간의 종목 수익률에서 시장 수익률을 뺀 `excess_return_1d`, `excess_return_5d`를 만듭니다. 모두 현재일 또는 과거 값만 사용하며 미래 5일 수익률 label과는 분리됩니다.

두 지수 API의 권한이 없거나 호출이 실패하면 주식시세 데이터만으로 파이프라인을 계속 실행합니다. 이때 시장 수익률과 시장 변동성은 `0.0`, 초과수익률은 같은 기간의 종목 수익률로 대체하고 원인과 fallback 여부를 `reports/data_summary.md`에 기록합니다. fallback 실행에서 나온 모델 결과는 실제 시장 대비 성과로 해석하면 안 됩니다.

실행 후 `reports/run_metadata.json`에서 `index_source`, `fallback_applied`, `fallback_reason`, `index_normalized_rows`, `merged_rows`를 확인합니다. `uses_real_kospi=true`와 `market_feature_mode=real_kospi`가 모두 기록되어야 실제 KOSPI feature가 검증된 실행입니다. 실제 지수 권한을 설정한 뒤에는 데이터 파이프라인부터 학습, 평가, 백테스트, 예측 순서로 다시 실행하고 `model_comparison.md`의 fallback 경고가 사라졌는지 확인합니다.

실제 KOSPI 모델과 같은 기간의 stock-only baseline을 비교할 때만 `--force-stock-only`를 사용합니다. 이 옵션은 API 장애가 아니라 비교 실험을 위해 의도적으로 지수 feature를 fallback 값으로 대체합니다.

```bash
python3 src/data_pipeline.py --ticker 005930 --start 2018-01-01 --end 2025-12-31 --force-stock-only
```

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
- `reports/run_metadata.json`: 데이터 출처, fallback 여부, 모델 및 평가 지표를 연결하는 실행 metadata
- `reports/runs/{run_id}.json`: fallback/real-index 비교를 위한 실행별 metadata snapshot
- `reports/index_mode_comparison.md`: 최신 fallback 실행과 실제 KOSPI 실행의 비교 보고서
- `reports/final_report.md`: 블로그/포트폴리오용 최종 보고서

## 7. 디렉토리 구조

초보자가 루트 디렉토리에서 바로 볼 파일은 최소화했습니다.

```text
.
├── README.md              # 프로젝트 시작 안내
├── AGENTS.md              # AI 작업 규칙
├── CURRENT_TASK.md        # 현재 작업 범위
├── requirements.txt       # Python 의존성
├── src/                   # 실행 코드
├── tests/                 # 테스트 코드
├── data/                  # raw/interim/processed 데이터
├── models/                # 학습된 모델
├── reports/               # 실행 결과 리포트
├── notebooks/             # 실험용 노트북
└── docs/                  # 보조 문서 모음
```

`src/` 하위 구조는 다음처럼 역할별로 나눴습니다.

```text
src/
├── data_pipeline.py       # 실행 진입점: 데이터 수집/가공
├── train.py               # 실행 진입점: 모델 학습
├── evaluate.py            # 실행 진입점: 모델 평가
├── backtest.py            # 실행 진입점: 단순 백테스트
├── predict.py             # 실행 진입점: 최신 예측
├── core/                  # 설정, 파일 저장/로드 유틸
├── data_sources/          # 외부 API client
├── domain/                # feature, label, sample data 생성 로직
└── pipeline/              # 실제 pipeline 구현
```

처음 코드를 볼 때는 `src/data_pipeline.py` 같은 실행 파일을 먼저 보고, 세부 구현은 `src/pipeline/`과 `src/domain/`을 따라가면 됩니다.

`docs/` 하위 구조는 다음과 같습니다.

```text
docs/
├── project/      # 규칙, 로드맵, 프로젝트 기획 문서
├── logs/         # 작업 로그
├── study/        # 공부할 개념과 기술 목록
├── prompts/      # 에이전트 작업 프롬프트
└── references/   # API 가이드 등 참고 자료
```

### 백엔드 개발자를 위한 코드 학습 순서

Python과 머신러닝이 익숙하지 않다면 다음 순서로 읽는 것을 추천합니다.

1. `docs/architecture/current_architecture.md`: 현재 코드 계층과 데이터 흐름 다이어그램
2. `docs/study/phase_1_5_pipeline_execution_flow_study.md`: main 위치와 전체 실행·데이터 흐름
3. `docs/study/phase_1_5_code_guide_study.md`: 계층별 파일 역할과 핵심 함수
4. `docs/study/phase_1_5_ml_concepts_roadmap_study.md`: 현재 ML 개념과 다음 학습 순서
5. `docs/study/phase_1_2_study_list.md`: API와 금융 데이터 관련 추가 공부 목록

처음 코드를 직접 따라갈 때는 첫 문서를 옆에 두고 `src/data_pipeline.py`에서 시작하면 됩니다.

## 8. 중요한 원칙

- 미래 데이터가 feature에 섞이면 안 됩니다.
- 랜덤 train/test split을 쓰지 않습니다.
- 재무제표는 결산 기준일이 아니라 공시 제출일 이후부터 사용할 수 있습니다.
- ML 성능과 투자 수익률은 다릅니다.
- 이 프로젝트는 교육/분석 목적이며 투자 자문이나 매매 신호 제공이 아닙니다.

## 9. 추천 블로그 시리즈

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
