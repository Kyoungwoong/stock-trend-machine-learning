# Task Log: 코드베이스 학습 가이드

## Purpose

Python과 머신러닝 경험이 적은 백엔드 개발자가 현재 프로젝트의 최초 진입점부터 데이터, 모델, 평가 흐름을 따라갈 수 있도록 학습 문서를 만든다. 현재 사용 중인 ML 개념과 다음 개발 단계도 실제 코드에 연결해 설명한다.

## Problem

기존 README와 Phase 1-2 공부 목록에는 실행 명령과 개념 목록이 있었지만, CLI wrapper와 실제 구현의 관계, 계층별 책임, 함수 사이의 DataFrame 흐름이 한 곳에 연결되어 있지 않았다. 이 때문에 처음 보는 사용자가 모델 코드부터 읽거나 `return_5d`와 `future_return_5d`를 혼동할 수 있었다.

## What Changed

- `CURRENT_TASK.md`: Phase 1-5 문서화 작업의 목적, 범위, 누수 점검과 다음 작업을 기록했다.
- `README.md`, `docs/README.md`: 세 학습 문서의 추천 독서 순서를 추가했다.
- `docs/study/phase_1_5_pipeline_execution_flow_study.md`: 다섯 CLI와 데이터 산출물의 전체 흐름을 설명했다.
- `docs/study/phase_1_5_code_guide_study.md`: 모든 Python 모듈의 역할과 핵심 함수를 백엔드 계층에 비유해 설명했다.
- `docs/study/phase_1_5_ml_concepts_roadmap_study.md`: 현재 ML 개념, 결과 해석 한계와 다음 학습 순서를 정리했다.
- `docs/architecture/current_architecture.md`: 코드 계층, 데이터·artifact 흐름과 누수 경계를 Mermaid 다이어그램으로 추가했다.
- `docs/prompts/phase_1_5_codebase_learning_guide_prompt.md`: 작업 전 범위, 계획, 위험과 완료 기준을 기록했다.
- `docs/logs/phase_1_5_codebase_learning_guide.md`: 작업 방법과 검증 결과를 기록했다.

실행 코드, 모델 artifact, 데이터와 report 결과는 변경하지 않았다.

## How It Works

첫 번째 문서는 `src/data_pipeline.py`에서 시작해 실제 `src/pipeline/data_pipeline.py` 구현으로 이동하는 법을 보여준다. 이후 데이터가 raw, interim, processed 레이어를 거쳐 모델과 report로 이동하는 흐름을 설명한다.

두 번째 문서는 CLI를 Controller, pipeline을 Application Service, domain을 업무 변환 규칙, data_sources를 외부 adapter, core를 설정과 저장 도구에 비유한다. 각 핵심 함수가 받는 데이터와 만드는 결과를 해당 계층 안에서 설명한다.

세 번째 문서는 코드에서 발견한 feature, label, 시간 분할, 전처리, 두 분류 모델, 평가와 백테스트를 개념과 연결한다. 마지막에는 현재 단일 시간 분할의 한계를 해결하기 위한 walk-forward validation부터 다음 학습 순서를 제시한다.

아키텍처 문서는 위 세 문서를 읽기 전에 전체 구조를 빠르게 파악할 수 있도록 CLI, application pipeline, domain, external adapter, core와 저장 산출물의 관계를 한 화면에 연결한다.

## Why This Approach

파일별 주석을 길게 복사하기보다 실행 흐름, 코드 책임, ML 개념을 분리하면 사용자가 궁금한 질문에 따라 문서를 선택할 수 있다. 모든 모듈은 지도처럼 포함하되 현재 실행 경로의 함수만 자세히 설명하여 미구현 DART/ECOS skeleton과 핵심 코드의 중요도를 혼동하지 않게 했다.

복잡한 새 모델을 제안하지 않고 현재 검증의 가장 큰 한계인 단일 시간 분할을 다음 학습 주제로 두었다. 이는 프로젝트의 우선순위인 데이터 누수 방지, 재현성, 시간 순서 검증에 맞는다.

## Verification

실행한 명령과 결과:

```text
python3 src/data_pipeline.py --help  -> passed
python3 src/train.py --help          -> passed
python3 src/evaluate.py --help       -> passed
python3 src/backtest.py --help       -> passed
python3 src/predict.py --help        -> passed
python3 -m pytest -q                 -> 26 passed in 8.21s
```

추가로 세 study 문서에 AGENTS.md가 요구하는 일곱 개 heading이 모두 있는지, 문서에서 설명한 주요 함수가 실제 코드에 있는지 `rg`로 확인했다.

실제 API는 호출하지 않았고 모델도 다시 학습하지 않았다. 문서에 사용한 1,473/1,414/1,409행과 평가 수치는 현재 저장소에 있는 실제 삼성전자 및 실제 KOSPI 산출물을 읽어 확인한 스냅샷이다. sample 또는 fallback 결과로 표현하지 않았다.

## Data Leakage Check

- `future_return_5d`는 미래 5영업일 정답 생성, 평가와 백테스트에만 사용하며 feature에 포함하면 안 된다고 설명했다.
- `label_up_5d`와 `future_return_5d`를 차단하는 `FEATURE_COLUMNS`, `validate_feature_columns()`와 테스트 위치를 연결했다.
- `return_5d`는 과거 방향, `future_return_5d`는 미래 방향이라는 식을 함께 제시했다.
- rolling feature는 장 마감 후 예측이라는 현재 정의에서 현재일을 포함하지만 미래일은 포함하지 않는다고 설명했다.
- train/validation/test와 다음 walk-forward validation이 날짜순이어야 한다고 명시했다.
- 향후 재무제표와 경제지표는 결산·대상일이 아니라 공시·발표일 이후에만 사용해야 함을 기록했다.

## Remaining Issues

- Markdown 전용 link checker는 프로젝트 의존성에 없어 경로와 함수 존재를 shell과 `rg`로 확인했다.
- 현재 모델은 단일 train/validation/test 분할만 사용하므로 기간별 안정성을 알 수 없다.
- 현재 백테스트의 5영업일 거래가 겹쳐 참고용 누적 수익률을 실제 포트폴리오 수익률로 해석할 수 없다.
- 새 문서는 현재 코드 스냅샷 기준이므로 pipeline interface가 바뀌면 함께 갱신해야 한다.

## Next Step

Phase 2-1에서 expanding window 또는 rolling window 정책을 먼저 명확히 정하고, 날짜순 fold별 학습·평가와 지표 분산을 기록하는 walk-forward validation을 구현한다.
