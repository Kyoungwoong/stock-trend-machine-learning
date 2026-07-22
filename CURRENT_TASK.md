# CURRENT_TASK.md

## 현재 작업

Phase 1-5. 백엔드 개발자를 위한 코드베이스 및 머신러닝 학습 가이드 작성 (완료)

## 한 문장 요약

현재 구현된 파이프라인의 시작점, 코드 구조, 머신러닝 개념과 다음 학습 순서를 실제 코드와 산출물을 기준으로 문서화한다.

## 배경

Phase 1-4까지 실제 주식·KOSPI 데이터 수집, feature/label 생성, 시간 순서 학습·평가, 백테스트와 run metadata가 구현되었다. 기존 문서는 실행 방법과 개념 목록을 제공하지만, Python과 ML 경험이 적은 백엔드 개발자가 코드의 최초 진입점부터 전체 호출 흐름을 따라가기에는 설명이 분산되어 있었다.

## 작업 범위

- 전체 CLI 실행 순서와 데이터 산출물 흐름 설명
- 모든 Python 모듈의 역할과 핵심 함수 상세 설명
- 현재 사용한 Python·ML 개념을 초보자 관점에서 설명
- walk-forward validation부터 시작하는 다음 학습 순서 제안
- README와 docs 안내 문서에 학습 경로 추가
- 필수 prompt, study, work log 작성

## 제외 범위

- Python 실행 코드와 모델 변경
- feature 또는 데이터 schema 변경
- 모델 재학습과 실제 API 재호출
- walk-forward validation 및 새 ML 알고리즘 구현
- 투자 추천이나 현재 성능의 과대해석

## 완료 결과

- 실행 흐름 문서에서 `data_pipeline → train → evaluate → backtest → predict`와 단계별 파일을 연결했다.
- 코드 가이드에서 CLI, pipeline, domain, data_sources, core를 백엔드 계층과 비교했다.
- ML 가이드에서 feature/label, 누수, 두 모델, 평가 지표, 백테스트와 다음 로드맵을 설명했다.
- `docs/architecture/current_architecture.md`에 코드 계층, 데이터 흐름과 누수 경계 다이어그램을 추가했다.
- 현재 저장된 실제 KOSPI 데이터의 1,473 → 1,414 → 1,409행 변화를 예시로 기록했다.
- 문서 변경만 수행하고 모델·데이터·실행 코드는 변경하지 않았다.

## Data Leakage Check

- `future_return_5d`는 label 생성, 평가, 백테스트용이며 feature가 아님을 명확히 설명한다.
- `label_up_5d`가 모델 입력에서 제외되는 코드와 테스트 위치를 안내한다.
- rolling feature가 장 마감 후 예측을 전제로 현재일을 포함하고 미래일은 포함하지 않음을 설명한다.
- train/validation/test와 다음 walk-forward validation 모두 날짜순이어야 함을 명시한다.
- 향후 DART와 ECOS 데이터는 공시·발표일 기준 point-in-time merge가 필요함을 설명한다.

## 완료 기준

- 세 개의 학습 문서와 prompt, work log가 존재한다.
- 다섯 CLI의 진입점과 옵션이 실제 코드와 일치한다.
- 전체 테스트가 통과한다.
- 새 문서에 API 키 값과 투자 추천 표현이 없다.

## 실행 확인 명령어

```bash
python3 src/data_pipeline.py --help
python3 src/train.py --help
python3 src/evaluate.py --help
python3 src/backtest.py --help
python3 src/predict.py --help
python3 -m pytest -q
```

## 다음 작업

Phase 2-1. 여러 시간 구간에서 모델 안정성을 검증하는 walk-forward validation을 구현한다.
