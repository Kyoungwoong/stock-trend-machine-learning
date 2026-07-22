# Study Note: 코드 구조와 핵심 함수

## What I Should Learn

- Python 프로젝트의 import, CLI wrapper, package 구조를 읽는 방법
- `core`, `data_sources`, `domain`, `pipeline` 계층의 책임
- 각 Python 파일이 현재 실행에 참여하는지, 호환용인지, 미래 확장용인지 구분하는 방법
- 핵심 함수의 입력 DataFrame과 출력 DataFrame이 어떻게 바뀌는지
- 코드에서 데이터 누수와 실행 불일치를 방지하는 지점

## Why It Matters

ML 프로젝트도 결국 데이터가 오가는 애플리케이션이다. 모델 클래스만 읽으면 API 실패, 컬럼 변환, 날짜 병합, 학습/평가 분리 같은 더 중요한 동작을 놓친다. 백엔드에서 계층의 책임과 DTO 흐름을 따라가듯 이 저장소도 바깥 계층에서 안쪽 계층으로 읽는 것이 효율적이다.

## Key Concepts

### 1. 백엔드 구조로 번역한 디렉토리

| 프로젝트 계층 | 백엔드에 비유 | 책임 |
|---|---|---|
| `src/*.py` CLI | Controller/Router | 인자를 받아 실제 pipeline `main()`으로 전달 |
| `src/pipeline` | Application Service | 여러 domain·infra 기능을 실행 순서에 맞게 조립 |
| `src/domain` | Domain Service | feature, label, 합성 데이터 변환 규칙 |
| `src/data_sources` | External API Client/Adapter | 외부 API 호출과 source schema 정규화 |
| `src/core` | Configuration/Repository Utility | 환경설정, 파일 I/O, metadata 관리 |

의존성 방향은 주로 `pipeline → domain/data_sources/core`다. `domain`은 API 키나 report 경로를 모르므로 DataFrame 변환 로직을 비교적 독립적으로 테스트할 수 있다.

### 2. 먼저 알아둘 최소 Python 문법

#### import와 package

```python
from src.pipeline.data_pipeline import main
```

Java의 package import와 비슷하다. `src/data_pipeline.py`는 실제 구현 대신 위 `main`을 가져와 호출한다.

#### 실행 가드

```python
if __name__ == "__main__":
    main()
```

파일을 직접 실행했을 때만 `main()`을 호출한다. 테스트가 모듈을 import할 때는 자동 실행되지 않는다.

#### type hint

```python
def split_by_date(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
```

입력과 반환 타입을 설명하지만 런타임에서 Java처럼 강제되지는 않는다. IDE, 리뷰어, 정적 분석 도구를 위한 계약에 가깝다.

#### DataFrame

행과 열을 가진 메모리상의 테이블이다. SQL 결과 집합과 비슷하지만 `rolling`, `shift`, 벡터 연산으로 여러 행을 한꺼번에 변환할 수 있다.

#### dataclass와 frozen

`@dataclass(frozen=True)`는 값 보관용 객체를 간결하게 만들고 생성 후 필드 변경을 막는다. immutable DTO와 비슷하다.

### 3. CLI와 호환 wrapper

`src/data_pipeline.py`, `src/train.py`, `src/evaluate.py`, `src/backtest.py`, `src/predict.py`는 직접 실행하는 진입점이다. 직접 실행 시 repository root를 import 경로에 추가하고 `src.pipeline` 구현을 호출한다.

다음 파일은 예전 import 경로를 유지하기 위한 re-export wrapper다.

- `src/config.py` → `src/core/config.py`
- `src/storage.py` → `src/core/storage.py`
- `src/features.py` → `src/domain/features.py`
- `src/labeling.py` → `src/domain/labeling.py`
- `src/sample_data.py` → `src/domain/sample_data.py`

새 구현을 찾을 때는 wrapper가 아니라 오른쪽 실제 파일을 읽는다. 다만 기존 테스트나 외부 코드가 왼쪽 경로를 import할 수 있으므로 이유 없이 삭제하면 안 된다.

### 4. core 계층

#### `src/core/config.py`

`.env`와 환경변수를 읽어 immutable `Settings`를 만든다. API 키, data/model/report 디렉토리와 기본 ticker를 중앙에서 관리한다. 키를 코드에 직접 적지 않는 것이 핵심이다.

#### `src/core/storage.py`

- `ensure_parent()`: 저장 전에 상위 디렉토리를 만든다.
- `save_parquet()`: DataFrame을 Parquet으로 저장한다.
- `load_parquet()`: 저장 형식 차이를 감추고 DataFrame을 읽는다.
- `write_report()`: Markdown report를 저장한다.

I/O를 변환 로직과 분리하여 domain 함수가 파일시스템을 몰라도 되게 한다.

#### `src/core/run_metadata.py`

한 번의 데이터 생성, 모델, 평가 결과를 같은 실행으로 추적한다.

