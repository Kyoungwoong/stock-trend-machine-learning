# Task Prompt: 공공데이터포털 주식/지수 데이터 수집 구현

## 목표

공공데이터포털 금융위원회_주식시세정보와 금융위원회_지수시세정보 API를 사용해 삼성전자 `005930`과 KOSPI 지수의 일별 데이터를 수집한다.

## 수정 대상

- `src/data_sources/fsc_stock_api.py`
- `src/data_sources/fsc_index_api.py`
- `src/data_pipeline.py`
- `reports/data_summary.md`

## 요구사항

1. `.env`의 `DATA_GO_KR_SERVICE_KEY`를 사용한다.
2. API 키를 코드에 직접 쓰지 않는다.
3. 응답 컬럼을 프로젝트 표준 컬럼명으로 바꾼다.
4. 데이터는 `data/raw/`에 parquet로 저장한다.
5. 종목 데이터와 지수 데이터는 `date` 기준 inner join 한다.
6. API 호출 실패 날짜는 경고를 남기고 계속 진행한다.
7. 수집 결과 요약을 `reports/data_summary.md`에 작성한다.

## 완료 기준

```bash
python src/data_pipeline.py --ticker 005930 --start 2018-01-01 --end 2025-12-31
```

위 명령어 실행 후 `data/processed/005930_dataset.parquet`가 생성되어야 한다.
