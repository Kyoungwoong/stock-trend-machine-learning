# 프로젝트 계획표

## 프로젝트명

바이브 코딩으로 공공 금융 데이터를 활용한 주식 방향성 예측 ML 파이프라인 만들기

## 최종 목표

공공데이터포털과 KRX 등 공개 금융 API를 활용해 실제 주가 데이터를 수집하고, 주가·거래량·시장지표 기반 feature를 생성한 뒤, 향후 5영업일 주가 방향성을 예측하는 머신러닝 파이프라인을 구축한다. 단순 모델 정확도뿐 아니라 시간 순서 기반 검증과 간단한 백테스트를 통해 예측 모델의 한계를 함께 분석한다.

## 1차 목표

| 단계 | 목표 | 산출물 | 완료 기준 |
|---|---|---|---|
| 1 | 프로젝트 구조 설계 | README, RULE, AGENTS, ROADMAP | Codex가 작업 가능한 구조 완성 |
| 2 | 데이터 수집 뼈대 구현 | `fsc_stock_api.py`, `fsc_index_api.py` | 샘플 데이터 또는 API 데이터 저장 가능 |
| 3 | 주가/지수 데이터 정제 | `data_pipeline.py` | 종목 데이터와 지수 데이터 날짜 기준 병합 |
| 4 | label 생성 | `labeling.py` | 향후 5영업일 수익률과 label 생성 |
| 5 | feature 생성 | `features.py` | 수익률, 이동평균, 거래량, 변동성, 시장 수익률 생성 |
| 6 | 첫 모델 학습 | `train.py` | LogisticRegression, RandomForest 학습 |
| 7 | 시간 순서 기반 평가 | `evaluate.py` | accuracy, precision, recall, f1, roc-auc 산출 |
| 8 | 단순 백테스트 | `backtest.py` | 모델 매수 전략과 buy-and-hold 비교 |
| 9 | 예측 출력 | `predict.py` | 최신 데이터 기준 상승 확률 출력 |
| 10 | 블로그 정리 | reports 문서 | 한계와 개선 방향까지 정리 |

## 일정 예시

| 주차 | 작업 | 블로그 주제 |
|---|---|---|
| 1주차 | 문제 정의, 데이터 출처 확인, skeleton project 구성 | 프로젝트 시작하기 |
| 2주차 | 공공데이터포털 주식/지수 API 수집 구현 | 실제 주가 데이터 수집하기 |
| 3주차 | feature/label 생성, 데이터 누수 방지 규칙 정리 | 데이터 누수가 왜 위험한가 |
| 4주차 | LogisticRegression, RandomForest 학습 | 첫 예측 모델 만들기 |
| 5주차 | 시간 순서 평가, walk-forward validation 도입 | 랜덤 분할 대신 시간 순서 검증하기 |
| 6주차 | 단순 백테스트와 거래비용 반영 | 예측 정확도와 투자 수익률은 왜 다른가 |
| 7주차 | DART/ECOS/시장자금 지표 확장 설계 | 재무제표와 거시지표 추가하기 |
| 8주차 | 최종 보고서, README 보강, 포트폴리오 정리 | Codex와 함께 문서화하기 |

## 단계별 도입 기술

| 먼저 경험할 문제 | 해결을 위해 도입할 기술 |
|---|---|
| 날짜 순서가 중요하다 | TimeSeriesSplit, walk-forward validation |
| API를 매번 호출하면 느리고 제한이 있다 | Parquet 저장, SQLite 캐시 |
| API 키가 여러 개다 | `.env`, config 관리 |
| 모델 정확도만으로 투자 성과를 알 수 없다 | 단순 백테스트, 거래비용 반영 |
| 종목/지수 날짜가 안 맞는다 | trading calendar, inner join, 결측치 처리 |
| 재무제표 기준일을 잘못 쓰면 미래 정보가 섞인다 | 공시 제출일 기준 point-in-time merge |

## 이번 skeleton에서 의도적으로 제외한 것

- 실시간 자동매매
- 뉴스 감성분석
- 공시 전문 NLP 분석
- LSTM, Transformer
- 전체 상장종목 장기 백테스트
- 종목 추천 서비스
- 매수/매도 추천 문구

## 다음 작업

`CURRENT_TASK.md` 기준으로 1차 작업을 진행한다.
