# Phase 1-3 KOSPI 지수 연동 작업 기록

## 목적

삼성전자 일별 시세에 같은 거래일의 KOSPI 지수를 결합하고 실제 시장 수익률과 초과수익률 feature를 생성한다. 지수 API 권한이 없을 때도 stock-only 파이프라인은 중단하지 않는다.

## 무엇을 했는가

- 지수 수집 우선순위를 금융위원회 지수 API, KRX Open API, stock-only fallback 순서로 구성했다.
- 두 API 응답을 `date`, `index_code`, `index_name`, `open`, `high`, `low`, `close`, `volume`, `trading_value`, `change_rate` 공통 스키마로 정규화했다.
- KRX 키는 request header의 `AUTH_KEY`로만 전달하고 오류에는 상태 코드와 endpoint만 남겼다.
- 주식과 지수는 `date` 기준 `inner join`하고 일대일 관계를 검증했다.
- 시장 1일/5일 수익률, 5일/20일 변동성, 종목의 1일/5일 초과수익률을 추가했다.
- 지수가 없으면 시장 수익률과 변동성을 0으로, 초과수익률을 같은 기간의 종목 수익률로 대체했다.
- 데이터 출처, 실패 사유, 병합 전후 행 수와 fallback 여부를 보고서에 기록했다.

## 어떻게 구현했는가

API client는 원천 응답 수집을 담당하고 `normalize_*` 함수가 날짜와 숫자 변환을 담당한다. interim 지수 데이터는 소스와 무관한 공통 스키마로 저장한다. 주식 OHLCV와 충돌하는 지수 컬럼은 병합 직전에만 `index_*` 접두사로 바꾼다.

feature는 날짜 오름차순 정렬 후 `pct_change`와 `rolling`으로 계산한다. 장 마감 후 예측을 전제로 현재일 종가까지 포함하지만 이후 날짜는 참조하지 않는다. KRX API는 `basDd` 단일 기준일 요청 방식이므로 평일을 순회하고 휴장일의 빈 응답은 건너뛴다.

## 왜 이렇게 했는가

- 공통 스키마는 FSC와 KRX 중 출처가 바뀌어도 feature 코드를 유지한다.
- `inner join`은 한쪽 시장에 없는 날짜를 임의 보간해 잘못된 수익률이 생기는 것을 막는다.
- fallback은 실행 재현성을 유지하지만 실제 시장 정보가 아니므로 해석 제한을 보고해야 한다.
- 과거 5일 초과수익률과 미래 5일 label을 분리해야 직접적인 데이터 누수를 막을 수 있다.

## 검증 항목

- FSC/KRX 공통 스키마와 numeric 변환
- 날짜 기준 inner join 및 지수 미수집 fallback
- 미래 지수 종가 변경이 과거 market feature에 미치는 영향 없음
- label 관련 컬럼의 feature 제외
- KRX HTTP 오류의 인증키 비노출
- 샘플/실제 pipeline과 train, evaluate, backtest, predict 실행

## 추가로 공부할 내용

### 거래일 캘린더

단순 평일과 실제 한국거래소 영업일은 다르다. 공휴일과 임시 휴장을 처리하는 거래 캘린더 및 원천 데이터 기반 inner join을 비교한다.

### 수익률과 변동성

단순수익률과 로그수익률, `rolling.std()`의 표본 표준편차, 변동성 연율화를 학습한다.

### 초과수익률과 시장모형

현재의 단순 차감 방식과 beta를 반영한 CAPM/시장모형의 차이를 학습한다.

### API 신뢰성

timeout, 재시도, 지수 백오프, 요청량 제한과 로컬 캐시를 학습한다. KRX 일별 API는 장기간 수집 시 호출이 많아 증분 수집이 필요하다.

### 시계열 검증

고정 날짜 분할 이후 walk-forward validation과 rolling window 검증으로 시장 국면 변화에 대한 안정성을 확인한다.