- `RunMetadata`: 실행 문맥의 schema다.
- `build_run_metadata()`: real/sample/fallback 상태를 일관되게 판정한다.
- `write_run_metadata()`, `load_run_metadata()`: JSON 저장과 필수 필드 검증을 담당한다.
- `metadata_from_artifact()`: 학습 모델 내부의 metadata를 꺼낸다.
- `update_matching_run_metadata()`: 현재 report metadata와 모델의 생성 시각이 다르면 평가를 거부한다.
- `redact_secrets()`: 오류 문자열에서 API 키 원문과 URL encoding 형태를 제거한다.
- `snapshot_run_metadata()`: 실행별 JSON을 보존한다.
- `write_index_mode_comparison()`: 최신 fallback/real KOSPI 결과를 비교한다.

이 모듈은 ML 모델보다 운영 추적성에 가깝다. 백엔드의 request ID, deployment metadata, audit record 역할을 함께 한다.

### 5. data_sources 계층

#### `src/data_sources/fsc_stock_api.py`

FSC 주식시세 API를 날짜 구간별로 호출한다. pagination된 응답에서 item을 추출하고 HTTP/API 오류를 검사한다. `normalize_stock_price_items()`는 `basDt`, `clpr`, `trqu` 같은 source 컬럼을 `date`, `close`, `volume` 같은 내부 schema로 변환한다.

#### `src/data_sources/fsc_index_api.py`

FSC 지수시세에서 KOSPI를 수집하고 정규화한다. 내부 index schema는 `date`, `index_code`, OHLCV, 거래대금과 등락률로 고정된다.

#### `src/data_sources/krx_index_api.py`

FSC 지수 호출이 실패했을 때 사용하는 두 번째 adapter다. KRX의 대문자 컬럼을 FSC와 같은 내부 index schema로 변환한다. 이후 pipeline은 데이터 출처가 FSC인지 KRX인지 몰라도 된다. 이것이 adapter와 normalization의 장점이다.

#### `src/data_sources/dart_api.py`, `bok_ecos_api.py`

Phase 4 확장 위치를 보여주는 skeleton이다. 메서드는 현재 `NotImplementedError`를 발생시키므로 현 파이프라인에서 호출하지 않는다. 재무정보는 결산일이 아니라 공시 제출일 이후, 경제지표는 실제 발표일 이후부터 사용해야 한다.

### 6. domain 계층

#### `src/domain/sample_data.py`

영업일 인덱스를 만들고 재현 가능한 합성 주식·지수 데이터를 생성한다. API 키가 없어도 전체 실행 구조를 검증하기 위한 데이터이며 실제 시장 분석에 사용할 수 없다.

#### `src/domain/features.py`

`FEATURE_COLUMNS`는 모델 입력 schema의 single source of truth다. 현재 21개 feature가 있다.

| 그룹 | 대표 컬럼 | 계산 의미 |
|---|---|---|
| 과거 수익률 | `return_1d`, `return_5d` | 현재 종가와 과거 종가의 변화 |
| 추세 | `ma_5`, `close_vs_ma20` | 이동평균과 현재 가격의 관계 |
| 거래량 | `volume_change_1d`, `volume_ma_20` | 거래 활동의 변화와 평균 |
| 변동성 | `volatility_5d`, `volatility_20d` | 과거 일간 수익률의 표준편차 |
| 시장 | `market_return_5d` | KOSPI의 같은 과거 기간 수익률 |
| 상대 성과 | `excess_return_5d` | 종목 수익률에서 시장 수익률을 뺀 값 |

`add_price_features()`는 날짜순으로 정렬한 뒤 `pct_change`와 `rolling`으로 feature를 만든다. 예측 시점이 장 마감 후이므로 rolling window는 현재일 종가와 거래량을 포함한다. 미래 행을 참조하지 않는다.

지수가 없으면 시장 수익률과 시장 변동성을 0으로 두고 초과수익률을 종목 수익률과 같게 만든다. 이는 pipeline을 계속 실행하기 위한 fallback이지 실제 시장 정보가 아니다.

#### `src/domain/labeling.py`

`add_forward_return_label()`은 다음 식을 계산한다.

```text
future_return_5d[t] = close[t+5] / close[t] - 1
label_up_5d[t] = 1 if future_return_5d[t] > 0 else 0
```

`shift(-5)`는 의도적으로 미래 종가를 참조해 정답을 만든다. 이 값은 label 생성, 평가, 백테스트에만 사용할 수 있다. `drop_unlabeled_rows()`는 아직 5일 뒤 가격이 없는 마지막 행을 학습 dataset에서 제거한다.

### 7. pipeline 계층

#### `src/pipeline/data_pipeline.py`

`build_dataset()`은 이 프로젝트에서 가장 먼저 읽을 application service다.

| 단계 | 호출 | 결과 |
|---|---|---|
| 수집 | API client 또는 sample generator | raw DataFrame |
| 정규화 | `normalize_*` | 내부 schema DataFrame |
| 지수 선택 | `fetch_kospi_index()` | FSC → KRX → fallback |
| 결합 | `merge_stock_and_index()` | 날짜 기준 one-to-one inner join |
| feature | `add_price_features()` | 현재·과거 기반 입력 컬럼 |
| label | `add_forward_return_label()` | 미래 5일 정답 컬럼 |
| 저장 | storage와 metadata 함수 | parquet, JSON, Markdown |

