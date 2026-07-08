# Phase 1-2 공부할 지식과 기술

이 문서는 이번 Phase 1-2 작업을 이해하고 다음 단계로 넘어가기 위해 공부할 항목을 정리한 목록이다.

## 1. 공공데이터포털 Open API 사용법

공부할 것:

- 서비스 활용신청
- service key 관리
- URL encoded key와 decoded key 차이
- REST API 요청 파라미터
- JSON 응답 구조
- HTTP status code와 API result code 구분
- pagination 처리

왜 필요한가:

이번 작업에서 주식시세 API는 정상 호출됐지만, 지수시세 API는 `403 Forbidden`이 발생했다. 이런 문제를 해결하려면 단순히 “키가 있다”가 아니라 해당 API별 활용신청, 승인 상태, endpoint 권한, 요청 파라미터가 맞는지 확인할 수 있어야 한다.

확인할 질문:

- 내 service key가 주식시세 API와 지수시세 API 모두에 승인되어 있는가?
- 403은 인증키 문제인가, API 활용신청 문제인가, endpoint 문제인가?
- API가 빈 응답을 줄 때 휴장일 때문인가, 파라미터 문제인가?

## 2. 금융 시계열 데이터 구조

공부할 것:

- OHLCV: open, high, low, close, volume
- 거래대금과 거래량 차이
- 시가총액과 상장주식수
- 등락률
- 영업일과 휴장일
- 기준일자와 데이터 제공 지연

왜 필요한가:

주식 데이터는 일반 tabular 데이터처럼 매일 같은 간격으로 완벽히 존재하지 않는다. 휴장일, 상장 이벤트, API 제공 지연이 있다. 이 차이를 이해해야 잘못된 결측치 처리나 잘못된 날짜 merge를 피할 수 있다.

확인할 질문:

- `2018-01-01`부터 요청했는데 실제 dataset 시작이 왜 `2020-03-27`인가?
- API 원천 데이터가 비어 있는 날짜는 휴장일인가, API 제한인가?
- 일별 종가 데이터는 언제 확정되는가?

## 3. 데이터 정규화

공부할 것:

- source schema와 internal schema 구분
- 컬럼명 표준화
- 문자열 숫자에서 comma 제거
- 날짜 파싱
- dtype 변환
- raw/interim/processed 데이터 레이어

왜 필요한가:

공공데이터포털 응답은 `basDt`, `srtnCd`, `clpr`처럼 API 전용 축약명을 사용한다. 모델 코드가 API 컬럼명에 직접 의존하면 API가 바뀔 때 전체 pipeline이 흔들린다. 그래서 `normalize_*` 함수에서 표준 컬럼명으로 바꾼 뒤 나머지 코드는 표준 컬럼만 사용한다.

확인할 질문:

- raw 데이터는 왜 수정하지 않고 따로 저장하는가?
- interim 데이터와 processed 데이터의 차이는 무엇인가?
- API 컬럼명이 바뀌면 어디를 고쳐야 하는가?

## 4. 데이터 누수

공부할 것:

- label leakage
- future data leakage
- time-based split
- rolling feature의 현재일 포함 여부
- train/validation/test 시간 순서

왜 필요한가:

주가 예측에서 가장 흔한 실수는 미래 값을 feature에 섞는 것이다. `future_return_5d`는 정답을 만들기 위한 값이지 모델 입력값이 아니다. 이 컬럼이 feature에 들어가면 모델 성능은 좋아 보여도 실제 예측에는 사용할 수 없다.

확인할 질문:

- `future_return_5d`가 feature에 들어가면 왜 문제인가?
- rolling mean은 현재일을 포함해도 되는가?
- 장마감 후 예측과 장중 예측은 feature 사용 가능 범위가 어떻게 다른가?
- random split이 금융 시계열에서 왜 위험한가?

## 5. Feature Engineering

공부할 것:

- 수익률 feature: `return_1d`, `return_5d`
- 이동평균: `ma_5`, `ma_20`, `ma_60`
- 이동평균 대비 괴리율
- 거래량 변화율
- rolling volatility
- 시장수익률과 초과수익률

왜 필요한가:

모델은 원본 OHLCV를 그대로 이해하지 않는다. 과거 수익률, 변동성, 거래량 변화 같은 형태로 변환해야 짧은 기간의 흐름을 학습할 수 있다. 단, feature는 반드시 예측 시점에 이미 알고 있는 값만 써야 한다.

확인할 질문:

- `pct_change(5)`와 `shift(-5)`는 어떻게 다른가?
- `return_5d`는 feature이고 `future_return_5d`는 label인 이유는 무엇인가?
- KOSPI 지수가 없을 때 `excess_return_5d`를 어떻게 처리해야 하는가?

## 6. 모델 학습과 평가

공부할 것:

- LogisticRegression
- RandomForestClassifier
- SimpleImputer
- StandardScaler
- Pipeline
- validation set과 test set
- accuracy, precision, recall, f1, roc_auc
- confusion matrix

왜 필요한가:

이번 프로젝트의 1차 목표는 fancy model이 아니라 재현 가능한 검증 흐름이다. LogisticRegression과 RandomForest는 단순하고 설명하기 쉬워서 pipeline 검증에 적합하다.

확인할 질문:

- validation score로 모델을 고르고 test score로 최종 평가하는 이유는?
- accuracy가 낮아도 precision이나 recall을 따로 봐야 하는 이유는?
- `roc_auc`가 0.5 근처면 어떤 의미인가?

## 7. 백테스트 기본 개념

공부할 것:

- buy-and-hold
- 전략 수익률
- 거래 횟수
- 승률
- 최대 낙폭
- 거래비용
- overlapping trade

왜 필요한가:

ML 지표가 좋아도 투자 성과가 좋다는 뜻은 아니다. 반대로 ML 지표가 애매해도 특정 거래 규칙에서는 다르게 보일 수 있다. 이번 백테스트는 교육용 단순 계산이며, 실제 포트폴리오 수익률로 해석하면 안 된다.

확인할 질문:

- 5영업일 보유 거래가 매일 겹치면 어떤 문제가 생기는가?
- 거래비용을 빼면 전략 수익률이 얼마나 달라지는가?
- buy-and-hold와 모델 전략을 왜 분리해서 봐야 하는가?

## 8. 다음 단계에서 필요한 기술

### KOSPI 지수 API 권한 확인

이번 실행에서 지수 API는 `403 Forbidden`이 발생했다. 다음 단계에서는 공공데이터포털에서 금융위원회_지수시세정보 API 활용신청 상태를 확인해야 한다.

### 데이터 품질 리포트

공부할 것:

- row count 검증
- 날짜 범위 검증
- 결측치 검증
- 중복 날짜 검증
- 비정상 가격 검증

### 캐시 구조

공부할 것:

- Parquet cache
- API 호출 재시도
- 증분 수집
- rate limit 대응

### Walk-forward validation

공부할 것:

- expanding window
- rolling window
- time series cross-validation

금융 시계열에서는 한 번의 train/validation/test split만으로 모델 안정성을 판단하기 어렵다. walk-forward validation은 기간을 여러 번 굴려 보며 모델이 시간에 따라 얼마나 안정적인지 확인하는 방법이다.

## 추천 학습 순서

1. 공공데이터포털 API 요청/응답 구조
2. pandas datetime, numeric 변환, parquet 저장
3. 데이터 누수와 time-based split
4. OHLCV feature engineering
5. LogisticRegression과 RandomForest 기본
6. classification metrics 해석
7. 단순 백테스트와 거래비용
8. KOSPI 지수 feature와 walk-forward validation
