# CURRENT_TASK.md

## 현재 작업

Phase 1-1. 삼성전자 단일 종목 기준으로 샘플 데이터 파이프라인을 끝까지 실행한다.

## 목표

API 키가 없어도 아래 명령어가 끝까지 실행되어야 한다.

```bash
python src/data_pipeline.py --ticker 005930 --start 2018-01-01 --end 2025-12-31 --use-sample
python src/train.py --ticker 005930
python src/evaluate.py --ticker 005930
python src/backtest.py --ticker 005930
python src/predict.py --ticker 005930
```

## 작업 범위

- `src/sample_data.py`
- `src/data_pipeline.py`
- `src/features.py`
- `src/labeling.py`
- `src/train.py`
- `src/evaluate.py`
- `src/backtest.py`
- `src/predict.py`

## 완료 기준

- `data/processed/005930_dataset.parquet` 생성
- `models/005930_model.joblib` 생성
- `reports/model_comparison.md` 갱신
- `reports/backtest_summary.md` 갱신
- `predict.py`가 최신일 기준 예측 확률 출력

## 주의사항

- 랜덤 split 금지
- label 관련 컬럼을 feature로 사용 금지
- 샘플 데이터는 실제 시장 데이터가 아님을 README와 report에 명시
- 투자 추천 문구 작성 금지

## 다음 작업 후보

1. 실제 공공데이터포털 API 연동
2. KOSPI 지수 데이터 수집
3. API 응답 스키마 정규화
4. Parquet 캐시 구조 개선