`validate_market_features()`는 실제 지수를 받았다고 기록했지만 시장 feature가 전부 0인 잘못된 상태를 탐지한다. 실패하면 stock-only fallback으로 다시 feature를 만든다.

#### `src/pipeline/train.py`

- `split_by_date()`: 우선 2024년 이전 train, 2024년 validation, 2025년 이후 test로 나눈다. 해당 구간이 비면 날짜순 70/15/15 비율을 사용한다. 어느 경우에도 shuffle하지 않는다.
- `validate_feature_columns()`: label과 미래 수익률이 feature 목록에 있으면 즉시 실패시킨다.
- `build_models()`: 두 scikit-learn Pipeline을 만든다.
- `train()`: train으로 두 모델을 fit하고 validation accuracy가 높은 모델을 선택해 artifact로 저장한다.

Logistic Regression Pipeline은 median imputer → scaler → model 순서다. Random Forest는 median imputer → model 순서이며 tree 모델에는 scaling이 필수적이지 않아 scaler가 없다.

#### `src/pipeline/evaluate.py`

선택된 모델을 test 구간에서 한 번 평가한다. 예측 확률이 있으면 ROC-AUC도 계산한다. 행별 예측 CSV, 평가 report, 실행 snapshot을 저장한다. validation 점수는 모델 선택용이고 test 점수는 최종 확인용이라는 역할을 분리한다.

#### `src/pipeline/backtest.py`

- `max_drawdown()`: 누적 가치가 이전 최고점에서 얼마나 하락했는지 계산한다.
- `backtest()`: 상승 예측 행에 미래 5일 수익률과 거래비용을 적용한다.

현재 전략은 겹치는 5일 포지션, 자본 배분, 실제 체결가를 엄밀히 모델링하지 않는다. 따라서 `strategy_total_return_reference`라는 이름처럼 참고 지표다.

#### `src/pipeline/predict.py`

label이 필요 없는 최신 feature 파일의 마지막 행을 읽고 예측한다. 모델 artifact에 저장된 feature 순서를 그대로 사용하므로 학습과 예측의 컬럼 계약이 유지된다. 출력에 실제 KOSPI 사용 여부와 교육용 경고를 함께 표시한다.

### 8. 테스트 코드를 읽는 순서

- `tests/test_labeling.py`: 미래 5일 label 계산
- `tests/test_features.py`: feature와 누수 컬럼 배제
- `tests/test_fsc_stock_api.py`: 주식 API schema 정규화
- `tests/test_index_data.py`: 지수 정규화, 날짜 결합, fallback
- `tests/test_run_metadata.py`: 실행 모드, 키 마스킹, artifact 일치

테스트는 코드 설명의 실행 가능한 예제다. 구현이 모호할 때 문서보다 테스트의 입력과 expected result를 먼저 보면 계약을 빠르게 이해할 수 있다.

## Related Concepts To Study Next

- pandas indexing, vectorization과 SQL window function 비교
- dependency direction과 pure transformation function
- scikit-learn estimator와 Pipeline 인터페이스
- model artifact versioning과 data lineage
- 단위 테스트에서 monkeypatch로 외부 API를 대체하는 방법

## Common Mistakes

- re-export wrapper를 실제 구현으로 착각하는 것
- pandas 연산이 원본 DataFrame을 변경한다고 가정하는 것: 이 코드는 대부분 `copy()` 후 새 값을 반환한다.
- `pct_change(5)`와 `shift(-5)`를 같은 의미로 보는 것
- `FEATURE_COLUMNS`에 컬럼을 추가하고 데이터 생성·테스트·예측 계약을 함께 확인하지 않는 것
- API 응답 컬럼을 pipeline 전체에서 직접 사용해 source 변경의 영향을 퍼뜨리는 것
- metadata 없이 모델 파일만 복사해 어느 데이터로 학습했는지 잃어버리는 것

## How This Appears In Our Code

- 계층 조립: `src/pipeline/data_pipeline.py`
- 입력 schema: `src/domain/features.py`의 `FEATURE_COLUMNS`
- 정답 schema: `src/domain/labeling.py`의 `LABEL_COLUMN`, `FUTURE_RETURN_COLUMN`
- 외부 schema adapter: `src/data_sources/fsc_stock_api.py`, `fsc_index_api.py`, `krx_index_api.py`
- 재현성과 추적: `src/core/run_metadata.py`
- 실행 가능한 계약: `tests/`

## Blog Angle

“Spring 백엔드 구조로 이해하는 Python ML 파이프라인”으로 구성할 수 있다. CLI를 Controller, pipeline을 Application Service, domain을 순수 업무 규칙, data_sources를 외부 adapter로 매핑하고 DataFrame을 단계별 DTO처럼 설명하면 두 생태계의 차이를 자연스럽게 연결할 수 있다.
