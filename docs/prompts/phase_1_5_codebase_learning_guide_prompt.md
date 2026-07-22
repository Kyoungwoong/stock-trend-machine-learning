# Agent Prompt Plan: 코드베이스 학습 가이드

## Current Task Summary

현재 구현된 주식 ML 파이프라인을 백엔드 개발자가 처음부터 따라가며 공부할 수 있도록 실행 흐름, 코드 구조, 머신러닝 개념을 문서화한다.

## Scope

- 실제 CLI 진입점부터 데이터 수집, 학습, 평가, 백테스트, 예측까지의 호출 흐름 설명
- 모든 Python 모듈의 역할과 핵심 함수의 입력, 처리, 출력 설명
- 현재 코드에 사용된 Python과 머신러닝 개념 설명
- 현재 프로젝트 상태에 맞는 다음 머신러닝 학습 순서 제안
- README와 docs 안내 문서에 새로운 학습 문서 링크 추가
- `docs/architecture/`에 현재 코드 계층, 데이터 흐름과 누수 경계 다이어그램 추가
- 현재 실데이터 산출물을 예시로 데이터 행과 파일 흐름 설명

## Out of Scope

- Python 실행 코드, 모델 구조, feature 또는 데이터 스키마 변경
- 모델 재학습 및 실제 API 재호출
- walk-forward validation이나 새로운 feature 구현
- LSTM, Transformer, 실시간 매매 및 투자 추천 기능 추가
- 현재 결과를 모델 성능 향상의 증거로 해석하는 작업

## Implementation Plan

1. `CURRENT_TASK.md`, CLI 진입점과 각 계층의 구현을 다시 확인한다.
2. 파이프라인 실행 순서와 단계별 입력·출력을 학습 문서로 작성한다.
3. 백엔드 계층 구조에 비유하여 모든 모듈의 역할과 핵심 함수를 설명한다.
4. 구현된 ML 개념과 다음에 공부할 개념을 현재 ROADMAP 순서에 맞춰 정리한다.
5. README와 docs 안내 문서에 추천 독서 순서를 연결한다.
6. 현재 구조를 Mermaid 기반 아키텍처 다이어그램으로 작성한다.
7. CLI 도움말, 테스트, 문서 경로와 보안 표현을 검증한다.
8. 검증 결과와 판단 근거를 작업 로그에 기록한다.

## Files Expected To Change

- `CURRENT_TASK.md`
- `README.md`
- `docs/README.md`
- `docs/study/phase_1_5_pipeline_execution_flow_study.md`
- `docs/study/phase_1_5_code_guide_study.md`
- `docs/study/phase_1_5_ml_concepts_roadmap_study.md`
- `docs/architecture/current_architecture.md`
- `docs/prompts/phase_1_5_codebase_learning_guide_prompt.md`
- `docs/logs/phase_1_5_codebase_learning_guide.md`

## Verification Plan

- 다섯 CLI의 `--help` 실행으로 문서의 명령과 옵션 확인
- `python3 -m pytest -q`로 기존 동작이 유지되는지 확인
- 문서에서 언급한 로컬 파일과 주요 함수가 실제로 존재하는지 검색
- API 키 값과 투자 추천 표현이 새 문서에 포함되지 않았는지 확인
- 세 개의 study 문서와 prompt, log 문서가 모두 존재하는지 확인

## Risks

- 실제 호출 흐름과 문서 설명이 달라질 수 있음
- `return_5d`와 `future_return_5d`를 혼동하여 데이터 누수를 잘못 설명할 수 있음
- 현재 한 번의 실험 결과를 일반적인 모델 성능으로 과대해석할 수 있음
- sample, real KOSPI, stock-only fallback 데이터를 혼동할 수 있음
- Python 초보자에게 불필요하게 많은 세부 구현을 한꺼번에 전달할 수 있음

## Completion Criteria

- 실행 흐름, 코드 해설, ML 개념·로드맵 문서가 각각 존재한다.
- 사용자가 `src/data_pipeline.py`에서 시작해 최종 예측까지 호출 경로를 설명할 수 있다.
- 모든 Python 모듈의 역할과 핵심 함수의 데이터 입출력을 찾을 수 있다.
- feature와 label의 차이, 시간 분할, 주요 평가 지표와 백테스트 한계를 설명할 수 있다.
- 다음 학습 과제가 walk-forward validation인 이유를 이해할 수 있다.
- CLI 검증과 전체 테스트가 통과하고 작업 로그에 결과가 기록된다.

## Execute Commands

 - `python3 src/data_pipeline.py --help`
 - `python3 src/train.py --help`
 - `python3 src/evaluate.py --help`
 - `python3 src/backtest.py --help`
 - `python3 src/predict.py --help`
 - `python3 -m pytest -q`

## Documentation

 - 실행 흐름: `docs/study/phase_1_5_pipeline_execution_flow_study.md`
 - 코드 해설: `docs/study/phase_1_5_code_guide_study.md`
 - ML 로드맵: `docs/study/phase_1_5_ml_concepts_roadmap_study.md`
 - Work log: `docs/logs/phase_1_5_codebase_learning_guide.md`
 - Agent plan: `docs/prompts/phase_1_5_codebase_learning_guide_prompt.md`
